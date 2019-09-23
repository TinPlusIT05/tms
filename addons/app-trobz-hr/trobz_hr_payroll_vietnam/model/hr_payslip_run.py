# -*- coding: utf-8 -*-

from openerp.osv import osv, fields

class hr_payslip_run(osv.osv):
    
    _inherit = 'hr.payslip.run'
    _columns = {
        'thirdteenth_year': fields.integer('Year of 13th Month Salary'),
    }

hr_payslip_run()
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

