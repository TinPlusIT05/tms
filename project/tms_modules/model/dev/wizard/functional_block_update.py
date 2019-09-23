# -*- coding: utf-8 -*-
##############################################################################
from openerp import api, models
from openerp.exceptions import Warning


class functional_block_update(models.TransientModel):

    _name = 'functional.block.update'
    _description = 'Functional Block of forge tickets'

    @api.model
    def get_functional_block(self, ticket_ids):
        fblock_obj = self.env['tms.functional.block']
        forge_obj = self.env['tms.forge.ticket']
        functional_block_objs = fblock_obj.search([])
        if not functional_block_objs:
            raise Warning('Forbidden action!',
                          'You must define some functional blocks first!')
        tickets = forge_obj.browse(ticket_ids)
        for ticket in tickets:
            best_choice = {
                'id': functional_block_objs and functional_block_objs.ids[0],
                'rank': 0
            }
            for functional_block in functional_block_objs:
                if (functional_block.project_ids and
                        ticket.project_id.id in
                        functional_block.project_ids.ids) \
                        or not functional_block.project_ids:
                    rank = ticket.summary.upper().count(
                        functional_block.name.upper()) * 2
                    if ticket.description:
                        rank += ticket.description.upper().count(
                            functional_block.name.upper())
                    if rank > best_choice['rank']:
                        best_choice = {
                            'id': functional_block.id, 'rank': rank
                        }
            if best_choice['rank'] != 0:
                best_choice_id = best_choice['id']
                ticket.write({'tms_functional_block_id': best_choice_id})
        return True

    @api.multi
    def functional_block_update(self):
        ticket = self.env['tms.forge.ticket']
        tickets = ticket.search([('tms_functional_block_id', '=', False)])
        if len(tickets.ids) > 0:
            self.get_functional_block(tickets.ids)
        return {
            'type': 'ir.actions.act_window_close'
        }
