# -*- encoding: UTF-8 -*-
from openerp import fields, models


class HrJobType(models.Model):

    _name = "hr.job.type"

    name = fields.Char("Name", required=True)
