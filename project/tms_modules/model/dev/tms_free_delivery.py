# -*- encoding: utf-8 -*-
from openerp import models, fields, api


class tms_free_delivery(models.Model):

    _name = "tms.free.delivery"
    _description = "Tms Free Delivery"

    @api.onchange('project_id')
    def onchange_project_id(self):
        self.instance_id = False

    # Columns
    date = fields.Datetime(string='Date')

    project_id = fields.Many2one(
        'tms.project', string='Project', required=True)

    instance_id = fields.Many2one(
        'tms.free.instance', string='Free Instance',
        required=True, domain="[('project','=',project_id)]")

    comment = fields.Text(string="Comment")
