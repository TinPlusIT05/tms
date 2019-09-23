# -*- encoding: utf-8 -*-
from openerp import models, api, fields, _
from .tms_forge_ticket import TmsForgeTicket
from openerp.exceptions import Warning
from datetime import datetime
import logging

FORGE_STATES = [
    ('assigned', 'Assigned'),
    ('wip', 'WIP'),
    ('code_completed', 'Code completed'),
    ('ready_to_deploy', 'Ready To Deploy'),
    ('in_qa', 'QA'),
    ('closed', 'Closed')
]


class ForgeTicketAssign(models.Model):

    _name = "forge.ticket.assign"
    _description = "Forge Ticket Assign"
    _order = 'date desc'
    _rec_name = 'forge_id'

    forge_id = fields.Many2one(
        'tms.forge.ticket', string='Forge Ticket ID', required=True,
        select=1, readonly=True)
    date = fields.Datetime(string='Date', readonly=True)
    assignee_id = fields.Many2one('res.users', string='Assignee', readonly=True)
    forge_state = fields.Selection(
        FORGE_STATES, string='Forge State', readonly=True)
