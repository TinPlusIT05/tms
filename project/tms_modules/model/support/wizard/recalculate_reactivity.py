# -*- coding: utf-8 -*-
##############################################################################
from openerp import api, models


class recalculate_reactivity(models.TransientModel):

    _name = 'recalculate.reactivity'
    _description = 'Recalculate reactivity'

    @api.multi
    def button_auto_trigger_recalculate_reactivity(self):
        support_ticket = self.env['tms.support.ticket']
        support_ticket.run_identify_support_tickets_missing_reactivity()
        return {
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window_close'
        }
