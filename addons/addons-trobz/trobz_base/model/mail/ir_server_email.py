# -*- coding: utf-8 -*-

import logging

from openerp.osv import osv
from openerp import tools


class ir_mail_server(osv.Model):

    _inherit = 'ir.mail_server'

    def build_email(self, email_from, email_to, subject, body, email_cc=None,
                    email_bcc=None, reply_to=False, attachments=None,
                    message_id=None, references=None, object_id=False,
                    subtype='plain', headers=None, body_alternative=None,
                    subtype_alternative='plain'):

        is_production_instance = tools.config.get('is_production_instance',
                                                  False)
        if not is_production_instance:
            logging.warning('Removing email_cc %s', email_cc)
            logging.warning('Removing email_bcc %s', email_bcc)

            email_cc = None
            email_bcc = None

        msg = super(ir_mail_server, self).build_email(
            email_from,
            email_to,
            subject,
            body,
            email_cc=email_cc,
            email_bcc=email_bcc,
            reply_to=reply_to,
            attachments=attachments,
            message_id=message_id,
            references=references,
            object_id=object_id,
            subtype=subtype,
            headers=headers,
            body_alternative=body_alternative,
            subtype_alternative=subtype_alternative)

        return msg

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
