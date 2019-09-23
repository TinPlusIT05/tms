# -*- coding: utf-8 -*-
from openerp import models, api, fields


class hr_wage_history(models.Model):
    _name = "hr.wage.history"

    name = fields.Many2one('hr.employee', 'Employee')
    contract_id = fields.Many2one('hr.contract', 'Contract')
    department_id = fields.Many2one('hr.department', 'Department')
    job_id = fields.Many2one('hr.job', 'Job')
    current_wage = fields.Float('Current Wage')
    new_wage = fields.Float('New Wage')
    difference = fields.Float('Difference')
    percentage = fields.Float('Percentage (%)')
    date_of_change = fields.Date('Effective Date')
    responsible_user_id = fields.Many2one('res.users', 'Responsible')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
