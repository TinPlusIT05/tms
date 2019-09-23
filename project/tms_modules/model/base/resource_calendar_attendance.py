# -*- encoding: UTF-8 -*-
from openerp import api, models, fields


class resource_calendar_attendance(models.Model):

    _inherit = "resource.calendar.attendance"
    _description = "Work Detail"

    number_hours = fields.Float(
        string='Number of hours', required=True, help="Total working time")

    @api.onchange('hour_from', 'hour_to')
    def onchange_hours(self):
        if not self.hour_from or not self.hour_to:
            self.number_hours = 0
        else:
            self.number_hours = self.hour_to - self.hour_from

    @api.model
    def create(self, vals):
        hour_from = vals.get('hour_from', 0)
        hour_to = vals.get('hour_to', 0)
        vals['number_hours'] = hour_to - hour_from
        return super(resource_calendar_attendance, self).create(vals)
