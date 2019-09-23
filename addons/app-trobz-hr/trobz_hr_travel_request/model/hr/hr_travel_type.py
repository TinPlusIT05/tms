# -*- coding: utf-8 -*-

from openerp import models, fields


class hr_travel_type(models.Model):
    _name = 'hr.travel.type'
    _description = 'Travel Type'
    _order = 'name'

    # Columns
    name = fields.Char(string="Name", required=True,
                       size=64, select=True)

hr_travel_type()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
