# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.safe_eval import safe_eval


class hr_config_settings(models.TransientModel):
    _inherit = 'hr.config.settings'

    # Columns
    leave_type_unpaid_ids = fields.Many2many(
        'hr.holidays.status',
        string='Leave Type Unpaid',
    )

    @api.model
    def get_default_leave_type_unpaid_ids(self, fields):
        param_obj = self.env['ir.config_parameter']
        leave_type_unpaid_ids = param_obj.get_param(
            'leave_type_unpaid_ids', '[]'
        )
        return {
            'leave_type_unpaid_ids': [
                (6, 0, safe_eval(leave_type_unpaid_ids))]
        }

    @api.one
    def set_default_leave_type_unpaid_ids(self):
        param_obj = self.env['ir.config_parameter']
        param_obj.set_param(
            'leave_type_unpaid_ids',
            self.leave_type_unpaid_ids.ids or []
        )
