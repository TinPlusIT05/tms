# -*- encoding: UTF-8 -*-
from openerp import api, fields, models
from openerp.exceptions import Warning
from openerp.tools.translate import _


class ir_attachment(models.Model):

    _inherit = "ir.attachment"

    @api.model
    def create(self, vals):
        context = self._context and self._context.copy() or {}
        comment_env = self.env["tms.ticket.comment"]
        comment_vals = {}

        # F#10457: Set res_model = 'hr.applicant' if user creates a Resume
        if context.get('model_hr_applicant', False):
            vals['res_model'] = 'hr.applicant'

        # Get file details from vals
        attach_file_name = vals.get("name")
        res_model_name = vals.get("res_model")
        res_model_id = vals.get("res_id")

        # Process file name to include ISO Date at
        # the end (with server date format) and also check file existence
        file_upload_check = self.is_file_exist(
            attach_file_name, res_model_name, res_model_id)
        _is_file_exist, _check_message, vals["name"] = file_upload_check

        # Just a flag to check
        attachment_for_ticket = res_model_name in (
            "tms.support.ticket", "tms.forge.ticket")

        # Log comment if attachment is created for Support Ticket or
        # Forge Ticket
        attachment_notify = False
        if attachment_for_ticket:
            # Raise warning if file is exist
            if _is_file_exist:
                raise Warning(
                    _("Warning!"),
                    _("{0} is already exist".format(attach_file_name)))

            # Prepare change log message
            template_msg = "ATTACHMENT {name} IS ADDED".format(
                name=vals["name"])

            # Changelog comment is created for support ticket
            if res_model_name == "tms.support.ticket":
                comment_vals["tms_support_ticket_id"] = res_model_id
                attachment_notify = True

            # Changelog comment is created for forge ticket
            elif res_model_name == "tms.forge.ticket":
                comment_vals["tms_forge_ticket_id"] = res_model_id

            # Update comment details, log comment as changelog
            comment_vals.update({
                "comment": template_msg, "type": "attachment",
                'author_id': self._uid
            })
            context.update({'field_change': comment_vals.keys()})

        # Create attachment
        result = super(ir_attachment, self).create(vals)

        # Create change log comment
        attachment_for_ticket and comment_env.create(comment_vals)

        if attachment_notify:
            self.with_context(
                context).sending_email_notification_for_attachment(
                res_model_id)

        # Check add attachment to second approval leave requests
        if res_model_name == "hr.holidays":
            result.check_update_double_validation_leave_request(res_model_id)

        return result

    @api.multi
    def check_update_double_validation_leave_request(self, res_model_id):
        for record in self:
            hr_holiday_env = record.env["hr.holidays"]
            holiday = hr_holiday_env.browse(res_model_id) or False
            if holiday:
                holiday.write({'remider_add_attachment': False})

    @api.multi
    def unlink(self):
        context = self._context and self._context.copy() or {}
        comment_env = self.env["tms.ticket.comment"]
        # Log removal message for attachments
        for attachment in self:
            attachment_notify = False
            # Prepare change log message
            change_log = "ATTACHMENT {name} IS REMOVED".format(
                name=attachment.name)
            comment_vals = {
                "comment": change_log,
                "type": "attachment"
            }

            # Just a flag to check
            remove_attachment_from_ticket = attachment.res_model in (
                "tms.support.ticket",
                "tms.forge.ticket"
            )

            # Remove attachment for support ticket or
            # forge ticket should have changelog
            if remove_attachment_from_ticket:
                if attachment.res_model == "tms.support.ticket":
                    comment_vals["tms_support_ticket_id"] = attachment.res_id
                    attachment_notify = True
                elif attachment.res_model == "tms.forge.ticket":
                    comment_vals["tms_forge_ticket_id"] = attachment.res_id

            context.update({'field_change': comment_vals.keys()})
            # Create change log comment
            remove_attachment_from_ticket and comment_env.create(comment_vals)
            if attachment_notify:
                attachment.with_context(
                    context).sending_email_notification_for_attachment(
                    attachment.res_id)

        return super(ir_attachment, self).unlink()

    @api.model
    def is_file_exist(self, _file_name, _res_model, _res_id):
        """
            @param {string} _file_name: uploaded file name(only file name
            with extension).
            @param {string} _res_model: the model resource which is needed
            to attach file.
            @param {int} _res_id: the record id on the resource model
            to attach file.
            @note: Check if a specific file name is already created
            for a specific model with id or not.
                    can be called from client side with javascript
            @return: {list}: [boolean, string, string]
                1./ {boolean}: indicates the uploaded file is exist or not
                2./ {string}: error message or success message
                to allow attachment to be uploaded
                3./ {string}: new file name (if successfully uploaded)
        """
        sep_index = _file_name.rfind(".")
        file_name = _file_name[:sep_index]
        file_extension = _file_name[sep_index + 1:]
        context_today = fields.Date.context_today(self)
        store_file_name = u"{0} ({1}).{2}".format(
            file_name, context_today, file_extension)

        # Make sure this file has not been attached before
        attachment_domain = [('res_id', '=', _res_id),
                             ('res_model', '=', _res_model),
                             '|',
                             ('name', '=', _file_name),
                             ('name', '=', store_file_name)]
        attachments = self.search(attachment_domain)
        if attachments:
            return True, "File name is already exist...", store_file_name
        return False, "File name is not exist...", store_file_name

    @api.model
    def sending_email_notification_for_attachment(self, res_model_id):
        template = self.env.ref(
            'tms_modules.tms_support_notification_email_html_template')
        template._send_mail_asynchronous(res_model_id)
