# -*- coding: utf-8 -*-
from openerp import models, api


class toggle_subscribe_ticket_wizard(models.TransientModel):

    _name = "toggle.subscribe.ticket.wizard"

    @api.multi
    def button_subscribe(self):
        """
            This button is used to subscribe current user to support ticket(s)
            @note: use Admin permission to make change on support ticket object
            because someobody does have permission to write on it
        """
        context = self._context and self._context.copy() or {}
        active_ids = context.get("active_ids")
        if not active_ids:
            return True

        # Calculate support tickets is subscribed by current user already.
        subscriber_env = self.env['tms.subscriber']
        subscribed_objs = subscriber_env.sudo().search(
            [('support_id', 'in', active_ids), ('name', '=', self._uid)])
        no_update_ids = []
        for sub in subscriber_env.sudo().browse(subscribed_objs.ids):
            no_update_ids.append(sub.support_id.id)

        # Add subscriber for the support ticket not subscribed by this user yet
        notif_env = self.env['notification.preferences']
        notif_id = notif_env._get_subscribe_me_notif_id()
        tms_support_ticket_objs = self.env["tms.support.ticket"].browse(
            list(set(active_ids) - set(no_update_ids)))
        tms_support_ticket_objs.sudo().write(
            {"support_ticket_subscriber_ids":
             [[0, False, {'name': self._uid, 'tk_notif_pref_id': notif_id}]]})
        return {
            'type': 'ir.actions.act_window_close'
        }

    @api.multi
    def button_unsubscribe(self):
        """
            This button is used to unsubscribe the current user
            from support ticket(s)
            @note: you admin permission to make change on support ticket object
            because someobody does have permission to write on it
        """
        context = self._context and self._context.copy() or {}
        active_ids = context.get("active_ids")
        if not active_ids:
            return True

        subscriber_env = self.env['tms.subscriber']
        subscriber_objs = subscriber_env.sudo().search(
            [('support_id', 'in', active_ids), ('name', '=', self._uid)])
        subscriber_objs.sudo().unlink()
        return {
            'type': 'ir.actions.act_window_close'
        }
