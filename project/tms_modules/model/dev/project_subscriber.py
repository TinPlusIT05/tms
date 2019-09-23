# -*- encoding: utf-8 -*-


from openerp import models, fields


class project_subscriber(models.Model):

    _name = "project.subscriber"
    _description = "Project Subscriber"

    name = fields.Many2one('res.users', 'User', required=True)
    notif_pref_id = fields.Many2one('notification.preferences',
                                    'Project Notification Preference')
    tms_project_id = fields.Many2one('tms.project', 'Project')

    _sql_constraints = [
        ('ref_uniq', 'unique (name,tms_project_id)', 'User must be unique!')
    ]
