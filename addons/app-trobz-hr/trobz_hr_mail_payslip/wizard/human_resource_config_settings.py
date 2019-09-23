# -*- coding: utf-8 -*-

from openerp import models, fields, api


class human_resource_config_settings(models.TransientModel):
    _inherit = 'hr.config.settings'

    send_email_refund_payslip = fields.Boolean(
        'Send email for refunded payslip',
        help='If this checkbox is not set, \
        do not send emails when refunding a payslip.'
    )

    @api.model
    def get_default_dp(self, fields):
        param_obj = self.env['ir.config_parameter']
        param_send_email_refund_payslip = param_obj.get_param(
            'param_send_email_refund_payslip'
        )
        send_email_refund_payslip = False
        if param_send_email_refund_payslip != 'False':
            send_email_refund_payslip = True
        return {
            'send_email_refund_payslip': send_email_refund_payslip
        }

    @api.one
    def set_default_dp(self):
        param_obj = self.env['ir.config_parameter']
        param_obj.set_param(
            'param_send_email_refund_payslip',
            str(self.send_email_refund_payslip)
        )
