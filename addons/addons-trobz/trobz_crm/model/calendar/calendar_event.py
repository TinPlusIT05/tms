# -*- coding: utf-8 -*-
from openerp import models, fields


class calendar_event(models.Model):
    _inherit = 'calendar.event'

    description = fields.Html('Description')
