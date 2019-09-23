# -*- coding: utf-8 -*-
from openerp import models, fields


class crm_lost_reason(models.Model):

    _name = 'crm.lost.reason'
    _description = 'Trobz CRM Lost Reason'

    name = fields.Char("Lost Reason", size=128)

crm_lost_reason()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
