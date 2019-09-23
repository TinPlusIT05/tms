# -*- encoding: utf-8 -*-

from openerp import models, fields


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    asset_ids = fields.One2many(
        'hr.employee.asset', 'employee_id', 'Assets'
    )
