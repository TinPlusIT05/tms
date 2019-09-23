# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv

class hr_payslip_parameter_group(osv.osv):
    _name = "hr.payslip.parameter.group"
    _description = "Payslip Parameter Groups"
    _columns = {
        'name': fields.char('Name', size=64, required=1),
        'grade_id': fields.many2one('hr.employee.grade', 'Employee Grade', required=1),
        'line_ids': fields.one2many('hr.payslip.parameter.group.line', 'payslip_parameter_group_id', 'Payslip Parameter Group Lines'),
    }
    _order = 'name'
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The name of paramter group the must be unique!'),
    ]
hr_payslip_parameter_group