# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2016 Trobz (<http://trobz.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api


class UpdateSubscriptionsWizard(models.TransientModel):
    _name = 'update.subscriptions.wizard'
    # Fields
    user_id = fields.Many2one('res.users', 'Subscriber User', required=True,
                              default=lambda self: self.env.user)
    tk_notif_pre_id = fields.Many2one('notification.preferences',
                                      "Ticket Notification Preference")

    @api.onchange('user_id')
    def onchange_sub_user(self):
        res = False
        if self.user_id.notif_pref_id:
            # The Notification Preference of the User
            res = self.user_id.notif_pref_id.id
        elif self.user_id.group_profile_id and \
                self.user_id.group_profile_id.notif_pref_id:
            # The Notification Preference of the Profile
            res = self.user_id.group_profile_id.notif_pref_id.id
        self.tk_notif_pre_id = res

    @api.multi
    def update_subscriptions(self):
        model = self._context.get('active_model', False)
        ticket_ids = self._context.get('active_ids', [])
        subscriber_obj = self.env['tms.subscriber']
        for wizard in self:
            for ticket_id in ticket_ids:
                # Update Subcription Forge Ticket
                if model == 'tms.forge.ticket':
                    ticket_type = 'forge_id'
                else:
                    ticket_type = 'support_id'
                subcribers = subscriber_obj.search(
                    [('name', '=', wizard.user_id.id),
                     (ticket_type, '=', ticket_id)])
                if not subcribers:
                    vals = {'name': wizard.user_id.id,
                            'tk_notif_pref_id': wizard.tk_notif_pre_id.id,
                            ticket_type: ticket_id}
                    subscriber_obj.create(vals)
                else:
                    subscriber_obj |= subcribers
            if subscriber_obj:
                subscriber_obj.write(
                    {'tk_notif_pref_id': wizard.tk_notif_pre_id.id})
