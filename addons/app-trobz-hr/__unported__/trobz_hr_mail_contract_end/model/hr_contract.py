# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime, date, timedelta


class hr_contract(osv.osv):
    _inherit = "hr.contract"

    _columns = {
        'no_renewal': fields.boolean('No Renewal'),
    }

    _defaults = {
        'no_renewal': False,
    }

    def get_email_to_send(self, cr, uid, ids, context=None):
        """
        Get list email of users in group HR officer
        """
        model_obj = self.pool.get('ir.model.data')
        group = model_obj.get_object(
            cr, uid, 'base', 'group_hr_user'
        )
        mail_list = ''
        for user in group.users:
            mail_list += user.email and user.email + ', ' or ''
        return mail_list

    def _get_contract_link(self, cr, uid, contract_id, context=None):
        """
        """
        param_obj = self.pool.get('ir.config_parameter')
        base_url = param_obj.get_param(cr, uid, 'web.base.url', default='',
                                       context=context)
        # Example link: http://0.0.0.0:8069/?db=database_name&#id=4
        #    &view_type=form&model=hr.contract&action=...
        act_window = self.pool.get('ir.actions.act_window').for_xml_id(
            cr, uid, 'hr_contract', 'action_hr_contract'
        )
        link = base_url + '/?db=%s&#id=%s&view_type=form&model=hr.contract&action=%s'\
            % (cr.dbname, contract_id, act_window.get("id"))
        return link

    def _get_expired_contracts_by_department(self, cr, uid, expiring_date):
        """
        Get the contract which will be expired
            before inputed date or from current_date to inputed date
            without the next contract created
            without the No Renewal checkbox set
        """
        today = date.today().strftime(DF)
        condition = ''
        if expiring_date > today:
            condition = "AND (con.date_end <= '%s' AND con.date_end > '%s')" \
                % (expiring_date, today)
        else:
            condition = "AND con.date_end <= '%s'" % (expiring_date)
        sql = """
            SELECT con.id, emp.name_related as employee,
            con.name, con.date_end,
            dept.name as department, job.name as job
            FROM hr_contract con
                JOIN hr_employee emp ON con.employee_id = emp.id
                LEFT JOIN hr_department dept ON emp.department_id = dept.id
                LEFT JOIN hr_job job ON con.job_id = job.id
            WHERE con.no_renewal = False
                AND NOT EXISTS(
                    SELECT 1 FROM hr_contract
                    WHERE
                    (date_start > con.date_end
                    OR date_end IS NULL)
                    AND employee_id = con.employee_id
                )
                %s
            ORDER BY date_end
           """ % condition
        cr.execute(sql)
        res = cr.dictfetchall()
        expired_contracts_department = {}
        for line in res:
            department = line['department']
            if department not in expired_contracts_department:
                expired_contracts_department[department] = []
            expired_contracts_department[department].append(line)
        return expired_contracts_department

    def send_email_contract_end_next_30_days(self, cr, uid, context=None):
        """
        Send email weekly to remind the contracts expired next 30 days
        """
        if context is None:
            context = {}

        model_obj = self.pool.get('ir.model.data')
        template_obj = self.pool.get('email.template')
        next_30_date = (date.today()
                        + timedelta(30)).strftime('%Y-%m-%d')

        email_data = self._get_expired_contracts_by_department(
            cr, uid, next_30_date
        )
        if email_data:
            context.update({'email_data': email_data})
            template = model_obj.get_object(
                cr, uid, 'trobz_hr_mail_contract_end',
                'email_template_contract_end_next_30_days'
            )
            if template:
                template_obj.send_mail(
                    cr, uid, template.id, email_data.values()[0][0]['id'],
                    True, context=context
                )
        return True

    def send_email_contract_end(self, cr, uid, context=None):
        """
        Send email daily to remind the contracts expired
        """
        if context is None:
            context = {}

        model_obj = self.pool.get('ir.model.data')
        template_obj = self.pool.get('email.template')
        today = date.today().strftime('%Y-%m-%d')

        email_data = self._get_expired_contracts_by_department(
            cr, uid, today
        )
        if email_data:
            context.update({'email_data': email_data})
            template = model_obj.get_object(
                cr, uid, 'trobz_hr_mail_contract_end',
                'email_template_contract_end'
            )
            if template:
                first_contract_id = email_data.values()[0][0]['id']
                template_obj.send_mail(
                    cr, uid, template.id, first_contract_id,
                    True, context=context
                )
        return True

    def get_email_information(self, cr, uid, ids, context=None):
        """
        Get content of email remind the expired contracts
        """
        if context is None:
            context = {}

        email_data = context.get('email_data', False)
        department = email_data.keys()
        str_email_info = ''
        for department in email_data:
            show_department = department or 'Undefined Department'
            str_email_info += """<p style="padding-top: 10px; padding-left: 20px;"> <b>Department '%s'</b>
            """ % show_department
            str_email_info += '<ul>'
            for contract in email_data[department]:
                link = self._get_contract_link(cr, uid, contract['id'])
                contract_end_date = datetime.strptime(
                    contract['date_end'], DF).strftime('%d/%m/%Y')
                str_email_info += '<li>%s: <a href=\"%s\">%s</a> - %s %s</li>'\
                    % (contract['employee'], link,
                       contract['name'], contract_end_date,
                       contract['job'] and '- ' + contract['job'] or '')
            str_email_info += '</p>'
            str_email_info += '</ul>'
        return str_email_info
