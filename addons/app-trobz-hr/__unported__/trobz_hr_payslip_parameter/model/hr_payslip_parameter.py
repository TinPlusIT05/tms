# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv

class hr_payslip_parameter(osv.osv):
    
    _name = "hr.payslip.parameter"
    _description = "Payslip Parameters"
    _order = 'code'
    
    _columns = {
        'name': fields.char('Name', size=64, required=1),
        'code': fields.char('Code', size=16, required=1),
        'note': fields.text('Notes'),
    }
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The name of the payslip parameter must be unique!'),
        ('code_uniq', 'unique (code)', 'The code of the payslip parameter must be unique!'),
    ]
    
hr_payslip_parameter()
