# -*- encoding: UTF-8 -*-
from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class mailman_list(models.Model):
    _inherit = ['mail.thread', 'mailman.list']
    _name = 'mailman.list'

    is_used_for_sup_notif = fields.Boolean('Used for Support Notifications')
    project_id = fields.Many2one('tms.project', string='Project')
    subscriber_ids = fields.Many2many(
        'res.partner', string='Subscribers',
        track_visibility='onchange')
    unsubscribe_me = fields.Boolean(
        string='Unsubscribe Me',
        compute='_compute_unsubscribe_me',
    )

    @api.multi
    def _compute_unsubscribe_me(self):
        curr_user = self.env['res.users'].browse(self._uid)
        partner_id = curr_user.partner_id
        for mailman in self:
            subscribers = mailman.subscriber_ids
            if subscribers:
                subscriber_ids = subscribers.ids
                if partner_id.id in subscriber_ids:
                    mailman.unsubscribe_me = True
                else:
                    mailman.unsubscribe_me = False

    def message_track(self, cr, uid, ids, tracked_fields,
                      initial_values, context=None):
        def convert_for_display(value, col_info):
            if not value and col_info['type'] == 'boolean':
                return 'False'
            if not value:
                return ''
            if col_info['type'] == 'many2one':
                return value.name_get()[0][1]
            if col_info['type'] == 'selection':
                return dict(col_info['selection'])[value]
            if col_info['type'] == 'many2many':
                str1 = ', '.join([v.name_get()[0][1] for v in value])
                return str1
            return value

        def format_message(message_description, tracked_values):
            message = ''
            if message_description:
                message = '<span>%s</span>' % message_description
            for name, change in tracked_values.items():
                old_values = change.get('old_value')
                list_old_values = [item.strip().encode('utf-8')
                                   for item in old_values.strip('[]').split(
                                   ',')]
                new_values = change.get('new_value')
                list_new_values = [item.strip().encode('utf-8')
                                   for item in new_values.strip('[]').split(
                                   ',')]

                vals = []
                for x in list_old_values:
                    if x not in list_new_values:
                        vals.append(x)
                if vals:
                    message +=\
                        '<div> &nbsp; &nbsp; &bull; <b>Removed %s</b>: ' %\
                        change.get('col_info')
                    message += '%s</div>' % ', '.join(vals)

                vals = []
                for x in list_new_values:
                    if x not in list_old_values:
                        vals.append(x)
                if vals:
                    message +=\
                        '<div> &nbsp; &nbsp; &bull; <b>Added %s</b>: ' %\
                        change.get('col_info')
                    message += '%s</div>' % ', '.join(vals)
            return message

        if not tracked_fields:
            return True

        for browse_record in self.browse(cr, uid, ids, context=context):
            initial = initial_values[browse_record.id]
            changes = set()
            tracked_values = {}

            # generate tracked_values data structure: {'col_name': {col_info,
            # new_value, old_value}}
            for col_name, col_info in tracked_fields.items():
                field = self._fields[col_name]
                initial_value = initial[col_name]
                record_value = getattr(browse_record, col_name)

                if record_value == initial_value and\
                        getattr(field, 'track_visibility', None) == 'always':
                    tracked_values[col_name] = dict(
                        col_info=col_info['string'],
                        new_value=convert_for_display(record_value, col_info),
                    )
                # because browse null != False
                elif record_value != initial_value and\
                        (record_value or initial_value):
                    if getattr(field, 'track_visibility', None) in\
                            ['always', 'onchange']:
                        tracked_values[col_name] = dict(
                            col_info=col_info['string'],
                            old_value=convert_for_display(
                                initial_value, col_info),
                            new_value=convert_for_display(
                                record_value, col_info),
                        )
                    if col_name in tracked_fields:
                        changes.add(col_name)
            if not changes:
                continue

            # find subtypes and post messages or log if no subtype found
            subtypes = []
            # By passing this key, that allows to let the subtype empty and so
            # don't sent email because partners_to_notify from
            # mail_message._notify will be empty
            if not context.get('mail_track_log_only'):
                for field, track_info in self._track.items():
                    if field not in changes:
                        continue
                    for subtype, method in track_info.items():
                        if method(self, cr, uid, browse_record, context):
                            subtypes.append(subtype)

            posted = False
            for subtype in subtypes:
                subtype_rec = self.pool.get('ir.model.data').xmlid_to_object(
                    cr, uid, subtype, context=context)
                if not (subtype_rec and subtype_rec.exists()):
                    _logger.debug('subtype %s not found' % subtype)
                    continue
                message = format_message(
                    subtype_rec.description if subtype_rec.description else
                    subtype_rec.name, tracked_values)
                self.message_post(
                    cr, uid, browse_record.id, body=message,
                    subtype=subtype, context=context)
                posted = True
            if not posted:
                message = format_message('', tracked_values)
                self.message_post(
                    cr, uid, browse_record.id,
                    body=message, context=context)
        return True

    @api.multi
    def button_unsubscribe_me(self):
        curr_user = self.env['res.users'].browse(self._uid)
        partner_id = curr_user.partner_id
        for mailman in self:
            subscribers = mailman.subscriber_ids
            if subscribers:
                subscriber_ids = subscribers.ids
                if partner_id.id in subscriber_ids:
                    subscriber_ids.remove(partner_id.id)
                mailman.write({'subscriber_ids': [(6, 0, subscriber_ids)]})
        return True

    @api.multi
    def button_subscribe_me(self):
        curr_user = self.env['res.users'].browse(self._uid)
        partner_id = curr_user.partner_id
        for mailman in self:
            subscribers = mailman.subscriber_ids
            if subscribers:
                subscriber_ids = subscribers.ids
                if partner_id.id not in subscriber_ids:
                    subscriber_ids.append(partner_id.id)
                mailman.write({'subscriber_ids': [(6, 0, subscriber_ids)]})
        return True

    @api.multi
    def button_force_sync(self):
        mailman = self._get_mailman()
        for list_obj in self:
            old_subscribers = {s.id: s.email
                               for s in list_obj.subscriber_ids}
            list_obj._save_in_mailman(mailman, old_subscribers)
        return True
