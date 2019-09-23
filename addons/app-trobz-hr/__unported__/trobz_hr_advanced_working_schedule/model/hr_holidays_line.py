# -*- encoding: utf-8 -*-
from openerp.osv import osv

class hr_holidays_line(osv.osv):    
    _description = 'Leave request lines'
    _inherit = 'hr.holidays.line' 
    
    def plus_day(self, cr, uid, has_working_hours, datetime_day, dayofweek, date_type, country_id, context=None):
        """
        @param has_working_hours: Advanced Working Plan Template 
        @param datetime_day: (Datetime) date
        @param dayofweek: Day of week
        @param country_id: country
        @return: number of day off (1 or 0.5)
        
        Ticket #5078
        Override plus day in hr_holidays 
        Calculate number of days on Leave Request Lines based on advanced working plan template
        """
        public_obj = self.pool.get('trobz.hr.public.holidays')
        pub_hol= public_obj.search(cr, uid, [('country', '=', country_id), ('date', '=', datetime_day.strftime('%Y-%m-%d')), ('template_holidays', '<>', True)], context=context)
        if pub_hol:
            return 0
        day = 1
        if has_working_hours:
            # search flexible day:
            working_hours_obj = self.pool.get('resource.calendar')
            working = working_hours_obj.read(cr, uid, has_working_hours, ['attendance_ids'], context=context)
            schedule_obj = self.pool.get('resource.calendar.attendance')
            for schedule in schedule_obj.browse(cr, uid, working['attendance_ids'], context=context):
                if schedule.dayofweek == str(dayofweek) and not schedule.advanced_schedule_id:
                    return 0
            day = date_type == 'full' and 1 or 0.5
        else:
            if datetime_day.weekday() not in (5, 6):
                day = date_type == 'full' and 1 or 0.5
        return day
        
hr_holidays_line()