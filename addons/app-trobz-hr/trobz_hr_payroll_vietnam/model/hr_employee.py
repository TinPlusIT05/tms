# -*- coding: utf-8 -*-

from openerp.osv import osv, fields

class hr_employee(osv.osv):
    
    _inherit = 'hr.employee'
    _columns = {
        'number_of_dependent': fields.integer('Number of Dependent'),
    }
    
hr_employee() 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

