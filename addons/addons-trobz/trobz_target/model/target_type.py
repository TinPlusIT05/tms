# -*- coding: utf-8 -*-

from openerp import fields, models

class trobz_target_type(models.Model):
    _name = "target.type"
    _description = "Target Type"
    _order = 'name'

    # Columns
    name = fields.Char(string="Name", size=256)
    description = fields.Text(string="Description")

trobz_target_type()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
