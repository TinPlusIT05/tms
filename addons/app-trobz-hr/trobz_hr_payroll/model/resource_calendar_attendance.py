# -*- coding: utf-8 -*-
from openerp.osv import osv

#Ticket 1414: add type of working schedule line 

class resource_calendar_attendance(osv.osv):
    _inherit = "resource.calendar.attendance"
    def type_working_calendar(self, cr, uid, resource_calendar_id, day, context=None):
        """ Get type of working days 
        @param resource_calendar_id: resource.calendar browse record
        @param day: datetime object

        @return: if type id half return 0.5 
        """
        res = 0.0
        for working_day in resource_calendar_id.attendance_ids:
            if (int(working_day.dayofweek) + 1) == day.isoweekday():
                res += 0.5
        return res
resource_calendar_attendance()
