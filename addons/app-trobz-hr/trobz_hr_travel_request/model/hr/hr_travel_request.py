# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta
from openerp.addons.decimal_precision\
    import decimal_precision as dp  # @UnresolvedImport
from openerp.exceptions import Warning
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _


class hr_travel_request(models.Model):
    _name = 'hr.travel.request'
    _inherit = ['mail.thread']
    _description = 'Travel Request'
    _order = 'start_date desc, employee_id'

    @api.model
    def _get_employee_from_uid(self):
        """
        Default value of employee_id is the employee of current user.
        """
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self._uid)], limit=1, order='id'
        )
        return employee.id

    # Columns
    name = fields.Char(string='Summary', required=True, readonly=True,
                       size=128, states={'draft': [('readonly', False)]})
    hr_travel_type_id = fields.Many2one(
        comodel_name='hr.travel.type', string='Travel Type',
        required=True, readonly=True, ondelete='restrict',
        states={'draft': [('readonly', False)]}
    )
    start_date = fields.Date(string='Start Date', required=True, readonly=True,
                             states={'draft': [('readonly', False)]})
    end_date = fields.Date(string='End Date', required=True, readonly=True,
                           states={'draft': [('readonly', False)]})
    duration = fields.Float('Number Of Days', readonly=True)
    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Employee',
        required=True, readonly=True, ondelete='restrict',
        states={'draft': [('readonly', False)]},
        default=_get_employee_from_uid
    )
    employee_department_id = fields.Many2one(
        comodel_name='hr.department', string='Department',
        readonly=True, states={'draft': [('readonly', False)]}
    )
    employee_designation_id = fields.Many2one(
        comodel_name='hr.job', string='Designation',
        required=True, readonly=True,
        states={'draft': [('readonly', False)]}
    )
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('confirm', 'Confirmed'),
                   ('refuse', 'Refused'), ('approved', 'Approved')],
        string='Status', default='draft'
    )
    visa_expiry_date = fields.Date(string='Visa Expiry Date', readonly=True,
                                   states={'draft': [('readonly', False)]})
    mutiple_visit_visa = fields.Boolean(
        string='Multiple Visit Visa', readonly=True,
        states={'draft': [('readonly', False)]}, default=False
    )
    destination_id = fields.Many2one(
        comodel_name='res.country', string='Destination',
        readonly=True, states={'draft': [('readonly', False)]}
    )
    round_trip = fields.Boolean(
        string='Round Trip', readonly=True, default=False,
        states={'draft': [('readonly', False)]}
    )
    one_way_trip = fields.Boolean(
        string='One Way Trip', readonly=True, default=False,
        states={'draft': [('readonly', False)]}
    )
    ticket_price = fields.Float(
        string='Ticket Price', readonly=True,
        digits_compute=dp.get_precision('Payroll'),
        states={'draft': [('readonly', False)]}
    )
    visa_cost = fields.Float(
        string='Visa Cost', readonly=True,
        digits_compute=dp.get_precision('Payroll'),
        states={'draft': [('readonly', False)]}
    )
    general_description = fields.Text(string='Description', readonly=True,
                                      states={'draft': [('readonly', False)]})
    attachments_count = fields.Integer(string="Documents Count")

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """
        Travel request start date must be less than end date.
        """
        msg = _('Travel request start date must be less than end date.')
        for travel_request in self:
            if travel_request.start_date\
                    and travel_request.end_date\
                    and travel_request.start_date > travel_request.end_date:
                raise Warning(msg)
        return True

    @api.multi
    def button_reset_to_draft(self):
        """
        Reset refused travel requests to draft.
        """
        self.state = 'draft'
        return True

    @api.multi
    def button_confirm(self):
        """
        This function opens a window to compose an email,
        with the travel request template message loaded by default.
        """
        self.state = 'confirm'
        mdata_obj = self.env['ir.model.data']
        try:
            template_id = self.env.ref(
                'trobz_hr_travel_request.email_template_confirm_travel_request'
            )
        except ValueError:
            template_id = False
        try:
            compose_form_id = self.env.ref(
                'trobz_hr_travel_request.'
                'travel_request_email_compose_message_wizard_form'
            )
        except ValueError:
            compose_form_id = False
        ctx = dict(self._context)
        ctx.update({
            'default_model': 'hr.travel.request',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id and template_id.id or False),
            'default_template_id': template_id and template_id.id or False,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id and compose_form_id.id or False, 'form')],
            'view_id': compose_form_id and compose_form_id.id or False,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def button_approve(self):
        """
        This function opens a window to compose an email,
        with the travel request template message loaded by default
        """
        self.state = 'approved'
        try:
            template_id = self.env.ref(
                'trobz_hr_travel_request.email_template_approved_travel_request'
            )
        except ValueError:
            template_id = False
        try:
            compose_form_id = self.env.ref(
                'trobz_hr_travel_request.'
                'travel_request_email_compose_message_wizard_form'
            )
        except ValueError:
            compose_form_id = False
        ctx = dict(self._context)
        ctx.update({
            'default_model': 'hr.travel.request',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id and template_id.id or False),
            'default_template_id': template_id and template_id.id or False,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id and compose_form_id.id or False, 'form')],
            'view_id': compose_form_id and compose_form_id.id or False,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def button_refuse(self):
        """
        This function opens a window to compose an email,
        with the travel request template message loaded by default.
        """
        self.state = 'refuse'
        try:
            template_id = self.env.ref(
                'trobz_hr_travel_request.email_template_refused_travel_request'
            )
        except ValueError:
            template_id = False
        try:
            compose_form_id = self.env.ref(
                'trobz_hr_travel_request.'
                'travel_request_email_compose_message_wizard_form'
            )
        except ValueError:
            compose_form_id = False
        ctx = dict(self._context)
        ctx.update({
            'default_model': 'hr.travel.request',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id and template_id.id or False),
            'default_template_id': template_id and template_id.id or False,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id and compose_form_id.id or False, 'form')],
            'view_id': compose_form_id and compose_form_id.id or False,
            'target': 'new',
            'context': ctx,
        }

    @api.onchange('employee_id')
    def on_change_employee(self):
        """
        @param employee_id: selected employee
        @return:
            employee_department_id
            employee_designation_id
        """
        if not self.employee_id:
            self.employee_department_id = False
            self.employee_designation_id = False
            return
        job_id = self.employee_id.job_id\
            and self.employee_id.job_id.id or False
        department_id = self.employee_id.department_id\
            and self.employee_id.department_id.id or False
        self.employee_department_id = department_id
        self.employee_designation_id = job_id

    @api.onchange('round_trip')
    def on_change_round_trip(self):
        """
        Be able to choose one_way_trip or round_trip,
        not both of them at a time.
        """
        self.one_way_trip = not self.round_trip and True or False

    @api.onchange('one_way_trip')
    def on_change_one_way_trip(self):
        """
        Be able to choose one_way_trip or round_trip,
        not both of them at a time.
        """
        self.round_trip = not self.one_way_trip and True or False

    @api.model
    def calculate_duration(self, employee_id, start_date, end_date):
        """
        Having start_date and end_date, calculating the days between them
        based on the contract of the employee.
        """
        if not start_date\
                or not end_date:
            return 0
        contract_obj = self.env['hr.contract']
        contracts = contract_obj.search(
            [('employee_id', '=', employee_id)],
            order='date_start', limit=1
        )
        if not contracts:
            return 0
        resource_calendar = contracts and contracts.working_hours\
            and contracts.working_hours[0] or False
        if not resource_calendar:
            return 0

        duration = 0
        dt_start_date = datetime.strptime(start_date, DF)
        dt_end_date = datetime.strptime(end_date, DF)
        delta = dt_end_date - dt_start_date
        work_days = []
        rca_obj = self.env['resource.calendar.attendance']
        resource_calendar_attendances = rca_obj.search(
            [('calendar_id', '=', resource_calendar.id)]
        )
        for rca in resource_calendar_attendances:
            dayofweek = rca and rca.dayofweek and rca.dayofweek[0] or False
            work_days.append(str(dayofweek))
        for day in range(delta.days + 1):
            next_date = dt_start_date + timedelta(days=day)
            # if not working schedule and not in Saturday and Sunday
            if not resource_calendar\
                    and next_date.weekday() not in (5, 6):
                duration += 1
            elif str(next_date.weekday()) in work_days:
                duration += 1
        return duration

    @api.onchange('start_date', 'end_date', 'employee_id')
    def on_change_date_value(self):
        """
        @param start_date: selected
        @param end_date: selected
        @return: duration: number of days from start_date to end_date
        """
        self.duration = self.calculate_duration(
            self.employee_id.id, self.start_date, self.end_date
        )
        return

    @api.multi
    def act_view_attachments(self):
        """
        View the list of documents associated with the travel request
        """
        attachment_obj = self.env['ir.attachment']
        attachments = attachment_obj.search(
            [('res_model', '=', 'hr.travel.request'),
             ('res_id', 'in', self.ids)]
        )
        if attachments:
            return {
                'domain': [('id', 'in', attachments.ids)],
                'name': _('Documents'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'ir.attachment',
                'type': 'ir.actions.act_window',
                'context': self._context,
            }
        raise Warning(_("This request does not contain any documents!"))

    @api.model
    def create(self, vals):
        """
        From three info: employee, start date and end date,
        compute the duration of each leave request.
        """
        if 'employee_id' in vals\
                and 'start_date' in vals\
                and 'end_date' in vals:
            vals.update({'duration': self.calculate_duration(
                vals['employee_id'], vals['start_date'],
                vals['end_date']
            )})
        return super(hr_travel_request, self).create(vals)

    @api.multi
    def write(self, vals):
        """
        From three info: employee, start date and end date,
        compute the duration of each leave request.
        """
        res = super(hr_travel_request, self).write(vals)
        if 'employee_id' in vals\
                or 'start_date' in vals\
                or 'end_date' in vals:
            for request in self:
                request.duration = self.calculate_duration(
                    request.employee_id.id, request.start_date,
                    request.end_date
                )
        return res

hr_travel_request()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
