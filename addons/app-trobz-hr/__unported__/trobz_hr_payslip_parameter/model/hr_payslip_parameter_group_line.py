# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv

class hr_payslip_parameter_group_line(osv.osv):
    
    _name = "hr.payslip.parameter.group.line"
    _description = "Payslip Parameter Group Lines"
    
    _columns = {
        'payslip_parameter_id': fields.many2one('hr.payslip.parameter','Payslip Parameter', required=1),
        'payslip_parameter_group_id': fields.many2one('hr.payslip.parameter.group', 'Payslip Parameter Group'),
        'value': fields.float('Value'),
        'date_from': fields.date('Date From'),
        'date_to': fields.date('Date To'),
        'note': fields.text('Note'),
    }
    
hr_payslip_parameter_group_line()
