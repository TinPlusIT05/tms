# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.addons.calendar import calendar  # @UnresolvedImport
from datetime import datetime, timedelta
from lxml import etree
from openerp.osv.orm import setup_modifiers
from openerp.addons.crm import crm

import logging
_logger = logging.getLogger(__name__)

WEEK_LIST = [('1', 'Monday'),
             ('2', 'Tuesday'),
             ('3', 'Wednesday'),
             ('4', 'Thursday'),
             ('5', 'Friday'),
             ('6', 'Saturday'),
             ('7', 'Sunday')]


class trobz_crm_event(models.Model):

    """ CRM Event Cases """

    _name = 'trobz.crm.event'
    _description = "Meeting"
    _order = "date, priority desc"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _inherits = {'calendar.event': 'calendar_event_id'}

    @api.depends('name', 'partner_id', 'partner_id.name')
    def _get_full_name_subject(self):
        for record in self:
            if record.partner_id:
                record.full_name = '[%s] %s' % (
                    record.partner_id.name, record.name)
            else:
                record.full_name = record.name

    # F#12553 Priority be ordered from very high to low
    def _generate_order_by(self, order_spec, query):
        my_order = """
            CASE
                WHEN trobz_crm_event.priority='very_high' THEN 0
                WHEN trobz_crm_event.priority='high' THEN 1
                WHEN trobz_crm_event.priority='normal' THEN 2
                WHEN trobz_crm_event.priority='low' THEN 3
                ELSE 4
            END
        """
        if order_spec:
            return super(trobz_crm_event, self)._generate_order_by(
                order_spec, query)
        return " ORDER BY {0}".format(my_order)

    @api.model
    def _get_default_partner(self):
        partner_id = self._context.get('partner_id', False)
        return partner_id and partner_id or False

    @api.model
    def _get_default_contact(self):
        contact = self._context.get('main_contact', False)
        return contact and contact or False

    # Columns
    type_id = fields.Many2one('trobz.crm.event.type', 'Event Type',
                              required=True)
    calendar_event_id = fields.Many2one('calendar.event', 'Calendar Event',
                                        ondelete="cascade", auto_join=True,
                                        required=True)
    partner_id = fields.Many2one(
        'res.partner', 'Customer',
        default='_get_default_partner', domain="[('is_company','=',True)]")
    partner_address_id = fields.Many2one(
        'res.partner', 'Contact', default='_get_default_contact',
        domain="[('parent_id','=',partner_id),('is_company','=',False)]")
    priority = fields.Selection(crm.AVAILABLE_PRIORITIES[::-1],
                                'Priority', required=True, default='2')
    email_from = fields.Char('From', size=128,
                             help='Message sender, taken from user '
                                  'preferences. If empty, this is not '
                                  'a mail but a message.')
    email_to = fields.Char('To', size=256, help='Message recipients')
    email_cc = fields.Char('Cc', size=256,
                           help='Carbon copy message recipients')
    attachment_ids = fields.Many2many('ir.attachment',
                                      'crm_event_attachment_rel', 'event_id',
                                      'attachment_id', 'Attachments')
    display_email_fields = fields.Boolean(
        related='type_id.display_email_fields',
        string='Display Email Fields')
    display_meeting_fields = fields.Boolean(
        related='type_id.display_meeting_fields',
        string='Display Meeting Fields')
    state = fields.Selection([('open', 'Open'),
                              ('done', 'Done'), ('cancel', 'Canceled')],
                             'State', track_visibility='onchange', size=16,
                             readonly=True, default='open')
    lead_id = fields.Many2one('crm.lead', 'Opportunity',
                              domain="[('partner_id','=',partner_id)]")
    date = fields.Date("Date", compute="_get_date", store=True)
    display_ending_at = fields.Boolean(
        string="Display ending at",
        compute="_get_display_ending_at")
    full_name = fields.Char(string='Full name',
                            compute="_get_full_name_subject",
                            store=True)

    def onchange_allday(self, cr, uid, ids, start=False, end=False,
                        starttime=False, endtime=False, startdatetime=False,
                        enddatetime=False, checkallday=False, context=None):
        return self.pool['calendar.event'].onchange_allday(
            cr, uid, ids, start, end, starttime, endtime, startdatetime,
            enddatetime, checkallday, context)

    @api.one
    def case_close(self):
        return self.write({'state': 'done'})

    @api.one
    def case_cancel(self):
        name = self.name
        new_name = "[Canceled]" + name
        return self.write({'state': 'cancel', 'name': new_name})

    @api.one
    def unlink(self):
        calendar_event = self.calendar_event_id
        return calendar_event.unlink()

    def onchange_dates(self, cr, uid, ids, fromtype, start=False, end=False,
                       checkallday=False, allday=False, context=None):
        result = self.pool['calendar.event'].onchange_dates(
            cr, uid, ids, fromtype, start, end, checkallday, allday, context)
        # F#12555 Set end date from the start date adding 1 hour
        if not allday and start:
            try:
                _start = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
                result['value'].update({'start_datetime': str(
                    _start.replace(second=0, microsecond=0))})
                if not end or ('display_ending_at' in context and not
                               context['display_ending_at']):
                    _end = datetime.strptime(
                        start, "%Y-%m-%d %H:%M:%S") + timedelta(hours=1)
                    result['value'].update({'stop_datetime': str(
                        _end.replace(second=0, microsecond=0))})
                else:
                    _end = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
                    result['value'].update(
                        {'stop_datetime': str(_end.replace(
                            second=0, microsecond=0))})
            except:
                pass

        elif allday and start:
            if 'display_ending_at' in context and not\
                    context['display_ending_at']:
                if 'value' in result:
                    result['value'].update({'stop_date': start})
        return result

    def onchange_partner_ids(self, cr, uid, ids, value, context=None):
        return self.pool['calendar.event'].onchange_partner_ids(
            cr, uid, ids, value, context)

    @api.multi
    def case_open(self):
        res = self.write({'state': 'open'})
        for (event_id, name) in self.name_get():
            message = _("The Event '%s' has been opened.") % name
            event_id = calendar.calendar_id2real_id(event_id)
            self.log(event_id, message)
        return res

    @api.onchange('type_id')
    def onchange_type_id(self):
        if not self.type_id:
            return {}
        self.display_email_fields = self.type_id.display_email_fields,
        self.display_meeting_fields = self.type_id.display_meeting_fields

    @api.multi
    def action_get_feedback_event(self):
        """
        Button `Add Feedback Event`: Auto create a CRM event
        """
        config_env = self.env['ir.config_parameter']
        default_start_date = config_env.get_param('default_start_date')

        get_feedback = config_env.get_param(
            'default_crm_event_type_get_feedback')
        event_type = self.env['trobz.crm.event.type'].search(
            [('name', '=', get_feedback)])

        default_alarm = config_env.get_param('default_alarm')
        alarm = self.env['calendar.alarm'].search(
            [('name', '=', default_alarm)])

        for event in self:

            start = event.allday and str(datetime.strptime(
                event.start, "%Y-%m-%d %H:%M:%S").replace(
                hour=3, minute=0, second=0, microsecond=0)) \
                or event.start_datetime
            start = str(datetime.strptime(start, "%Y-%m-%d %H:%M:%S") +
                        timedelta(days=int(default_start_date)))
            end = str(datetime.strptime(start, "%Y-%m-%d %H:%M:%S") +
                      timedelta(hours=0.5))

            event_vals = {
                'name': 'Get feedback for ' + event.name,
                'type_id': event_type and event_type[0].id or False,
                'priority': '2',
                'user_id': event.user_id and event.user_id.id or False,
                'partner_id': event.partner_id and event.partner_id.id or False,
                'lead_id': event.lead_id and event.lead_id.id or False,
                'start_datetime': start,
                'stop_datetime': end,
                'start': event.start or False,
                'stop': event.stop or False,
                'alarm_ids': alarm and [[6, 0, alarm.ids]] or False,
                'partner_address_id': event.partner_address_id and
                            event.partner_address_id.id or False,
            }
            crm_event = self.create(event_vals)
            if not self._context.get('not_open_event_on_add_feedback', False):
                return {
                    'name': _('CRM Events'),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'trobz.crm.event',
                    'res_id': crm_event.id,
                    'domain': [('id', 'in', [crm_event.id])],
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                }
            else:
                return crm_event

    @api.model
    def create(self, vals):
        crm_event_tag = self.env['calendar.event.type'].search(
            [('name', '=', 'CRM-Event')])
        if crm_event_tag:
            categ_ids = vals.get('categ_ids', False)
            if categ_ids and categ_ids[0][2] and crm_event_tag:
                categ_ids[0][2].append(crm_event_tag.id)
                vals.update(categ_ids=categ_ids)
        return super(trobz_crm_event, self).create(vals)

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        res = super(
            trobz_crm_event, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type,
            context=context, toolbar=toolbar, submenu=submenu)
        if view_type in {'tree', 'form'}:
            doc = etree.XML(res['arch'])
            if context.get('hide_lead_id', False) and res['type'] == 'form':
                nodes = doc.xpath("//field[@name='lead_id']")
                for node in nodes:
                    node.set('invisible', '1')
                    setup_modifiers(node, None)
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    @api.depends('start_date', 'start_datetime', 'allday')
    def _get_date(self):
        """
        Calculate field date:
        - Check Allday, get start_date
        - NOT check, get start_datetime
        """
        for x in self:
            if x.allday:
                x.date = x.start_date
            else:
                local_dt = datetime.strptime(
                    x.start_datetime, '%Y-%m-%d %H:%M:%S')
                user_dt = fields.Datetime.context_timestamp(self, local_dt)
                x.date = user_dt.strftime('%Y-%m-%d')

    @api.multi
    @api.depends('type_id')
    def _get_display_ending_at(self):
        for crm_event in self:
            crm_event.display_ending_at = crm_event.type_id \
                and crm_event.type_id.display_ending_at_fields or False

    @api.cr_uid_ids_context
    def message_post(self, cr, uid, thread_id, body='', subject=None,
                     type='notification', subtype=None, parent_id=False,
                     attachments=None, context=None, content_subtype='html',
                     **kwargs):
        if context is None:
            context = {}
        crm_lead_obj = self.pool['trobz.crm.event']
        crm_lead = crm_lead_obj.browse(cr, uid, thread_id, context=context)
        if crm_lead:
            subject = crm_lead.full_name
        return super(trobz_crm_event, self).message_post(
            cr, uid, thread_id, body=body, subject=subject, type=type,
            subtype=subtype, parent_id=parent_id, attachments=attachments,
            context=context, content_subtype=content_subtype, **kwargs)

trobz_crm_event()
