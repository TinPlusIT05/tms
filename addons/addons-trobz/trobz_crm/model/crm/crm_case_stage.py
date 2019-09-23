# -*- coding: utf-8 -*-
from openerp import models, fields


class crm_case_stage(models.Model):
    _inherit = 'crm.case.stage'

    open_status = fields.Boolean('Open Status')
