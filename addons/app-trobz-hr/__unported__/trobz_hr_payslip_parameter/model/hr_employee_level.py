# -*- encoding: utf-8 -*-
##############################################################################

from openerp.osv import osv, fields

class hr_employee_level(osv.osv):
    _name = "hr.employee.level"
    _description = "Employee Level"
    
    _columns = {
        'name': fields.char('Name', size=128, required=1),
    }
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The name of the employee type must be unique!'),
    ]
hr_employee_level()
