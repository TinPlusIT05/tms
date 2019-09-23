# -*- encoding: UTF-8 -*-
##############################################################################
from openerp import models, fields


class HrJob(models.Model):
    _inherit = "hr.job"

    productivity = fields.Integer('Productivity (%)')
    job_type_id = fields.Many2one('hr.job.type', 'User Job Type')
    work_seniority_interval = fields.Integer(
        'Work Seniority Interval',
        default=1)
    extra_annual_leaves_for_work_seniority = fields.Float(
        'Extra Annual Leaves for Work Seniority',
        digits=(1, 1),
        default=0.5)


HrJob()
