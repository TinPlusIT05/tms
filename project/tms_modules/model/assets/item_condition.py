# -*- coding: utf-8 -*-
from openerp import models, fields


class ItemCondition(models.Model):
    _name = 'item.condition'
    _description = 'Assets Condition that it used for maintenance information.'

    name = fields.Char(string="Short Description")
    description = fields.Text(string="Full details")
