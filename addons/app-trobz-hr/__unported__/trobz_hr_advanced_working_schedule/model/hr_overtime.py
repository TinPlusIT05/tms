# -*- encoding: utf-8 -*-
##############################################################################

from openerp.osv import osv, fields
from datetime import datetime
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _

class hr_overtime(osv.osv): 
    _inherit = 'hr.overtime'    
    _states = {'done': [('readonly', True)]}
    
    _columns = {
        'advanced_schedule_id': fields.many2one('hr.advanced.working.schedule', 'Advanced Working Schedule', 
                                               required=False, readonly=False, states=_states),
    }
        
    def overtime_confirm(self, cr, uid, ids, context=None):
        """
        Override function: 
        Add field advanced_schedule_id
        """
        res = self.write(cr, uid, ids, {'state': 'confirmed'}, context=context)
        wf_service = netsvc.LocalService("workflow")
        for overtime in self.read(cr, uid, ids, context=context):
            if overtime['mode'] == 'by_employees':
                # common values
                vals = {
                    'name': overtime['name'],
                    'month_year': overtime['month_year'],
                    'mode': 'by_employee',
                    'advanced_schedule_id': overtime['advanced_schedule_id'] and overtime['advanced_schedule_id'][0] or False,
                    'datetime_start': overtime['datetime_start'],
                    'datetime_stop': overtime['datetime_stop'],
                    'break_start': overtime['break_start'],
                    'break_stop': overtime['break_stop'],
                    'break_hour': overtime['break_hour'],
                    'working_hour': overtime['working_hour'],
                    'working_activity_id': overtime['working_activity_id'] and overtime['working_activity_id'][0] or False,
                    'type': overtime['type'],
                    'compensation_date': overtime['compensation_date'],
                    'reason': overtime['reason']
                }
                # Generate overtime for every employee
                for employee_id in overtime['employee_ids']:
                    contract_ids = self.pool.get('hr.contract').get_contract(cr, uid, employee_id, overtime['name'], context=context)
                    if contract_ids:
                        vals.update({'employee_id': employee_id,
                                     'contract_id': contract_ids[0]})
                        overtime_id = self.create(cr, uid, vals, context=context)
                        wf_service.trg_validate(uid, 'hr.overtime', overtime_id, 'button_confirm', cr)
                res = self.write(cr, uid, ids, {'state': 'done'}, context=context)
        return res
    
    def onchange_advanced_schedule_id(self, cr, uid, ids, name, advanced_schedule_id, context=None):
        """
        @param advanced_schedule_id: Select Advanced working schedule
        @name: Current Overtime date
        @return: Datetime Start/Stop, Break Start/Stop, Break Hours, Overtime Hours
        """
        
        res = {'value':{'datetime_start': '',
                        'datetime_stop': '',
                        'working_hour': 0.0,
                        'break_start': False,
                        'break_stop': False,
                        'break_hour': 0.0,
                        }
               }
        
        if not name or not advanced_schedule_id:
            return res
        
        time_obj = self.pool.get('hr.advanced.working.time')
        schedule_obj = self.pool.get('hr.advanced.working.schedule')

        schedule = schedule_obj.read(cr, uid, advanced_schedule_id, 
                                     ['work_from', 'work_to', 'break_from', 'break_to'], 
                                     context=context)
        
        datetime_work_from = time_obj.compute_datetime(cr, uid, name, schedule['work_from'][0], context=context)
        datetime_work_to = time_obj.compute_datetime(cr, uid, name, schedule['work_to'][0], context=context)
        str_datetime_work_from = datetime_work_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        str_datetime_work_to = datetime_work_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        break_hour = 0.0
        str_datetime_break_from = ''
        str_datetime_break_to = ''
        if schedule['break_from'] and schedule['break_to']:
            datetime_break_from = schedule['break_from'] and time_obj.compute_datetime(cr, uid, name, schedule['break_from'][0], context=context)
            datetime_break_to = schedule['break_to'] and time_obj.compute_datetime(cr, uid, name, schedule['break_to'][0], context=context)
            str_datetime_break_from = datetime_break_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            str_datetime_break_to = datetime_break_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            break_hour = time_obj.diff_hour(datetime_break_from, datetime_break_to)
        working_hour = time_obj.diff_hour(datetime_work_from, datetime_work_to) - break_hour
        if str_datetime_break_from == '' or str_datetime_break_to == '':
            res['value'] = {'datetime_start': str_datetime_work_from,
                            'datetime_stop': str_datetime_work_to,
                            'break_start': False,
                            'break_stop': False,
                            'break_hour': break_hour,
                            'working_hour': working_hour,
                            }
        else:
            res['value'] = {'datetime_start': str_datetime_work_from,
                            'datetime_stop': str_datetime_work_to,
                            'break_start': str_datetime_break_from,
                            'break_stop': str_datetime_break_to,
                            'break_hour': break_hour,
                            'working_hour': working_hour,
                            }
        return res
    
    def onchange_start_stop(self, cr, uid, ids, name, advanced_schedule_id, str_datetime_start, str_datetime_stop, context=None):
        """
        Override fnct: Map datetime_start, datetime_stop with advanced working schedule
        
        @param str_datetime_start: Select Datetime start (string)
        @param str_datetime_stop: Select Datetime stop (string)
        @param advanced_schedule_id: Current advanced working schedule
        @param name: current overtime date
        @return: working hour, break hour
        """
        
        res = {'value': {'working_hour': 0, 'break_hour': 0}}
        
        if not str_datetime_start or not str_datetime_stop or not name:
            return res
        
        # Convert from string to datetime
        datetime_start = datetime.strptime(str_datetime_start, DEFAULT_SERVER_DATETIME_FORMAT)
        datetime_stop = datetime.strptime(str_datetime_stop, DEFAULT_SERVER_DATETIME_FORMAT)
        
        time_obj = self.pool.get('hr.advanced.working.time')
        if not advanced_schedule_id:
            #The current advanced working schedule id null
            res['value']['working_hour'] = time_obj.diff_hour(datetime_start, datetime_stop)
            return res
        ot_date = datetime.strptime(name, DEFAULT_SERVER_DATE_FORMAT)
        if advanced_schedule_id:
            schedule_obj = self.pool.get('hr.advanced.working.schedule')
            working_schedule = schedule_obj.read(cr, uid, advanced_schedule_id, ['work_from', 'work_to'],
                                                 context=context)
            working_time_obj = self.pool.get('hr.advanced.working.time')
            res['value'].update({
                # Compute the month and year
                'month_year': ot_date.strftime('%m/%Y'),
                # Re-compute the start and stop
                'datetime_start': working_time_obj.compute_datetime(cr, uid, name, working_schedule['work_from'][0],
                                                                    get_str=True, context=context),
                'datetime_stop': working_time_obj.compute_datetime(cr, uid, name, working_schedule['work_to'][0],
                                                                   get_str=True, context=context)
            })
        
        #The current advanced working schedule is not null
        # Suppose an advanced working schedule
        # - Starts from 07:00
        # - Stops from 16:00
        # - Breaks from 12:00
        # - Breaks to 13:00
        
        schedule_obj = self.pool.get('hr.advanced.working.schedule')
        
        schedule = schedule_obj.read(cr, uid, advanced_schedule_id, 
                                     ['work_from', 'work_to', 'break_from', 'break_to'],
                                     context=context)
        break_hour = 0.0
        if schedule and schedule['break_from'] and schedule['break_to']:
            work_from = time_obj.compute_datetime(cr, uid, name, schedule['work_from'][0], context=context)
            work_to = time_obj.compute_datetime(cr, uid, name, schedule['work_to'][0], context=context)
            break_from = time_obj.compute_datetime(cr, uid, name, schedule['break_from'][0], context=context)
            break_to = time_obj.compute_datetime(cr, uid, name, schedule['break_to'][0], context=context)
            # Overtime starts after 12:00 and ends before 13:00 (wrong data input by user)
            if datetime_start > break_from and datetime_stop < break_to:
                raise osv.except_osv(_('Warning'), _('DateTime Start and DateTime End does not match the Advanced Working Schedule!'))
            # Overtime starts before 7:00
            if datetime_start < work_from:
                datetime_start = work_from
            # Overtime stops after 16:00
            if datetime_stop > work_to:
                datetime_stop = work_to
            # Overtime stops before 7:00 or starts after 16:00 (wrong data input by user)
            if datetime_start >= datetime_stop:
                raise osv.except_osv(_('Warning'), _('DateTime Start and DateTime End does not match the Advanced Working Schedule!'))
            # Overtime starts in the break time
            if datetime_start > break_from and datetime_start < break_to:
                datetime_start = break_to
            # Overtime stops in the break time
            if datetime_stop > break_from and datetime_stop < break_to:
                datetime_stop = break_from
            # Overtime starts before or on break from OR
            # Overtime stops after or on break to.
            if datetime_start <= break_from and datetime_stop >= break_to:
                break_hour = time_obj.diff_hour(break_from, break_to)
            # Overtime starts after the break OR
            # Overtime ends before the break
            # => break_hour = 0
        res['value']['break_hour'] = break_hour   
        res['value']['working_hour'] = time_obj.diff_hour(datetime_start, datetime_stop)- break_hour
        return res
    
hr_overtime()
