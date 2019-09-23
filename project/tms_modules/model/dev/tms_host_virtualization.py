# -*- encoding: utf-8 -*-
from openerp import fields, models


class tms_host_virtualization(models.Model):

    _name = "tms.host.virtualization"
    _description = "Host Virtualization"

    # Columns
    name = fields.Char('Host Name', size=256, required=True)
