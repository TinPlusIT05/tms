# -*- encoding: utf-8 -*-
from openerp import models, fields


class tms_ticket_task_type_family(models.Model):

    _name = "tms.ticket.task.type.family"
    _description = "TMS Ticket Task Type Family"

    name = fields.Char('Name', required=True)
