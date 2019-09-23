# -*- encoding: utf-8 -*-


from openerp import models, fields, api


class tms_subscriber(models.Model):

    _name = "tms.subscriber"
    _description = "TMS Subscriber"

    name = fields.Many2one('res.users', 'User', required=True)
    tk_default_notif_pre_id = fields.Many2one(
        compute='_default_notif_preference',
        comodel_name='notification.preferences',
        string="Ticket Default Notification Preference",
        store=True)
    tk_notif_pref_id = fields.Many2one(
        'notification.preferences', 'Ticket Notification Preference')
    forge_id = fields.Many2one('tms.forge.ticket', 'Forge Ticket')
    support_id = fields.Many2one('tms.support.ticket', 'Support Ticket')

    _sql_constraints = [
        ('ref_uniq_forge', 'unique (name,forge_id)',
         'This user was added already in the subscriber of this ticket!'),
        ('ref_uniq_support', 'unique (name,support_id)',
         'This user was added already in the subscriber of this ticket!')
    ]

    @api.multi
    @api.depends('forge_id.project_id',
                 'support_id.project_id',
                 'name',
                 'name.notif_pref_id')
    def _default_notif_preference(self):
        """
        Function field to calculate the default notification preference:
            The Notification Preference of the Project Subscriber
            or (if not set) from the Notification Preference of the User
            or (if not set) from the Notification Preference of the Profile
            or (if not set) don't send a notification
        Update: remove the re-calculation of the tk_default_notif_pre_id
        when the Default Notification Preference is changed on the related
        profile (`name.group_profile_id.notif_pref_id`).
        """
        for record in self:
            if not record.name:
                # Have no user link to the subscriber line
                continue
            res = False
            project_id = False
            if record.forge_id:
                project_id = record.forge_id.project_id.id or False
            elif record.support_id:
                project_id = record.support_id.project_id.id or False
            if project_id:
                if record.forge_id:
                    ps_ids = self.env['tms.forge.subscriber'].search(
                        [('project_id', '=', project_id),
                         ('name', '=', record.name.id)])
                    if ps_ids and ps_ids[0].forge_notif_ref_id:
                        # The Notification Preference of the Forge Subscriber
                        res = ps_ids[0].forge_notif_ref_id.id
                else:
                    ps_ids = self.env['project.subscriber'].search(
                        [('tms_project_id', '=', project_id),
                         ('name', '=', record.name.id)])
                    if ps_ids and ps_ids[0].notif_pref_id:
                        # The Notification Preference of the Project Subscriber
                        res = ps_ids[0].notif_pref_id.id

                if not res:
                    if record.name.notif_pref_id:
                        # The Notification Preference of the User
                        res = record.name.notif_pref_id.id
                    elif record.name.group_profile_id and \
                            record.name.group_profile_id.notif_pref_id:
                        # The Notification Preference of the Profile
                        res = record.name.group_profile_id.notif_pref_id.id
            record.tk_default_notif_pre_id = res
