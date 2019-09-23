# -*- coding: utf-8 -*-
##############################################################################

from datetime import datetime

from openerp import tools
from openerp.addons.mail.mail_mail import _logger
from openerp.osv import osv


class mail_mail(osv.osv):

    _inherit = "mail.mail"

    def send_get_mail_to(self, cr, uid, mail, partner=None, context=None):
        """Trobz: Config send mail when is_production_instance is False
        """
        ir_config_para_obj = self.pool['ir.config_parameter']
        # Get is_production_instance
        is_production_instance = tools.config.get(
            'is_production_instance', False)

        # Get default_email
        default_email = ir_config_para_obj.get_param(
            cr, uid, 'default_email', default='poweremail.test@trobz.com',
            context=context)

        email_to = super(mail_mail, self).send_get_mail_to(cr, uid, mail,
                                                           partner=partner,
                                                           context=context)

        if not is_production_instance:
            _logger.warning(
                'Changing the email_to from %s to %s', email_to, default_email)
            email_to = [default_email]
        return email_to

    def send_get_mail_body(self, cr, uid, mail, partner=None, context=None):
        """
        ."""
        body = super(mail_mail, self).send_get_mail_body(
            cr, uid, mail, partner=partner, context=context)
        # Get is_production_instance
        is_production_instance = tools.config.get(
            'is_production_instance', False)
        if not is_production_instance:
            # Get the original recipients
            original_recipients = super(mail_mail, self).send_get_mail_to(
                cr, uid, mail, partner=partner, context=context)
            body = "<i>Original recipients: %s</i><br/>" % ','.join(
                original_recipients) + body
        return body

    def send_get_mail_subject(self, cr, uid, mail, force=False, partner=None,
                              context=None):
        if context is None:
            context = {}

        subject = super(mail_mail, self).send_get_mail_subject(cr, uid, mail,
                                                               force=force,
                                                               partner=partner,
                                                               context=context)

        # Get is_production_instance
        is_production_instance = tools.config.get(
            'is_production_instance', False)

        if not is_production_instance and not context.get('error_mail', False):

            # Get url
            config_parameter_obj = self.pool['ir.config_parameter']
            config_param_data = config_parameter_obj.get_param(cr, uid,
                                                               'web.base.url')

            if config_param_data:
                add_subject = '(' + config_param_data + ')'
            add_subject = add_subject + ' (' + str(cr.dbname) + ')'

            # get time
            current_time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            # Convert time to user timezone
            current_time = self.pool['trobz.base'].\
                convert_from_utc_to_current_timezone(cr, uid, current_time,
                                                     get_str=True,
                                                     context=context)
            add_subject = add_subject + ' (' + current_time + ')'
            subject = add_subject + subject

        return subject

    def send(self, cr, uid, ids, auto_commit=False, raise_exception=False,
             context=None):
        # Use is_skip_mail = True in dev environment. This will fasten
        # actions which triggers mails
        is_skip_mail = tools.config.get('is_skip_mail', False)

        if is_skip_mail:
            _logger.warn('Email sending skipped; config is_skip_mail = True')
            return True
        else:
            return super(mail_mail, self).send(cr, uid, ids,
                                               auto_commit=auto_commit,
                                               raise_exception=raise_exception,
                                               context=context)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
