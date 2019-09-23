# -*- encoding: utf-8 -*-
from openerp import models, fields


class tms_project_type(models.Model):

    _name = "tms.project.type"
    _description = "Project Type"
    _order = "name"

    name = fields.Char("Name", required=True)

    _sql_constraints = [
        ('tms_project_type_name_unique',
         'unique(name)',
         "The name must be unique!")
    ]
