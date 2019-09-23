# -*- encoding: utf-8 -*-
import logging

from openerp import api, models, fields, _
from openerp.exceptions import Warning

_logger = logging.getLogger(__name__)


class TmsSupportTraining(models.Model):
    _name = 'tms.support.training'
    _inherit = ['mail.thread']
    _description = 'TMS Support Training'

    name = fields.Char(string='Summary', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', track_visibility='onchange',
       states={'approved': [('readonly', True)],
               'cancelled': [('readonly', True)]})
    customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        track_visibility='onchange',
        required=True,
        states={'approved': [('readonly', True)],
                'cancelled': [('readonly', True)]})
    employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        relation='hr_employee_support_training_rel',
        column1='support_training_id',
        column2='employee_id',
        string='Employees',
        track_visibility='onchange',
        required=True,
        states={'approved': [('readonly', True)],
                'cancelled': [('readonly', True)]})
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        default=lambda self: self.env.user.employee_id,
        readonly=True,
        states={'approved': [('readonly', True)],
                'cancelled': [('readonly', True)]})
    location_id = fields.Many2one(
        comodel_name='tms.location.type',
        string='Location Type',
        track_visibility='onchange',
        required=True,
        states={'approved': [('readonly', True)],
                'cancelled': [('readonly', True)]})
    location_address = fields.Char(
        string='Location Address',
        states={'approved': [('readonly', True)],
                'cancelled': [('readonly', True)]})
    moving_method = fields.Selection([
        ('self_moving', 'Self Moving'),
        ('paid_by_trobz', 'Paid By Trobz'),
        ('paid_by_customer', 'Paid By Customer'),
        ('other', 'Other'),
    ], string='Moving Method',
       states={'approved': [('readonly', True)],
               'cancelled': [('readonly', True)]})
    date_from = fields.Date(
        string='Date From', required=True,
        states={'approved': [('readonly', True)],
                'cancelled': [('readonly', True)]})
    date_to = fields.Date(
        string='Date To', required=True,
        states={'approved': [('readonly', True)],
                'cancelled': [('readonly', True)]})
    duration = fields.Float(
        digits=(16, 2),
        compute='_get_duration',
        store=True,
        string='Duration (days)',
        track_visibility='onchange',
        states={'approved': [('readonly', True)],
                'cancelled': [('readonly', True)]})
    detail = fields.Text(string='Detail')
    leave_request_ids = fields.One2many(
        'hr.holidays',
        'support_training_id',
        'Leave Requests'
    )

    @api.constrains('customer_id', 'employee_ids', 'date_from', 'date_to')
    def _check_overlap(self):
        for travel in self:
            if travel.date_to < travel.date_from:
                raise Warning(
                    _('Date From must be greater than or equal Date To'))
            domain = [
                ('id', '!=', travel.id),
                ('date_to', '>=', travel.date_from),
                ('date_from', '<=', travel.date_to),
            ]
            search_travels = self.search(domain)
            for search_travel in search_travels:
                if len(search_travel.employee_ids & travel.employee_ids):
                    raise Warning(
                        _('You can not have the same business travel request \
                            with the overlapped period'))
        return True

    @api.depends('date_from', 'date_to')
    def _get_duration(self):
        for travel in self:
            if not travel.date_from or not travel.date_to:
                travel.duration = 0.0
            else:
                employee = travel.employee_id
                if not employee:
                    employee = self.env.user.employee_id
                days = self.env['hr.holidays.line'].\
                    _calculate_days(employee, travel.date_from, travel.date_to,
                                    'full', 'full')
                travel.duration = days

    @api.multi
    def action_draft(self):
        for travel in self:
            travel.write({'state': 'draft'})
        return True

    @api.multi
    def action_confirm(self):
        for travel in self:
            travel.write({'state': 'confirm'})
            travel.send_travel_email(
                'tms_modules.email_template_business_travel_to_approve')
        return True

    @api.multi
    def action_approve(self):
        for travel in self:
            travel.write({'state': 'approved'})
            travel.send_travel_email(
                'tms_modules.email_template_business_travel_approval')
        self.create_leave_request()
        return True

    @api.multi
    def action_cancel(self):
        for travel in self:
            travel.write({'state': 'cancelled'})
            travel.send_travel_email(
                'tms_modules.email_template_business_travel_cancelled')
        self.remove_leave_request()
        return True

    @api.multi
    def create_leave_request(self):
        LeaveRequest = self.env['hr.holidays']
        for travel in self:
            leave_type = travel.location_id.holiday_status_id
            duration = travel.duration
            vals = {
                'name': travel.name,
                'holiday_type': 'employee',
                'number_of_days_temp': duration,
                'support_training_id': travel.id
            }
            for employee in travel.employee_ids:
                vals.update({
                    'employee_id': employee.id,
                    'holiday_line': [(0, 0, {
                        'holiday_status_id': leave_type.id,
                        'first_date': travel.date_from,
                        'last_date': travel.date_to,
                        'first_date_type': 'full',
                        'last_date_type': 'full',
                        'number_of_days': duration,
                        'employee_id': employee.id,
                    })]
                })
                LeaveRequest |= LeaveRequest.create(vals)
            LeaveRequest.holidays_confirm()
            LeaveRequest.holidays_validate()
        return True

    @api.multi
    def remove_leave_request(self):
        leaves = self.mapped('leave_request_ids')
        leaves.change_state_to_cancel()
        leaves.unlink()

    @api.model
    def send_travel_email(self, mail_template):
        template = self.env.ref(mail_template)
        _logger.info("===== START Send %s =====" % template.name)
        template.send_mail(self.id)
        _logger.info("===== END Send %s =====" % template.name)

    @api.model
    def get_request_link(self):
        """
        Get business travel view from url
        """
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        act_window = self.env.ref('tms_modules.action_tms_support_training')
        link = '%s/web?db=%s#id=%s&view_type=form&model=%s&action=%s' % \
            (base_url, self._cr.dbname, self.id, self._model, act_window.id)
        return link

    @api.model
    def get_email_content(self):
        """
        Get business travel email content
        """
        employee_content = "<ul>"
        for employee in self.employee_ids:
            employee_content += "<li>%s</li>" % employee.name
        employee_content += "</ul>"

        content = """
        <div>Details:<div>
        <ul>
            <li>Request's owner: %s</li>
            <li>Summary: %s</li>
            <li>Customer: %s</li>
            <li>Employees: %s</li>
            <li>Date From: %s</li>
            <li>Date To: %s</li>
            <li>Duration (days): %s</li>
            <li>Location type: %s</li>
        </ul>
""" % (self.employee_id.name, self.name, self.customer_id.name,
            employee_content, self.date_from, self.date_to, self.duration,
            self.location_id.name)

        return content
