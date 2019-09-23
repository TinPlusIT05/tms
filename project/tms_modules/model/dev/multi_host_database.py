# -*- encoding: utf-8 -*-
from openerp import models, fields as fields_v8


class MultiHostDatabase(models.Model):
    _name = "multi.host.database"
    _description = "Multi Host Database"

    host_id = fields_v8.Many2one('tms.host', string="Host")
    master = fields_v8.Boolean(string="Master")
    instance_id = fields_v8.Many2one('tms.instance', string="Instance")
