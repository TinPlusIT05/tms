# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
from datetime import datetime
from dateutil.relativedelta import relativedelta

class hr_advanced_working_time(osv.osv):
    
    _name = 'hr.advanced.working.time'
    _description = "Advanced working time"
    _order = "name"
    _columns = {
        'name': fields.char('Name'),
        'day': fields.selection([('today','Today'), ('nextday','Next day')], 'Day', required=1), 
        'hour': fields.float('Hour', required=1), 
    }
    
    _sql_constraints = [
        ('day_hour_uniq', 'unique(day, hour)', 'The advanced working time must be unique !'),
    ]
    
    def diff_hour(self, datetime_start, datetime_stop):
        """
        Delta hours between datetime start to datetime stop
        """
        diff = datetime_stop - datetime_start
        return float(diff.days) * 24 + (float(diff.seconds) / 3600)

    def delta_hours(self, time_from, time_from_type, time_to, time_to_type):
        """
        Generic function
        Use to calculate the expected working hours and the break time
        + Today/Nextday the same 
            delta hours = work to - work from
        + Work From Today and Work To Nextday
            delta hours = work to + (24 - work from)
        @param time_from_type, time_to_type: advanced working time > day
        @param time from, time_to: advanced working time > hour  
        @return: delta hour 
        """
        hours = 0
        if time_from_type == time_to_type:
            hours = time_to - time_from
        else:
            hours = (24 - time_from) + time_to
        return hours
    
    def compute_datetime(self, cr, uid, date, working_time_id, get_str=False, context=None):
        """
        Generic function
        Get datetime from the date and working time.
        @param get_str: True to get the value of type string. False to get the value of type datetime.
        """
        working_time = self.read(cr, uid, working_time_id, ['hour', 'day'], context=context)
        hour =  1 * working_time['hour']
        minute = (1.0 * working_time['hour'] - hour) * 60.0
        if working_time['day'] == 'today':
            res_dt = datetime.strptime(date, '%Y-%m-%d') \
                            + relativedelta(hours = hour, minutes = minute)
        else:
            res_dt = datetime.strptime(date, '%Y-%m-%d') \
                            + relativedelta(hours = hour + 24, minutes = minute)
        return self.pool.get('trobz.base').convert_from_current_timezone_to_utc(cr, uid, res_dt,
                                                                                get_str=get_str, context=context)
    
    def create(self, cr, uid, vals, context=None):
        """
        Advanced working time name = <day, hour>
        """
        day = vals.get('day', '')
        day = day == 'today' and 'Today' or 'Next day'
        hour = vals.get('hour', 0)
        str_hour = hour >= 10 and str(int(hour)) or '0' + str(int(hour))  
        minute = int((hour - int(hour))* 60)
        str_minute = minute >= 10 and str(minute) or '0' + str(minute)
        name = day + ', ' + str_hour + ':'+ str_minute
        vals.update({'name': name})
        return super(hr_advanced_working_time, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        """
        Advanced working time name = <day, hour>
        """
        ad_time = self.browse(cr, uid, ids[0], fields_process=['day','hour'], context=context)
        day = vals.get('day', ad_time.day)
        day = day == 'today' and 'Today' or 'Next day'
        hour = vals.get('hour', ad_time.hour)
        str_hour = hour >= 10 and str(int(hour)) or '0' + str(int(hour))  
        minute = int((hour - int(hour))* 60)
        str_minute = minute >= 10 and str(minute) or '0' + str(minute)
        name = day + ', ' + str_hour + ':'+ str_minute
        vals.update({'name': name})
        return super(hr_advanced_working_time, self).write(cr, uid, ids, vals, context=context)
    
hr_advanced_working_time()
