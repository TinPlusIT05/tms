# -*- coding: utf-8 -*-
from openerp.osv import osv,fields

class import_attendance_error(osv.osv_memory):
    
    _name = 'import.attendance.error'
    
    _columns = {
        'employee_id': fields.char('Employee', size=64),
        'date': fields.char('Date', size=64),
        'action': fields.char('Action', size=64),
        'action_reason_id': fields.char('Action Reason', size=64),
        'error': fields.char('Error', size=100),
    }

import_attendance_error()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

