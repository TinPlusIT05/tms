# -*- coding: utf-8 -*-

from openerp import models, api
import logging


class hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def write(self, vals):
        """
        Send email when approving payslip
        only send email for refund payslip
            if send_email_refund_payslip in HR setting is set
        """
        hr_config_obj = self.env['hr.config.settings']
        if vals.get('state', False) == 'verify':
            template = self.env.ref(
                'trobz_hr_mail_payslip.email_template_hr_payslip', False
            )
            if template:
                hr_config = hr_config_obj.get_default_dp(
                    ['send_email_refund_payslip']
                )
                send_email_refund_payslip = hr_config \
                    and hr_config['send_email_refund_payslip'] or False

                for payslip in self:
                    # Do not send email for refund payslip
                    # If send_email_refund_payslip in HR setting is not set
                    credit_note = vals.get('credit_note', payslip.credit_note)
                    if credit_note and not send_email_refund_payslip:
                        continue

                    # Send email when approving payslip
                    logging.info(
                        "START sending email to %s" % payslip.employee_id.name
                    )
                    template.send_mail(
                        payslip.id, force_send=True, raise_exception=True
                    )
                    logging.info(
                        "END sending email to %s" % payslip.employee_id.name
                    )
        return super(hr_payslip, self).write(vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
