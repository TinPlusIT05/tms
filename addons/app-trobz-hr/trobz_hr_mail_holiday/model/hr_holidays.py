# -*- coding: utf-8 -*-
from openerp import api, models
import logging


class hr_holidays(models.Model):
    _inherit = "hr.holidays"

    @api.multi
    def get_request_link(self):
        """
        Get url of given request
        """
        param_obj = self.env['ir.config_parameter']
        base_url = param_obj.get_param('web.base.url')
        # Example link: http://0.0.0.0:8069/web?db=database_name#id=4
        #    &view_type=form&model=hr.holidays&action=...
        act_window = self.env.ref('hr_holidays.open_ask_holidays')
        link = base_url + '/web?db=%s#id=%s&view_type=form&model=hr.holidays&action=%s'\
            % (self._cr.dbname, self.id, act_window.id)
        return link

    @api.multi
    def holidays_confirm(self):
        """
        Send email to the manager when the leave request
            need to be approved
        """
        for holiday in self:
            if holiday.type == 'remove':
                template = self.env.ref(
                    'trobz_hr_mail_holiday.email_template_holiday_confirm'
                )
                if template:
                    logging.info("=== holidays_confirm ====")
                    logging.info(
                        "START send email to %s"
                        % holiday.employee_id.parent_id.work_email
                    )
                    template.send_mail(holiday.id)
                    logging.info(
                        "END send email to %s"
                        % (holiday.employee_id.parent_id.work_email)
                    )
        return super(hr_holidays, self).holidays_confirm()

    @api.multi
    def holidays_validate(self):
        """
        Send email to the employee when the manager approve the leave request
        on the first time
        """
        for holiday in self:
            if holiday.type == 'remove':
                template = self.env.ref(
                    'trobz_hr_mail_holiday.email_template_holiday_approval'
                )
                if template:
                    logging.info("=== holidays_validate ====")
                    logging.info(
                        "START send email to %s"
                        % holiday.employee_id.work_email
                    )
                    template.send_mail(holiday.id)
                    logging.info(
                        "END send email to %s"
                        % holiday.employee_id.work_email
                    )
        return super(hr_holidays, self).holidays_validate()

    @api.multi
    def holidays_refuse(self):
        """
        Send email to the employee when the manager refused the leave request
        """
        for holiday in self:
            if holiday.type == 'remove':
                template = self.env.ref(
                    'trobz_hr_mail_holiday.email_template_holiday_denial'
                )
                if template:
                    logging.info("=== holidays_refuse ====")
                    logging.info(
                        "START send email to %s, %s"
                        % (holiday.employee_id.parent_id.work_email,
                           holiday.employee_id.work_email)
                    )
                    template.send_mail(holiday.id)
                    logging.info(
                        "END send email to %s, %s"
                        % (holiday.employee_id.parent_id.work_email,
                           holiday.employee_id.work_email)
                    )
        return super(hr_holidays, self).holidays_refuse()

    @api.multi
    def change_state_to_cancel(self):
        """
        Send email to manager when the leave request is cancel
        Change state to "Cancel"
        """
        for holiday in self:
            if holiday.type == 'remove':
                template = self.env.ref(
                    'trobz_hr_mail_holiday.email_template_holiday_cancel'
                )
                if template:
                    logging.info("=== change_state_to_cancel ====")
                    logging.info(
                        "START send email to %s"
                        % holiday.employee_id.parent_id.work_email
                    )
                    template.send_mail(holiday.id)
                    logging.info(
                        "END send email to %s"
                        % holiday.employee_id.parent_id.work_email
                    )
        return super(hr_holidays, self).change_state_to_cancel()

    @api.multi
    def get_current_balance_of_causual_leave(self):
        """
        Get the current balance of the casual leave
            to show on the reminder email
        """
        current_leave_days = 0.0
        employee_id = False
        line_obj = self.env['hr.holidays.line']
        status_obj = self.env['hr.holidays.status']
        casual_leave_paid_param = self.env.ref(
            'trobz_hr_holiday.default_casual_leave_paid'
        )
        leave_type = status_obj.search(
            [('name', '=', casual_leave_paid_param.value)],
        )
        for holiday in self:
            employee_id = holiday.employee_id.id
            if holiday.state != 'validate':
                current_leave_days = sum(
                    [x.number_of_days for x in holiday.holiday_line
                     if x.holiday_status_id.id == leave_type.id]
                )
        # Get number of allocation days with the same holiday_status_id
        # which was approved.
        allo_requests = self.search(
            [('holiday_status_id', '=', leave_type.id),
             ('employee_id', '=', employee_id),
             ('type', '=', 'add'),
             ('state', '=', 'validate')]
        )
        allo_days = 0.0
        for holiday in allo_requests:
            allo_days += holiday.number_of_days
        # Get the number of leave day with the same holiday_status_id
        # which was approved.
        approved_lines = line_obj.search(
            [('holiday_status_id', '=', leave_type.id),
             ('holiday_id.employee_id', '=', employee_id),
             ('holiday_id.state', '=', 'validate'),
             ('holiday_id.type', '=', 'remove')],
        )
        leave_days = 0.0
        for line in approved_lines:
            leave_days += line.number_of_days
        return allo_days - leave_days - current_leave_days

    @api.multi
    def get_email_content(self):
        """
        Get leave request information
        """
        info_string = '<div>Details:<div><ul>'
        for holiday in self:
            info_string += "<li>Request's owner: %s </li>" \
                           % holiday.employee_id.name
            info_string += "<li>Description: %s </li>" % holiday.name
            info_string += "<li>Full Description: %s </li>" \
                            % holiday.full_description
            info_string += "<li>Total Duration: %s day(s) </li>" \
                           % holiday.number_of_days_temp
            info_string += "<li>Balance of Casual Leaves (paid)*:\
                            %s day(s)</li>" \
                           % self.get_current_balance_of_causual_leave()
            info_string += "<li>*Current balance of the casual leaves taking\
                            into account this request.</li>"
            count_holiday_line = 0
            for holiday_line in holiday.holiday_line:
                count_holiday_line += 1
                first_date = holiday_line.first_date
                last_date = holiday_line.last_date
                first_date_type = dict(holiday_line.fields_get(
                    allfields=['first_date_type'])
                    ['first_date_type']['selection'])[holiday_line.first_date_type]
                last_date_type = dict(holiday_line.fields_get(
                    allfields=['last_date_type'])
                    ['last_date_type']['selection'])[holiday_line.last_date_type]
                number_of_days = holiday_line.number_of_days
                reason = holiday_line.holiday_status_id.name
                info_string += '<li>Leave Request Line %s</li>'\
                               % count_holiday_line
                info_string += '<ul><li>Leave Type: %s</li>' \
                               % reason
                info_string += '<li>From %s to %s </li>' \
                               % (first_date, last_date)
                info_string += '<li>First Day Type: %s </li>' \
                               % (first_date_type)
                info_string += '<li>Last Day Type: %s </li>' \
                               % (last_date_type)
                info_string += "<li>Duration: %s day(s)</li></ul>" \
                               % number_of_days
        info_string += '</ul>'
        return info_string

    @api.multi
    def get_reminding_email_content(self):
        """
        Get the email content of reminding email
        """
        holidays = self._context.get('holidays', [])
        info_string = '<ul>'
        for holiday in holidays:
            link = holiday.get_request_link()
            info_string += "<li><a href=\"%s\"> \
                Leave Request of %s</a> - %s day(s)</li>" \
                % (link, holiday.employee_id.name,
                   holiday.number_of_days_temp)
            count_holiday_line = 0
            for holiday_line in holiday.holiday_line:
                count_holiday_line += 1
                first_date = holiday_line.first_date
                last_date = holiday_line.last_date
                first_date_type = dict(holiday_line.fields_get(
                    allfields=['first_date_type'])
                    ['first_date_type']['selection'])[holiday_line.first_date_type]
                last_date_type = dict(holiday_line.fields_get(
                    allfields=['last_date_type'])
                    ['last_date_type']['selection'])[holiday_line.last_date_type]
                number_of_days = holiday_line.number_of_days
                reason = holiday_line.holiday_status_id.name
                info_string += '<ul><li>Leave Request Line %s</li>'\
                               % count_holiday_line
                info_string += '<ul><li>Leave Type: %s</li>' \
                               % reason
                info_string += '<li>From %s to %s </li>' \
                               % (first_date, last_date)
                info_string += '<li>First Day Type: %s </li>' \
                               % (first_date_type)
                info_string += '<li>Last Day Type: %s </li>' \
                               % (last_date_type)
                info_string += "<li>Duration: %s day(s)</li></ul></ul>" \
                               % number_of_days
        info_string += '</ul>'
        return info_string

    @api.model
    def automatic_send_reminder_email_to_manager(self):
        """
        Send email to manager to remind
            the leave request not approved yet
        """
        self._cr.execute("""
            -- get confirmed leave requests
            -- managers of employee on leave request have work-email
            SELECT id
            FROM hr_holidays
            WHERE type = 'remove'
                AND state = 'confirm'
                AND employee_id IN (
                    SELECT b.id
                    FROM hr_employee a, hr_employee b
                    WHERE b.parent_id = a.id
                        AND a.work_email IS NOT NULL)
            ORDER BY employee_id""")
        res = self._cr.fetchall()
        confirmed_holiday_ids = [x[0] for x in res]
        if confirmed_holiday_ids:
            # Confirmed leaves which start date is tomorrow
            # group by manager_id
            email_data = {}
            confirmed_holidays = self.browse(confirmed_holiday_ids)
            for confirmed_holiday in confirmed_holidays:
                if confirmed_holiday.employee_id.parent_id:
                    manager_id = confirmed_holiday.employee_id.parent_id.id
                    if manager_id not in email_data:
                        email_data.update({
                            manager_id: [confirmed_holiday]})
                    else:
                        email_data[manager_id].append(confirmed_holiday)

            # Get leave requests into email_data group by manager
            # Send email reminder to each manager
            for manager_id in email_data.keys():
                holidays = email_data[manager_id]
                logging.info(
                    'Holiday reminder email > holidays: %s'
                    % str(holidays))
                if holidays:
                    context = dict(self._context)
                    context.update({'holidays': holidays})
                    template = self.env.ref(
                        'trobz_hr_mail_holiday.email_template_remind_manager'
                    )
                    if template:
                        logging.info("START Send holiday reminder email")
                        template.with_context(context).send_mail(
                            holidays[0].id
                        )
                        logging.info("END Send holiday reminder email")
        return True


hr_holidays()
