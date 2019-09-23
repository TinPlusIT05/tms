# -*- encoding: utf-8 -*-
from datetime import datetime
import logging
import threading

from openerp import models, api, _
import openerp
from openerp.addons.email_template import email_template  # @UnresolvedImport
from openerp.exceptions import Warning


# Import Utility Libraries
# Import logging, get logging for the current module name
_logger = logging.getLogger("email.template")

# TODO: Do not escapse HTML string generated from object's functions
email_template.mako_template_env.autoescape = False


class email_template(models.Model):
    _inherit = "email.template"

    # Compose send email function that is used in asynchronous mode
    @api.model
    def _send(self, res_id):
        msg_name = "TMS Email For::: {0}".format(self.name)
        # the send mail will not work without this
        with openerp.api.Environment.manage():
            # get new cursor by reconnecting, use Super User uid = 1
            db = openerp.sql_db.db_connect(self._cr.dbname)
            local_cr = db.cursor()
            context = self._context and self._context.copy() or {}
            new_env = api.Environment(local_cr, 1, context)

            try:
                self.with_env(new_env).send_mail(
                    res_id,
                    force_send=True
                )
                local_cr.commit()
                local_cr.close()

                # Log message for easy on tracking later
                _logger.warn(msg_name)

            except Exception:
                local_cr.rollback()
                failed_msg = "TMS Email Failed To Send:: ".\
                    format(self.name)
                _logger.error(failed_msg, exc_info=True)

            return

    # TODO: Investigate if this method is necessary. Maybe it is legacy and
    # can be ignored using the argument force_send=False in send_mail with
    # a scheduler running every minute or so...
    @api.model
    def _send_mail_asynchronous(
            self, res_id, asynchronous=True):
        """
            This method allows user to send email in TMS with both
            asynchronous / synchronous mode, using asynchronous mode is
            recommended because email will be handled in different thread
            and the main thread will be free to handle business tasks.

            @param {int} res_id: id of the record to render the template with
                              (model is taken from the template)

            @param {bool} asynchronous: indicates if email
                should be sent asynchronously, default is True.

            @note: This method triggers email send signal using admin
            credential (SUPERUSER_ID) to bypass permission check in ORM system,
            the reason is allowing users to send email without worrying
            anything about the access rights related to
            'mail' and 'email_template' modules.

            Therefore inside methods called by the email template, the 'uid'
            is now turned to be admin user id (SUPERUSER_ID) so if you want to
            get the real user id who is triggering this 'send_email' method,
            you have to get it from the 'context' by the following code:
                uid = context.get("uid")
            And to make sure this method works correctly,
            do not dismiss the 'context'
        """
        # Start sending email asynchronously / synchronously
        if asynchronous:
            self._cr.commit()  # commit previous session
            threading.Thread(
                target=self._send(res_id),
                name='TMS >>_send_mail_asynchronous').start()
        else:
            self.send_mail(res_id, force_send=True)

        return True

    # TODO: find a better model to store the below parameters and functions

    KEY_FIGURE_RED_DIV_START = '<div style="font-size:18px;' +\
        'color:red;margin-top:15px;font-weight:bold;">'
    KEY_FIGURE_GREEN_DIV_START = '<div style="font-size:18px;' +\
        'color:green;margin-top:15px;font-weight:bold;">'
    KEY_FIGURE_BLACK_DIV_START = '<div style="font-size:18px;' +\
        'color:black;margin-top:15px;font-weight:bold;">'
    KEY_FIGURE_ORANGE = '<h4><div style="font-size:18px;' +\
        'color:orange;font-family:Arial" >%s</div></h4>'
    KEY_FIGURE_MESSAGE = '<div style="font-size:11px;font-style:italic;' +\
        'margin-left:30px" title="%s">%s</div>'
    KEY_FIGURE_TARGET = '<span style="font-size:14px;' +\
        'color:black;"><b>%s<b></span></div>'

    @api.model
    def send_daily_notifications_mail(self):
        """
            This method allow to send daily notification in TMS
        """
        template = self.env.ref(
            'tms_modules.daily_notifications_email'
        )
        return template._send_mail_asynchronous(template.id)

    @api.model
    def send_hr_daily_notification_mail(self):
        """
            This method allow to send hr daily notifications
        """
        template = self.env.ref(
            'tms_modules.hr_daily_notifications'
        )
        return template._send_mail_asynchronous(template.id)

    @api.model
    def send_daily_support_consumption_status_to_pm(self):
        """
            This method allow to send daily notification in TMS to PM
            every morning of the week day at 7am
        """
        template = self.env.ref(
            'tms_modules.daily_support_consumption_status'
        )
        if datetime.now().weekday() not in (5, 6):
            """
                where Monday is 0 and Sunday is 6.
            """
            return template._send_mail_asynchronous(template.id)
        return False

    @api.model
    def get_daily_notification_receiver_emails(self):
        """
            If current user is admin, send daily notification to all people in
            "staff@lists.trobz.com" configured in ir.config_parameter,
            otherwise send email to the current user who clicks on the button.
        """
        context = self._context and self._context or {}

        # Get real user id through the context instead
        # of default 'uid' parameter, it's now overrided by
        # email_template's 'send_mail' function call as
        # SUPERUSER_ID to bypass ORM permission check
        cuid = context.get("uid", self._uid)

        # Get object pool references
        if cuid == 1:
            config_pool = self.env['ir.config_parameter']
            # default receiver email to be sent
            config_key = "default_daily_notification_receiver_email"
            receiver = config_pool.get_param(config_key,
                                             "staff@lists.trobz.com")
        # in case user clicks on the button is not admin, override 'receiver'
        else:
            user_data = self.env["res.users"].browse(cuid)
            if not user_data.email:
                raise Warning(
                    _('Error'),
                    _('You need to define your email address!'))
            receiver = user_data.email

        # Just for logging
        _logger.warn(_("Email is being sent to:: '{0}'".format(receiver)))
        return receiver

    @api.model
    def get_target_value(self, target_name):
        target_current_time = datetime.today()
        target_type_ids = self.env['target.type'].\
            search([('name', '=', target_name)])
        value = 0
        if target_type_ids and target_type_ids.ids:
            target_ids = self.env['target'].\
                search([('target_type_id', '=',
                         target_type_ids.ids[0]),
                        ('start_day', '<=', target_current_time),
                        '|', ('end_day', '>=', target_current_time),
                        ('end_day', '=', False)])
            if not target_ids or len(target_ids) > 1:
                value = 0
            else:
                value = target_ids[0].value
        return value

    @api.model
    def get_target_description(self, name):
        target_type = self.env['target.type']
        target_types = target_type.search([('name', '=', name)])
        if target_types:
            return target_types[0].description or \
                'This target is currently has no description'
        return 'There is no target defined'

    def render_colored_key_figure(self, test, numb):
        if test:
            return self.KEY_FIGURE_GREEN_DIV_START + str(numb)
        else:
            return self.KEY_FIGURE_RED_DIV_START + str(numb)

    def render_default_colored_key_figure(self, numb):
        return self.KEY_FIGURE_BLACK_DIV_START + str(numb)

    @api.model
    def send_weekly_developer_productivity(self, sprint_date=None):
        """
            This method allow to send daily notification in TMS
        """
        template = self.env.ref(
            'tms_modules.email_weekly_developer_productivity'
        )
        ctx = dict(self._context or {})
        if sprint_date:
            ctx.update({'sprint_date': sprint_date})
        return template.with_context(ctx)._send_mail_asynchronous(template.id)

    @api.model
    def get_weekly_developer_productivitys(self):
        return self.get_daily_notification_receiver_emails()
