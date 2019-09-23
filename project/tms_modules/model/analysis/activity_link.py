# -*- coding: utf-8 -*-

from openerp import models, fields


class ActivityLink(models.Model):
    _name = 'activity.link'

    name = fields.Char(string='Name')
    url = fields.Char(string='URL')
    activity_id = fields.Many2one('tms.activity', string='Activity')
