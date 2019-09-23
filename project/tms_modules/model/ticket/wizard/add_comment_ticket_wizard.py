# -*- coding: utf-8 -*-
from openerp import models, api, fields


class add_comment_ticket_wizard(models.TransientModel):

    _name = "add.comment.ticket.wizard"

    comment = fields.Text(string='Comment')

    @api.multi
    def button_add_comment(self):
        context = self._context and self._context.copy() or {}
        active_model = context.get('active_model', False)
        active_id = context.get('active_id', False)
        if active_model == 'tms.support.ticket':
            support_ticket = self.env['tms.support.ticket'].browse(active_id)
            vals = {
                'tms_support_ticket_comment_ids': [
                    [0, False, {'comment': self.comment, 'is_invalid': False,
                                'type': 'comment'}]]
            }
            support_ticket.write(vals)
            return True
        else:
            forge_ticket = self.env['tms.forge.ticket'].browse(active_id)
            vals = {
                'tms_forge_ticket_comment_ids': [
                    [0, False, {'comment': self.comment, 'is_invalid': False,
                                'type': 'comment'}]]
            }
            forge_ticket.write(vals)
            return True
