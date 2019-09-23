# -*- coding: utf-8 -*-
from openerp import models, fields, api


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.multi
    def _job_history_count(self):
        """
        Count number of job history records
        """
        history_obj = self.env['hr.job.history']
        for employee in self:
            employee.job_history_count = \
                history_obj.search_count([('employee_id', '=', employee.id)])

    job_history_count = fields.Integer(compute=_job_history_count)
  
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
