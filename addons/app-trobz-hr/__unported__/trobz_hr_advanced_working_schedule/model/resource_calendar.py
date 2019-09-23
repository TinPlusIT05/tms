# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta

class resource_calendar(osv.osv):
    _inherit = "resource.calendar"
    _description = "Advance working plan template"

    _columns = {
        'min_flexible_days': fields.float('Minimal Flexible Days'),
        'expected_working_days': fields.float('Expected Working Days', required=1),
        'cycle': fields.integer('Cycle', required=1),
    }
        
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The Name of the advance working plan template must be unique !'),
        ('cycle_check', 'CHECK(cycle > 0)', 'Please input the cycle!'),
        ('expected_working_days_check', 'CHECK(expected_working_days > 0)', 'Please input the expected working days!'),
    ]
    
    def find_day_of_cycle(self, cr, uid, plan_id, cycle, date):
        """
        Find the day of cycle of this date
        + If date is the first date of this month 
            The day of cycle will be found in the first week of cycle 
        + If NOT 
            The day of cycle of this date = day of cycle first month + (this date - first date of this month)%cycle
        Get the plan line the day of cycle that must be unique on a cycle    
        @param date: datetime.date
        @param plan_id: Advanced working plan template
        @param cycle: Day in cycle of Advanced working plan template
        @return: The day of this day in cycle
        """
        
        first_date = date + relativedelta(day=1)
        dayofweek = first_date.weekday()
        #Find day of cycle of the first_date
        cr.execute("""SELECT day 
                          FROM resource_calendar_attendance 
                          WHERE calendar_id = %s 
                          AND dayofweek = '%s' 
                          AND day <=7"""%(plan_id, dayofweek))
        res = cr.fetchone()
        if not res:
            raise osv.except_osv(_('Warning!'),
                        _('Please set up the advanced working schedule for this date (%s).'%(date.strftime('%d/%m/%Y'))))
        day_of_cycle = res[0]
        if date > first_date:
            day_of_cycle = (day_of_cycle + (date - first_date).days)%cycle
        return day_of_cycle == 0 and cycle or day_of_cycle

    def create(self, cr, uid, vals, context=None):
        """
        Override Fnct:
        Check if minimal flexible days > 0, must exist a schedule line is flexible day
        """
        if vals.get('min_flexible_days') > 0:
            res = False
            for line in vals['attendance_ids']:
                if line[2] and line[2].get('is_flexible', False):
                    res = True
                    break
            if not res:
                raise osv.except_osv(_('Warning!'),_('There is no flexible day defined for this schedule'))
        return super(resource_calendar, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        """
        Override Fnct:
        Check if minimal flexible days > 0, must exist a schedule line is flexible day
        """
        
        if vals.get('min_flexible_days') > 0:
            if 'attendance_ids' not in vals:
                # Get flexible days frome DB 
                cr.execute("""SELECT day from resource_calendar_attendance 
                            WHERE is_flexible = True 
                            AND calendar_id in (%s)"""%(','.join(map(str,ids))))
                res = cr.fetchone()
                if not res:
                    raise osv.except_osv(_('Warning!'),_('There is no flexible day defined for this schedule'))
            else:
                # Get flexbile days from the changed data (vals['attendance_ids'])
                res = False
                for line in vals['attendance_ids']:
                    if line[2] and line[2].get('is_flexible', False):
                        res = True
                        break
                if not res:
                    raise osv.except_osv(_('Warning!'),_('There is no flexible day defined for this schedule'))
            
        return super(resource_calendar, self).write(cr, uid, ids, vals, context=context)

    def onchange_cycle(self, cr, uid, ids, cycle, context=None):
        """
        Auto create Advanced Working Plan Template Lines 
        Only for a new Advanced Working Plan Template
        @param cycle: cycle of Advanced Working Plan Template 
        @return: Advanced Working Plan Template Line
        """
        if ids:
            return {}
        
        lines = []
        advanced_schedule_ids = self.pool.get('hr.advanced.working.schedule').search(cr, uid, [], context=context)
        for day in range(1, cycle+1):
            item = {'advanced_schedule_id': advanced_schedule_ids[0], 
                    'day': day, 
                    'name': 'Day%s'%day,
                    'dayofweek': str((day-1)%7), 
                    }
            lines.append(item)
            
        return {'value': {'attendance_ids': lines}}
    
resource_calendar()