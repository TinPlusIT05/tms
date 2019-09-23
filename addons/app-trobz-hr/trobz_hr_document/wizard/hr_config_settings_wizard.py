# -*- coding: utf-8 -*-

from openerp import models, fields, api


class hr_config_settings(models.TransientModel):
    _inherit = 'hr.config.settings'

    # Columns
    reminder_doc_expiring_in_30_days = fields.Boolean(
        string='Send weekly reminder to HR Manager \
        for Documents expiring in 30 days'
    )
    reminder_doc_expired = fields.Boolean(
        string='Send weekly reminder to HR Manager for Documents expired'
    )

    @api.model
    def get_default_dp(self, fields):
        param_obj = self.env['ir.config_parameter']
        reminder_doc_expiring_in_30_days = param_obj.get_param(
            'reminder_doc_expiring_in_30_days', 'False'
        )
        reminder_doc_expired = param_obj.get_param(
            'reminder_doc_expired', 'False'
        )
        return {
            'reminder_doc_expiring_in_30_days':
                eval(reminder_doc_expiring_in_30_days),
            'reminder_doc_expired': eval(reminder_doc_expired),
        }

    @api.one
    def set_default_dp(self):
        param_obj = self.env['ir.config_parameter']
        param_obj.set_param(
            'reminder_doc_expiring_in_30_days',
            self.reminder_doc_expiring_in_30_days or 'False'
        )
        param_obj.set_param(
            'reminder_doc_expired',
            self.reminder_doc_expired or 'False'
        )
