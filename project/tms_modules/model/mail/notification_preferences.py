# -*- encoding: utf-8 -*-


from openerp import models, fields, api


class notification_preferences(models.Model):

    _name = "notification.preferences"
    _description = "Notification Preferences"

    name = fields.Char('Name', size=256, required=True)
    use_by_subscribe_me = fields.Boolean(
        'Used by Subscribe Me',
        help="Check this box for TMS to use this Notification Preferences"
        " when using the Subscribe Me")
    forge_field_ids = fields.Many2many(
        'ir.model.fields', 'notif_tms_forge_field_rel',
        'notif_id', 'forge_field_id', string="Forge", copy=False,
        help="When a value will be change in one of those fields, "
        "the user should be notified.")
    support_field_ids = fields.Many2many(
        'ir.model.fields', 'notif_tms_support_field_rel',
        'notif_id', 'support_field_id', string="Support", copy=False,
        help="When a value will be change in one of those fields, "
        "the user should be notified.")
    receive_notif_for_my_action = fields.Boolean(
        'Receive Notifications for My Actions')

    @api.model
    def _get_subscribe_me_notif_id(self):
        """
        Get Notification preference when using feature `Subscribe Me` on ticket
        - Get Notification preference with use_by_subscribe_me checked
        - If NOT, get the notification preference defined on current user.
        """
        notif_obj = self.env['notification.preferences']
        notif = notif_obj.sudo().search([('use_by_subscribe_me', '=', True)])
        if notif:
            notif_id = notif[0].id
        else:
            user_notif = self.env.user.notif_pref_id
            notif_id = user_notif and user_notif.id or False
        return notif_id
