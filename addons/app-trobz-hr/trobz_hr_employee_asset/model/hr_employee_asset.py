# -*- encoding: utf-8 -*-
from openerp import models, fields, api, _


class hr_employee_asset(models.Model):
    _name = 'hr.employee.asset'

    lot_id = fields.Char(
        'Serial Number', required=True
    )
    employee_id = fields.Many2one(
        'hr.employee', 'Employee', ondelete='cascade', required=True
    )
    product_id = fields.Many2one('product.product', 'Product', default=False)
    delivery_date = fields.Date('Delivery Date')
    comment = fields.Text('Comment')

    _sql_constraints = [
        ('serial_employee_uniq', 'unique(lot_id,employee_id)',
         _('Employee and Serial Number of a asset record is unique!'))
    ]
