# -*- coding: utf-8 -*-

from openerp.osv import osv, fields

class resource_calendar_attendance(osv.osv):
    _inherit = "resource.calendar.attendance"
    _description = "Advanced working plan template line"
    _order = 'day, dayofweek, hour_from'
    
    _columns = {
        'day': fields.integer('Day'),
        'is_flexible': fields.boolean('Flexible Day'),
        'advanced_schedule_id': fields.many2one("hr.advanced.working.schedule", "Advanced Working Schedule"),
    }
    
    _sql_constraints = [
        ('day_uniq', 'unique(name, calendar_id)', 'The day of the schedule must be unique !'),
        ('day_check', 'CHECK(day > 0)', 'The day of the schedule must be greater than 0!'),
    ] 
 
    def onchange_schedule(self, cr, uid, ids, advanced_schedule_id, day, context=None):
        """
        Name is Day1, day2, ...
        Get the work from and the work to of the original working schedule line 
        """
        res = {'value': {}}
        if not advanced_schedule_id:
            return res
        
        schedule_obj = self.pool.get('hr.advanced.working.schedule')
        schedule = schedule_obj.browse(cr, uid, advanced_schedule_id, 
                                       fields_process=['work_from', 'work_to'], 
                                       context=context)
        res['value'].update({
                            'name': 'day' + str(day),
                            'hour_from': schedule.work_from.hour,
                            'hour_to': schedule.work_to.hour,
                            })
        return res 
    
resource_calendar_attendance()