# -*- encoding: utf-8 -*-
from openerp import models, fields


class TmsProjectTag(models.Model):

    _name = "tms.project.tag"
    _description = "Project Tag"
    _order = "name"

    name = fields.Char('Name', size=256, required=True)
    description = fields.Text('Description')
    project_id = fields.Many2one('tms.project', 'Project')
