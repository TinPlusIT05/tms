# -*- encoding: utf-8 -*-
from openerp import api, models, fields
import datetime


class tms_internal_tools(models.Model):
    _name = "tms.internal.tools"
    _description = "Internal Tools"
    _order = "name"

    name = fields.Char(
        help='emoi / anhoi / auditoi', required=1
    )
    host_group = fields.Char(
        'Host group',
        help='Limit to host group to be deployed, ie: integration')
    host_ids = fields.Many2many(
        'tms.host',
        'internal_tools_host_rel',
        'internal_tools_id', 'host_id',
        'Host',
        help='Limit to one / multiple host(s) to be deployed'
    )
    awx_job_history_ids = fields.One2many(
        comodel_name='tms.awx.job.history',
        inverse_name='internal_tools_id', string='AWX Job History')
