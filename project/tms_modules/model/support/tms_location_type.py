# -*- coding: utf-8 -*-

from openerp import fields, models, _


class TmsLocationType(models.Model):
    _name = 'tms.location.type'
    _description = 'Location Type'

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    holiday_status_id = fields.Many2one(
        'hr.holidays.status',
        'Leave Type',
        require=True
    )

    _sql_constraints = [
        ('code_uniq', 'unique (code)',
            _('The code of location type must be unique!'))
    ]
