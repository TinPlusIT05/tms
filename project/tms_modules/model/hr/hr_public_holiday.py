# -*- encoding: utf-8 -*-
from openerp import models, fields


class hr_public_holiday(models.Model):
    _inherit = "hr.public.holiday"

    code = fields.Char(string="Code", default="H")
