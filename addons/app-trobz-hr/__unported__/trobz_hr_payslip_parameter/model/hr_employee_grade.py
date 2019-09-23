# -*- encoding: utf-8 -*-
##############################################################################

from openerp.osv import osv, fields

class hr_employee_grade(osv.osv):
    _name = "hr.employee.grade"
    _description = "Employee Grade"
    
    _columns = {
        'name': fields.char('Name', readonly=1),
        'level_id':fields.many2one('hr.employee.level', 'Level', required=True),
        'job_id': fields.many2one('hr.job', 'Job Category', required=True),
    }
    
    def create(self, cr, uid, vals, context=None):
        """
        Override fnct:
        Get grade name
        """
        if not vals.get('name', False):
            emp_job = self.pool.get('hr.job').read(cr, uid, vals['job_id'], ['name'], context=context)
            emp_level = self.pool.get('hr.employee.level').read(cr, uid, vals['level_id'], ['name'], context=context)
            
            vals['name'] = emp_job['name'] + " " + emp_level['name']
        return super(hr_employee_grade, self).create(cr, uid, vals, context=context)
    
    def write(self, cr, uid, ids, vals, context=None):
        """
        Override fnct:
        Get grade name
        """
        if not vals.get('name', False):
            grade = self.browse(cr, uid, ids[0], context=context)
            job_obj = self.pool.get('hr.job')
            level_obj = self.pool.get('hr.employee.level')
            emp_job_name = 'job_id' in vals and job_obj.read(cr, uid, vals['job_id'], ['name'], context=context)['name'] or grade.job_id.name
            emp_level_name = 'level_id' in vals and level_obj.read(cr, uid, vals['level_id'], ['name'], context=context)['name'] or grade.level_id.name
            
            vals['name'] = emp_job_name + " " + emp_level_name
        return super(hr_employee_grade, self).write(cr, uid, ids, vals, context=context)
    
hr_employee_grade()
