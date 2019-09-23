# -*- encoding: utf-8 -*-

from openerp import models, fields


class tms_forge_subscriber(models.Model):

    _name = 'tms.forge.subscriber'
    _description = 'TMS Forge Subscriber'

    name = fields.Many2one('res.users', 'Users', required=True)
    forge_notif_ref_id = fields.Many2one('notification.preferences',
                                         'Forge Notification Preference')
    project_id = fields.Many2one('tms.project', 'TMS Project')
    forge_id = fields.Many2one('tms.forge.ticket', 'TMS Forge Ticket')
