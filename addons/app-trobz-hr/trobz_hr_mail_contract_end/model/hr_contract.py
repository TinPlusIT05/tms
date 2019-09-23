# -*- coding: utf-8 -*-
import datetime
from openerp import models, fields, api
from openerp.exceptions import Warning
from openerp.tools.translate import _
import logging


class hr_contract(models.Model):
    _inherit = "hr.contract"

    no_renewal = fields.Boolean('No Renewal', default=False)

    @api.multi
    def get_email_to_send(self):
        """
        Get list emails of users in group HR officer.
        """
        group = self.env.ref('base.group_hr_user')
        mail_list = ''
        for user in group.users:
            mail_list += user.email and user.email + ', ' or ''
        return mail_list

    @api.multi
    def _get_contract_link(self):
        """
        Build a link to the contract.
        """
        param_obj = self.env['ir.config_parameter']
        base_url = param_obj.get_param('web.base.url', default='')
        # Example link: http://0.0.0.0:8069/?#id=4
        #    &view_type=form&model=hr.contract&action=...
        act_window = self.env.ref('hr_contract.action_hr_contract')
        link = base_url + '/?#id=%s&view_type=form&model=hr.contract&action=%s'\
            % (self.id, act_window.id)
        return link

    @api.model
    def _get_expired_contracts_by_department(self, date):
        """
        Get the contract which will be expired before inputed date
            without the next contract created
            without the No Renewal checkbox set
        """
        self._cr.execute("""
            SELECT con.id, emp.name_related as employee,
            con.name, con.date_end,
            dept.name as department, job.name as job
            FROM hr_contract con
                JOIN hr_employee emp ON con.employee_id = emp.id
                LEFT JOIN hr_department dept ON emp.department_id = dept.id
                LEFT JOIN hr_job job ON con.job_id = job.id
            WHERE con.date_end <= '%s'
                AND con.no_renewal = False
                AND NOT EXISTS(
                    SELECT 1 FROM hr_contract
                    WHERE date_start > con.date_end
                    AND employee_id = con.employee_id
                )
            ORDER BY date_end
           """ % date)
        res = self._cr.dictfetchall()
        expired_contracts_department = {}
        for line in res:
            department = line['department'] or 'Undefined'
            if department not in expired_contracts_department:
                expired_contracts_department[department] = []
            expired_contracts_department[department].append(line)
        return expired_contracts_department

    @api.model
    def send_email_contract_end_next_x_days(self):
        """
        Send email weekly to remind the contracts expired next 30 days
        """
        context = dict(self._context)
        param_obj = self.env['ir.config_parameter']
        days_param = param_obj.get_param('contract_expiring_days', default='30')
        try:
            next_x_date = (datetime.date.today()
                            + datetime.timedelta(int(days_param))).strftime('%Y-%m-%d')
        except Exception as exc:
            logging.error(exc)
            raise Warning(_('Wrong value defined in parameter expiring_days.'))

        email_data = self._get_expired_contracts_by_department(next_x_date)
        if not email_data:
            return True
        context.update({'email_data': email_data})
        template = self.env.ref(
            'trobz_hr_mail_contract_end.email_template_contract_end_next_x_days'
        )
        if not template:
            return True
        template.with_context(context).send_mail(
            email_data.values()[0][0]['id'], True
        )
        return True

    @api.model
    def send_email_contract_end(self):
        """
        Send email daily to remind the contracts expired
        """
        context = dict(self._context)
        date = datetime.date.today().strftime('%Y-%m-%d')

        email_data = self._get_expired_contracts_by_department(date)
        if not email_data:
            return True
        context.update({'email_data': email_data})
        template = self.env.ref(
            'trobz_hr_mail_contract_end.email_template_contract_end'
        )
        if not template:
            return True
        first_contract_id = email_data.values()[0][0]['id']
        template.with_context(context).send_mail(
            first_contract_id, True
        )
        return True

    @api.multi
    def get_email_information(self):
        """
        Get content of renewal contracts email
        """
        email_data = self._context.get('email_data', False)
        department = email_data.keys()
        str_email_info = ''
        for department in email_data:
            str_email_info += """<p style="padding-top: 10px; padding-left: 20px;"> <b>Department %s</b>
            """ % department
            str_email_info += '<ul>'
            for contract in email_data[department]:
                link = self._get_contract_link()
                str_email_info += '<li>%s - <a href=\"%s\">%s</a> - %s</li>'\
                    % (contract['date_end'], link,
                       contract['name'], contract['job'] or 'Undefined Job')
            str_email_info += '</p>'

            str_email_info += '</ul>'
        return str_email_info

    @api.model
    def get_contract_expiring_days(self):
        """
        """
        param_obj = self.env['ir.config_parameter']
        return param_obj.get_param('contract_expiring_days', default='30')

hr_contract()
