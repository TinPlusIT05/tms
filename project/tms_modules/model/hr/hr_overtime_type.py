
# -*- coding: utf-8 -*-

from openerp import fields, models


class ModuleName(models.Model):
    _name = 'hr.overtime.type'
    _description = 'Hr Overtime Type'

    name = fields.Char(string='Name')
    time = fields.Char(string='Time')
    overtime_pay = fields.Char(string='Overtime Pay')
    description = fields.Char(string='Description')
