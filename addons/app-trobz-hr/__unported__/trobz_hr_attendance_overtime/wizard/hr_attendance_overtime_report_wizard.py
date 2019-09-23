'''
Created on Oct 10, 2014

@author: tin
'''
from openerp.osv import osv, fields
from datetime import datetime
from openerp.tools.translate import _
class hr_attendance_overtime_report_wizard(osv.osv_memory):
    
    _name = "hr.attendance.overtime.report.wizard"

    _columns = {
        'date_from': fields.date('Date From', required= True),
        'date_to': fields.date('Date To', required= True),
        'department_id': fields.many2one('hr.department', 'Department'),
        'manager_id': fields.many2one('hr.employee', 'Manager', domain="[('manager', '=', True)]"),
        }
    
    def print_report(self, cr, uid, ids, context=None):
        if context is None: context = {}
        data = self.read(cr, uid, ids[0], [], context=context)
        department_id = data['department_id'] and data['department_id'][0] or False
        manager_id = data['manager_id'] and data['manager_id'][0] or False
        domain = []
        if department_id:
            domain.append(('department_id', '=', department_id))
        if manager_id:
            domain.append(('parent_id', '=', manager_id))
        datas = {
                 'department_id': department_id,
                 'manager_id': manager_id,
                 'date_from': data['date_from'],
                 'date_to': data['date_to'],
                 }
        res = {
                'type': 'ir.actions.report.xml', 
                'report_name': 'hr.attendance.overtime.xls.report', 
                'datas': datas,
                'name': 'Attendance Overtime Report'
            }
        return res
    
hr_attendance_overtime_report_wizard()