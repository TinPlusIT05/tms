
# -*- coding: utf-8 -*-

from openerp import api, fields, models
from openerp.exceptions import Warning
import logging


READONLY_STATES = {
    'approved': [('readonly', True)],
    'refused': [('readonly', True)],
}


class ModuleName(models.Model):
    _name = 'hr.input.overtime'
    _description = 'Hr Input Overtime'

    name = fields.Char(string='Name', compute='_generate_name')
    state = fields.Selection(
        string='Status',
        selection=[
            ('draft', 'New'),
            ('to_review', 'To Review'),
            ('approved', 'Approved'),
            ('refused', 'Refused'),
        ],
        default='draft',
    )
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee",
        states=READONLY_STATES
    )
    date_ot = fields.Date(string='Date have OT', states=READONLY_STATES)
    total_wh = fields.Float(string='Total WH', states=READONLY_STATES)
    from_time = fields.Float(string="From Time", states=READONLY_STATES)
    to_time = fields.Float(string="To Time", states=READONLY_STATES)
    overtime_type_id = fields.Many2one(
        comodel_name='hr.overtime.type',
        string='OverTime Type',
        states=READONLY_STATES
    )
    purpose = fields.Text(string='Purpose', states=READONLY_STATES)
    approved_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Approved By',
    )

    @api.multi
    def button_confirm(self):
        for rec in self:
            rec.state = 'to_review'
            rec.sendmail()

    @api.multi
    def button_approve(self):
        for rec in self:
            if rec.button_check_ot():
                rec.state = 'approved'
                rec.approved_by_id = self.env['res.users'].browse(self._uid).id

    @api.multi
    def button_refuse(self):
        for rec in self:
            rec.state = 'refused'

    @api.depends('date_ot', 'employee_id')
    def _generate_name(self):
        for rec in self:
            if rec.employee_id:
                rec.name = rec.employee_id.name + " OT date " + rec.date_ot
            else:
                rec.name = "New OT"

    @api.multi
    def button_check_ot(self):
        wk_object = self.env['tms.working.hour']
        for rec in self:
            wk_recs = wk_object.search([
                ('date', '=', rec.date_ot),
                ('employee_id', '=', rec.employee_id.id)
            ])
            duration_wk = sum([wk.duration_hour for wk in wk_recs]) - 8.0
            if duration_wk > 0 and duration_wk == rec.total_wh:
                return True
            else:
                raise Warning(
                    'Duration overtime does not match in working hours.')

    @api.multi
    def get_request_link(self):
        """
        Get url of given request
        """
        param_obj = self.env['ir.config_parameter']
        base_url = param_obj.get_param('web.base.url')
        # Example link: http://0.0.0.0:8069/web?db=database_name#id=4
        #    &view_type=form&model=hr.holidays&action=...
        act_window = self.env.ref('tms_modules.hr_overtime_act')
        link = base_url + '/web?db=%s#id=%s&view_type=form&model=hr.input.overtime&action=%s'\
            % (self._cr.dbname, self.id, act_window.id)
        return link

    @api.multi
    def get_email_content(self):
        """
        Get leave request information
        """
        info_string = '<div>Details:</div><ul>'
        for rec in self:
            info_string += "<li>Request's owner: %s </li>" \
                           % rec.employee_id.name or ''
            info_string += "<li>Date: %s day(s) </li>" \
                           % rec.date_ot or ''
            info_string += "<li>Total Duration: %s hour(s) </li>" \
                           % rec.total_wh or ''
            info_string += "<li>Description: %s </li>" % rec.purpose or ''
        info_string += '</ul>'

        return info_string

    @api.multi
    def sendmail(self):
        template = self.env.ref(
                    'tms_modules.email_template_input_ot_confirm'
                )
        for rec in self:
            if template:
                template.send_mail(rec.id)
        return True
