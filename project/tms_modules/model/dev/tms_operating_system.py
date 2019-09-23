# -*- encoding: utf-8 -*-
from openerp import models, fields


class tms_operating_system(models.Model):

    _name = 'tms.operating.system'
    _description = 'Operating System'
    _order = 'name ASC'

    # Columns
    name = fields.Char('Operating System Name', size=256, required=True)

    _sql_constraints = [
        ('operating_system_unique',
         'unique (name)',
         'This operating system already exists!')
    ]
