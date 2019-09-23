# -*- encoding: utf-8 -*-
from openerp import models, fields


class MultiHostDatabase(models.Model):
    _name = "tms.wkhtmltopdf.version"
    _description = "Wkhtmltopdf version"

    name = fields.Char("Wkhtmltopdf Version", size=256, required=1)
