# -*- encoding: utf-8 -*-
from openerp import fields, models


class tms_free_instance(models.Model):

    _name = "tms.free.instance"
    _description = "TMS Free Instance"
    _order = "name"

    name = fields.Char(string='Name', required=True, size=256)
    description = fields.Text("Description")
    project_type = fields.Many2one('tms.project.type', 'Project Type')
    project = fields.Many2one('tms.project', 'Project')
    configuration = fields.Text('Configuration')
    version = fields.Char('Version', size=256)
    host = fields.Char('Host', size=256)

    _sql_constraints = [
        ('tms_free_instance_name_unique',
         'unique(name)',
         "The name must be unique!")
    ]
