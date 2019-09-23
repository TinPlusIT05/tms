# -*- encoding: utf-8 -*-
from openerp import models, fields


class tms_host_group(models.Model):

    _name = "tms.host.group"
    _description = "Host Group"

    # Columns
    name = fields.Char('Name', size=256, required=True)
    config = fields.Serialized(
        'Config', help="Config variable used by Ansible")
