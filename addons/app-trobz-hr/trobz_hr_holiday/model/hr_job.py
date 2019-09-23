# -*- encoding: utf-8 -*-
from openerp import models, fields


class hr_job(models.Model):
    _inherit = 'hr.job'
    work_seniority_interval = fields.Integer('Work Seniority Interval')
    extra_annual_leaves_for_work_seniority = fields.Float(
        'Extra Annual Leaves for Work Seniority', digits=(1, 1))

hr_job()
