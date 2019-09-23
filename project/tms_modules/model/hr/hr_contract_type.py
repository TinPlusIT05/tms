# -*- coding: utf-8 -*-
from openerp import models, fields


class HrContractType(models.Model):

    _inherit = 'hr.contract.type'

    auto_tick_trial = fields.Boolean(
        string='Auto-tick Trial',
        default=False,
        help='If ticked, contracts of this type will be marked Trial Contract \
        automatically.'
    )
