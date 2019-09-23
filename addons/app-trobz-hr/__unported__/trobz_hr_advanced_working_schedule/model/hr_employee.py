# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import  DEFAULT_SERVER_DATETIME_FORMAT
import logging

class hr_employee(osv.osv):
    _inherit = "hr.employee"
    _columns = {
        'advance_working_schedule_id': fields.many2one('hr.advanced.working.schedule', 'Advanced Working Schedule', readonly=True),
    }
    
    def update_advance_working_schedule(self, cr, uid, context=None):
        """
        Ticket #5091
        Scheduler to update the advanced working schedule on employee form
        Get the advanced working schedule of the latest of employee from 22h to 22h next day (time 22h take from scheduler)
        """
        pwh_obj = self.pool.get('hr.payroll.working.hour')
        employee_obj = self.pool.get('hr.employee')
        from_date = (datetime.now() + relativedelta(hour=13, minute=0, second=0)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        to_date = (datetime.now() + relativedelta(hour=13, minute=0, second=0, days=1)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        
        #Get all employee
        employee_not_update_ids = []
            
        for emp_id in employee_obj.search(cr, uid, [], context=context):
            pwh_ids = pwh_obj.search(cr, uid, [('expected_start','>=',from_date),
                                               ('expected_start','<=',to_date)],
                                     order='expected_start', 
                                     context=context)
            if pwh_ids:
                latest_pwh = pwh_obj.read(cr, uid, pwh_ids[0], ['advanced_schedule_id'], context)
                schedule_id = latest_pwh.get('advanced_schedule_id', [False])[0]
                employee_obj.write(cr, uid, [emp_id], 
                                   {'advance_working_schedule_id': schedule_id}, 
                                   context=context)
                logging.info('      >> Update the latest Advance Schedule: %s of Employee-ID: %s'%(schedule_id, emp_id))
            else:
                employee_not_update_ids.append(emp_id)
        
        logging.info('      >>Employees-ID have not schedule (%s)'%employee_not_update_ids)
        if employee_not_update_ids:
            employee_obj.write(cr, uid, employee_not_update_ids, 
                               {"advance_working_schedule_id": False}, 
                               context=context)
        return True
hr_employee()