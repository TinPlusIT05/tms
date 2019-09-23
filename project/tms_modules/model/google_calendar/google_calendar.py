# -*- coding: utf-8 -*-
import operator
import simplejson
import urllib2
from openerp.addons.google_calendar.google_calendar\
    import SyncEvent, NothingToDo, Create, Update, Delete, Exclude
import openerp
from openerp import SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.osv import osv
from openerp.tools.translate import _
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)


class google_calendar(osv.AbstractModel):
    _inherit = "google.calendar"

    def update_events(self, cr, uid, lastSync=False, context=None):
        context = dict(context or {})

        calendar_event = self.pool['calendar.event']
        user_obj = self.pool['res.users']
        att_obj = self.pool['calendar.attendee']
        mypartner_id = user_obj.browse(
            cr, uid, uid, context=context).partner_id.id
        context_novirtual = self.get_context_no_virtual(context)

        if lastSync:
            try:
                all_event_from_google = self.get_event_synchro_dict(
                    cr, uid, lastSync=lastSync, context=context)
            except urllib2.HTTPError, e:
                if e.code == 410:  # GONE, Google is lost.
                    # we need to force the rollback from this cursor, because
                    # it locks my res_users but I need to write in this tuple
                    # before to raise.
                    cr.rollback()
                    registry = openerp.modules.registry.RegistryManager.get(
                        request.session.db)
                    with registry.cursor() as cur:
                        self.pool['res.users'].write(
                            cur, SUPERUSER_ID, [uid],
                            {'google_calendar_last_sync_date': False},
                            context=context)
                error_key = simplejson.loads(str(e))
                error_key = error_key.get('error', {}).get('message', 'nc')
                error_msg = "Google is lost... the next synchro" \
                            " will be a full synchro. \n\n %s" % error_key
                raise self.pool.get('res.config.settings').get_config_warning(
                    cr, _(error_msg), context=context)

            my_google_att_ids = att_obj.search(cr, uid, [
                ('partner_id', '=', mypartner_id),
                ('google_internal_event_id', 'in',
                    all_event_from_google.keys())
            ], context=context_novirtual)

            my_openerp_att_ids = att_obj.search(cr, uid, [
                ('partner_id', '=', mypartner_id),
                ('event_id.oe_update_date', '>', lastSync and
                 lastSync.strftime(DEFAULT_SERVER_DATETIME_FORMAT) or
                 self.get_minTime(cr, uid, context).strftime(
                     DEFAULT_SERVER_DATETIME_FORMAT)),
                ('google_internal_event_id', '!=', False),
            ], context=context_novirtual)

            my_openerp_googleinternal_ids = att_obj.read(
                cr, uid, my_openerp_att_ids,
                ['google_internal_event_id', 'event_id'],
                context=context_novirtual)

            if self.get_print_log(cr, uid, context=context):
                _logger.info("Calendar Synchro -  \n\nUPDATE IN GOOGLE\n%s\n\n"
                             "RETRIEVE FROM OE\n%s\n\nUPDATE IN OE\n%s\n\n"
                             "RETRIEVE FROM GG\n%s\n\n" %
                             (all_event_from_google, my_google_att_ids,
                              my_openerp_att_ids,
                              my_openerp_googleinternal_ids))

            for giid in my_openerp_googleinternal_ids:
                active = True  # if not sure, we request google
                if giid.get('event_id'):
                    active = calendar_event.browse(cr, uid, int(
                        giid.get('event_id')[0]),
                        context=context_novirtual).active

                if giid.get('google_internal_event_id') and\
                        not all_event_from_google.get(giid.get(
                            'google_internal_event_id')) and active:
                    one_event = self.get_one_event_synchro(
                        cr, uid, giid.get('google_internal_event_id'),
                        context=context)
                    if one_event:
                        all_event_from_google[one_event['id']] = one_event

            my_att_ids = list(set(my_google_att_ids + my_openerp_att_ids))

        else:
            domain = [
                ('partner_id', '=', mypartner_id),
                ('google_internal_event_id', '!=', False),
                '|',
                ('event_id.stop', '>', self.get_minTime(
                    cr, uid, context).strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)),
                ('event_id.final_date', '>', self.get_minTime(
                    cr, uid, context).strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)),
            ]

            # Select all events from OpenERP which have been already
            # synchronized in gmail
            my_att_ids = att_obj.search(
                cr, uid, domain, context=context_novirtual)
            all_event_from_google = self.get_event_synchro_dict(
                cr, uid, lastSync=False, context=context)

        event_to_synchronize = {}
        for att in att_obj.browse(cr, uid, my_att_ids, context=context):
            event = att.event_id

            base_event_id = att.google_internal_event_id.rsplit('_', 1)[0]

            if base_event_id not in event_to_synchronize:
                event_to_synchronize[base_event_id] = {}

            if att.google_internal_event_id not in \
                    event_to_synchronize[base_event_id]:
                event_to_synchronize[base_event_id][
                    att.google_internal_event_id] = SyncEvent()

            ev_to_sync = event_to_synchronize[
                base_event_id][att.google_internal_event_id]

            ev_to_sync.OE.attendee_id = att.id
            ev_to_sync.OE.event = event
            ev_to_sync.OE.found = True
            ev_to_sync.OE.event_id = event.id
            ev_to_sync.OE.isRecurrence = event.recurrency
            ev_to_sync.OE.isInstance = bool(
                event.recurrent_id and event.recurrent_id > 0)
            ev_to_sync.OE.update = event.oe_update_date
            ev_to_sync.OE.status = event.active
            ev_to_sync.OE.synchro = att.oe_synchro_date

        for event in all_event_from_google.values():
            event_id = event.get('id')
            base_event_id = event_id.rsplit('_', 1)[0]

            if base_event_id not in event_to_synchronize:
                event_to_synchronize[base_event_id] = {}

            if event_id not in event_to_synchronize[base_event_id]:
                event_to_synchronize[base_event_id][event_id] = SyncEvent()

            ev_to_sync = event_to_synchronize[base_event_id][event_id]

            ev_to_sync.GG.event = event
            ev_to_sync.GG.found = True
            ev_to_sync.GG.isRecurrence = bool(event.get('recurrency', ''))
            ev_to_sync.GG.isInstance = bool(event.get('recurringEventId', 0))
            # if deleted, no date without browse event
            ev_to_sync.GG.update = event.get('updated', None)
            if ev_to_sync.GG.update:
                ev_to_sync.GG.update = ev_to_sync.GG.update.replace(
                    'T', ' ').replace('Z', '')
            ev_to_sync.GG.status = (event.get('status') != 'cancelled')

        ######################
        #   PRE-PROCESSING   #
        ######################
        for base_event in event_to_synchronize:
            for current_event in event_to_synchronize[base_event]:
                event_to_synchronize[base_event][
                    current_event].compute_OP(modeFull=not lastSync)
            if self.get_print_log(cr, uid, context=context):
                if not isinstance(event_to_synchronize[base_event][
                        current_event].OP, NothingToDo):
                    _logger.info(event_to_synchronize[base_event])

        ######################
        #      DO ACTION     #
        ######################
        for base_event in event_to_synchronize:
            event_to_synchronize[base_event] = sorted(
                event_to_synchronize[base_event].iteritems(),
                key=operator.itemgetter(0))
            for current_event in event_to_synchronize[base_event]:
                cr.commit()
                event = current_event[1]  # event is an Sync Event !
                actToDo = event.OP
                actSrc = event.OP.src

                context['curr_attendee'] = event.OE.attendee_id

                if isinstance(actToDo, NothingToDo):
                    continue
                elif isinstance(actToDo, Create):
                    context_tmp = context.copy()
                    context_tmp['NewMeeting'] = True
                    if actSrc == 'GG':
                        res = self.update_from_google(
                            cr, uid, False, event.GG.event,
                            "create", context=context_tmp)
                        event.OE.event_id = res
                        meeting = calendar_event.browse(
                            cr, uid, res, context=context)
                        attendee_record_id = att_obj.search(cr, uid, [(
                            'partner_id', '=', mypartner_id),
                            ('event_id', '=', res)], context=context)
                        self.pool['calendar.attendee'].write(
                            cr, uid, attendee_record_id,
                            {'oe_synchro_date': meeting.oe_update_date,
                             'google_internal_event_id': event.GG.event['id']},
                            context=context_tmp)
                    elif actSrc == 'OE':
                        raise Exception(
                            "Should be never here, "
                            "creation for OE is done before update !")
                    # TODO Add to batch
                elif isinstance(actToDo, Update):
                    if actSrc == 'GG':
                        self.update_from_google(
                            cr, uid, event.OE.event, event.GG.event,
                            'write', context)
                    elif actSrc == 'OE':
                        self.update_to_google(
                            cr, uid, event.OE.event, event.GG.event, context)
                elif isinstance(actToDo, Exclude):
                    if actSrc == 'OE':
                        self.delete_an_event(cr, uid, current_event[
                                             0], context=context)
                    elif actSrc == 'GG':
                        new_google_event_id = event.GG.event['id'].rsplit(
                            '_', 1)[1]
                        if 'T' in new_google_event_id:
                            new_google_event_id = new_google_event_id.replace(
                                'T', '')[:-1]
                        else:
                            new_google_event_id = new_google_event_id + \
                                "000000"

                        if event.GG.status:
                            parent_event = {}
                            if not event_to_synchronize[base_event][
                                    0][1].OE.event_id:
                                main_ev = att_obj.search_read(
                                    cr, uid,
                                    [('google_internal_event_id', '=',
                                      event.GG.event['id'].rsplit('_', 1)[0])],
                                    fields=['event_id'],
                                    context=context_novirtual)
                                if main_ev and \
                                        main_ev[0].get('event_id', False):
                                    event_to_synchronize[base_event][0][
                                        1].OE.event_id = main_ev[0].get(
                                        'event_id')[0]
                                else:
                                    return True

                            parent_event['id'] = "%s-%s" % \
                                                 (event_to_synchronize[
                                                     base_event][0][
                                                     1].OE.event_id,
                                                  new_google_event_id)
                            self.update_from_google(
                                cr, uid, parent_event, event.GG.event,
                                "copy", context)
                        else:
                            parent_oe_id = event_to_synchronize[
                                base_event][0][1].OE.event_id
                            if parent_oe_id:
                                calendar_event.unlink(
                                    cr, uid, "%s-%s" %
                                             (parent_oe_id,
                                              new_google_event_id),
                                    can_be_deleted=True, context=context)

                elif isinstance(actToDo, Delete):
                    if actSrc == 'GG':
                        try:
                            self.delete_an_event(cr, uid, current_event[
                                                 0], context=context)
                        except Exception, e:
                            error = simplejson.loads(e.read())
                            error_nr = error.get('error', {}).get('code')
                            # if already deleted from gmail or never created
                            if error_nr in (404, 410,):
                                pass
                            else:
                                raise e
                    elif actSrc == 'OE':
                        calendar_event.unlink(
                            cr, uid, event.OE.event_id,
                            can_be_deleted=False, context=context)
        return True
