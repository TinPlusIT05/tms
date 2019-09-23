# -*- coding: utf-8 -*-
from openerp import fields, models, _


class tms_job_type(models.Model):
    _name = "tms.job.type"
    _description = "Job Type"
    _rec_name = "label"

    label = fields.Char('Label', required=True)
    code = fields.Char('Code')
    description = fields.Text('Description')

    _sql_constraints = [
        ('code_uniq', 'unique (code)',
            _('The code of job type must be unique!'))
    ]
