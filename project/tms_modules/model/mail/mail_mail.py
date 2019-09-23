# -*- coding: utf-8 -*-
##############################################################################
from openerp import models, api


class MailMail(models.Model):
    _inherit = "mail.mail"

    @api.cr_uid_context
    def send_get_mail_body(self, cr, uid, mail, partner=None, context=None):
        """Return a specific ir_email body. The main purpose of this method
        is to be inherited to add custom content depending on some module."""
        body = super(MailMail, self).send_get_mail_body(
            cr, uid, mail, partner=partner, context=context)
        # For emails sent by OpenChatter,
        # if the recipient is not an "@trobz.com" email,
        # don't add the footer with links to TMS
        sent_by_str = '<br /><small>Sent by'
        if partner and '@trobz.com' not in partner.email and \
                sent_by_str in body:
            body = body.split(sent_by_str)[0]
        return body
