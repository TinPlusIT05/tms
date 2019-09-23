# -*- coding: utf-8 -*-
from openerp import models, fields


class trobz_crm_event_type(models.Model):
    _name = "trobz.crm.event.type"
    _description = "Event Type"
    _order = "name"

    name = fields.Char('Event Type', size=256, required=True)
    display_email_fields = fields.Boolean(
        'Display Email Fields', help='from, to, cc, attachment...'
    )
    display_meeting_fields = fields.Boolean(
        'Display Meeting Fields',
        help='Your participants, Customer Participants...'
    )
    display_ending_at_fields = fields.Boolean('Display Ending at')

trobz_crm_event_type()
