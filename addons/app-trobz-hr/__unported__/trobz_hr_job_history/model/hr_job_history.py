# -*- coding: utf-8 -*-
from openerp.osv import osv, fields


class hr_job_history(osv.Model):
    _name = "hr.job.history"

    _columns = {
        'name': fields.char('Description'),
        'employee_id': fields.many2one('hr.employee', 'Employee', required=1),
        'contract_id': fields.many2one('hr.contract', 'Contract', required=1),
        'department_id': fields.many2one('hr.department', 'Department'),
        'previous_job_id': fields.many2one('hr.job', 'Previous Job'),
        'current_job_id': fields.many2one('hr.job', 'Current Job'),
        'date_of_change': fields.date('Effective Date', required=1),
        'responsible_user_id': fields.many2one('res.users', 'Responsible'),
    }
    _default = {
        'responsible_user_id': lambda self, cr, uid, context=None: uid,
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
