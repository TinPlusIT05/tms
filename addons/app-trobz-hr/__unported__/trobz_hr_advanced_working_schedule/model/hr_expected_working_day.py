# -*- coding: utf-8 -*-

from openerp.osv import osv, fields

class hr_expected_working_day(osv.osv):
    
    _name = 'hr.expected.working.day'
    _description = "Expected Working Days"
    _order = "name"
    _columns = {
        'name': fields.char('Name', readonly=1),
        'month_year': fields.char('Month/Year', 16, required=1, readonly=1), 
        'contract_id': fields.many2one('hr.contract', 'Contract', required=1, readonly=1),
        'employee_id': fields.many2one('hr.employee', 'Employee', required=1, readonly=1),
        'from_date': fields.date('From Date', readonly=1),
        'to_date': fields.date('To Date', readonly=1),
        'days': fields.float('Expected Working Days'),
    }
    
    _sql_constraints = [
        ('name_uniq', 'unique(month_year, contract_id)', 'The expected working days must be unique !'),
    ]

hr_expected_working_day()
