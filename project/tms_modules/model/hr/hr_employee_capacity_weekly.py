# -*- encoding: UTF-8 -*-
from openerp import models, fields, api


class HrEmployeeCapacityWeekly(models.Model):

    _name = 'hr.employee.capacity.weekly'
    _description = 'HR Employee Capacity Weekly'
    _order = 'start_date DESC, employee_id DESC'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True)
    start_date = fields.Date(
        string='Sprint',
        default=lambda self: self.env['daily.mail.notification'].
        get_current_sprint().strftime('%Y-%m-%d'),
        required=True)
    production_rate = fields.Float(
        string='Production Rate (%)',
        digits=(2, 0),
        required=True)

    @api.model
    def _cron_update_weekly_employee_capacity(self):
        # If existing capacity weekly over or equal this week
        # delete it to create new one (with new production_rate computed)
        sprint_date = self.env['daily.mail.notification'].\
            get_current_sprint().strftime('%Y-%m-%d')
        over_date_weekly_capacities = self.search(
            [('start_date', '>=', sprint_date)],
            order='start_date DESC')
        if over_date_weekly_capacities:
            over_date_weekly_capacities.unlink()

        employee_ids = self.env['hr.employee'].search([])
        for emp in employee_ids:
            production_rate = emp.current_employee_capacity
            # Do not track those who have production rate 0%
            if production_rate > 0.0:
                self.create({
                    'employee_id': emp.id,
                    'production_rate': production_rate
                })
