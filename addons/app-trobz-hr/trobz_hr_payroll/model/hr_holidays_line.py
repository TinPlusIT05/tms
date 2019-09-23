# -*- encoding: utf-8 -*-

from openerp.osv import fields, osv

class hr_holidays_line(osv.osv):    
    _inherit = 'hr.holidays.line'
    _columns = {
        'computed_on_payslip_days': fields.float("Computed on Payslip Days"),
    }
hr_holidays_line()