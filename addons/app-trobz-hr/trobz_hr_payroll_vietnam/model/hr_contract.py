# -*- coding: utf-8 -*-

from openerp.osv import osv, fields

class hr_contract(osv.osv):
    
    _inherit = 'hr.contract'
    _columns = {
        'wage': fields.float('Payroll Wage', help='Payroll Wage is used to compute salary per hour on normal working days and overtime.'),
        'basic_wage': fields.float('Contract Wage', help='Contract Wage is used to compute the insurance amount.'),
        'wage_type': fields.selection([('hour','Hour'),('day','Day'),('month','Month')], string='Wage Type', required=1),
        'is_union': fields.boolean('Union'),
    }
    _defaults = {
        'wage_type': 'hour',
    }
    
hr_contract()
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

