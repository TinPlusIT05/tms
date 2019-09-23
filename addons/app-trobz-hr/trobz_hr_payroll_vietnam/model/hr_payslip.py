# -*- coding: utf-8 -*-

from openerp.osv import osv, fields

class hr_payslip(osv.osv):
    
    _inherit = 'hr.payslip'
    _columns = {
        'thirdteenth_year': fields.integer('Year of 13th Month Salary'),
    }

hr_payslip()
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

