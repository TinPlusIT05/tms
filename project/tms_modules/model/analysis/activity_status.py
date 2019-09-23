# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import date


class ActivityStatus(models.Model):
    _name = 'activity.status'
    _order = 'date desc'
    name = fields.Char(string='Name', compute='_compute_name')
    status = fields.Text(string='Status')
    date = fields.Date(string='Date',  default=fields.Date.today())
    activity_id = fields.Many2one('tms.activity', string='Activity',
                                  required=True)

    @api.multi
    def _compute_name(self):
        today = str(date.today())
        for status in self:
            status.name = '%s %s' % (status.activity_id and
                                     status.activity_id.name or '', today)
