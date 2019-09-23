# -*- coding: utf-8 -*-

from openerp.osv import osv, fields

class hr_advanced_working_schedule(osv.osv):
    
    _name = 'hr.advanced.working.schedule'
    _description = "Advanced working schedule"
    _columns = {
        'name': fields.char('Name', required=1),
        'work_from': fields.many2one('hr.advanced.working.time', 'Work From', required=1), 
        'work_to': fields.many2one('hr.advanced.working.time', 'Work To', required=1), 
        'break_from': fields.many2one('hr.advanced.working.time', 'Break From'),
        'break_to': fields.many2one('hr.advanced.working.time', 'Break To'),
        'activity_id': fields.many2one('hr.working.activity', 'Activity', required=1),
    }
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The Name of the advance working schedule must be unique !'),
    ]
    
    def _check_work_from_to(self, cr, uid, ids, context=None):
        """
        Check work from < work to
        """
        for obj in self.browse(cr, uid, ids, context=context):
            if (obj.work_from.day == obj.work_to.day and obj.work_from.hour >= obj.work_to.hour) \
                or (obj.work_from.day != obj.work_to.day and obj.work_to.day == 'today'):
                return False
        return True
    
    def _check_break_from_to(self, cr, uid, ids, context=None):
        """
        Check break from < break to
        """
        for obj in self.browse(cr, uid, ids, context=context):
            if (obj.break_from and obj.break_to) \
                and ((obj.break_from.day == obj.break_to.day and obj.break_from.hour >= obj.break_to.hour) \
                or (obj.break_from.day != obj.break_to.day and obj.break_to.day == 'today')):
                return False
        return True
    
    _constraints = [
        (_check_work_from_to, 'The work to must be greater than the work from', ['work_from','work_to']),
        (_check_break_from_to, 'The break to must be greater than the break from', ['break_from','break_to']),
    ]
    
hr_advanced_working_schedule()
