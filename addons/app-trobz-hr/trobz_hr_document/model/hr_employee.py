# -*- encoding: utf-8 -*-
from openerp import fields, models, api
from datetime import datetime
from openerp.addons.email_template import email_template

email_template.mako_template_env.autoescape = False


class hr_employee(models.Model):
    _inherit = "hr.employee"

    # Columns
    documents_count = fields.Integer(
        string='Documents', compute="_documents_count"
    )

    @api.one
    def _documents_count(self):
        document = self.env['hr.document']
        self.documents_count = document.search_count(
            [('emp_id', '=', self.id)]
        )

    @api.model
    def get_email_to(self):
        group_obj = self.env['res.groups']
        hr_manager_group_records = group_obj.search(
            [('full_name', '=', 'Human Resources / Manager')]
        )
        res = [user.email for user in hr_manager_group_records.users
               if user.email]
        return ";".join(res)

    @api.model
    def get_doc_url(self, doc_id):
        param_obj = self.env['ir.config_parameter']
        web_base_url = param_obj.get_param('web.base.url', False)
        url = web_base_url + \
            "web?#id=%s&view_type=form&model=hr.document&active_id=1" \
            % (doc_id)
        return url

    def format_date(self, string_date):
        return datetime.strptime(string_date, "%Y-%m-%d").strftime("%d/%m/%Y")

    @api.model
    def get_dict_emp_doc(self, for_expired):
        document_env = self.env['hr.document']
        doc_records = for_expired and document_env.get_doc_expired() \
            or document_env.get_doc_expiring_30_days()
        dict_emp_doc = {}
        for doc_record in doc_records:
            emp_name = doc_record.emp_id and doc_record.emp_id.name or False
            if emp_name:
                if emp_name in dict_emp_doc:
                    dict_emp_doc[emp_name].append(
                        "<a href='%s'>%s %s - %s</a><br/>"
                        % (self.get_doc_url(doc_record.id),
                           doc_record.type_id.name,
                           doc_record.name,
                           self.format_date(doc_record.expiry_date))
                    )
                else:
                    dict_emp_doc.update({
                        emp_name: ["<a href='%s'>%s %s - %s</a><br/>"
                                   % (self.get_doc_url(doc_record.id),
                                      doc_record.type_id.name,
                                      doc_record.name,
                                      self.format_date(doc_record.expiry_date))
                                   ]
                    })
        return dict_emp_doc

    def convert_dict_emp_doc(self, dict_emp_doc):
        res = ""
        for emp_name in dict_emp_doc.keys():
            res += "<ul><li>%s:</li>" % (emp_name)
            res += "<ul>"
            for doc_info in dict_emp_doc[emp_name]:
                res += '<li style="margin-top:5px;">' + doc_info + '</li>'
            res += "</ul></ul>"
        return res

    @api.model
    def get_email_content(self, for_expired):
        res = """
        <p>Hello Managers !</p>
        <p>Below is the list of %s documents %s:</p>
        <p>%s</p>
        Regards,
        """ % (for_expired and 'expired' or 'expiring',
               not for_expired and 'in 30 days' or '',
               self.convert_dict_emp_doc(self.get_dict_emp_doc(for_expired))
               )
        return res

    @api.model
    def send_email(self, emp_id, template_xml_id):
        if template_xml_id:
            email_template = self.env.ref(
                'trobz_hr_document.%s' % (template_xml_id)
            )
            if email_template:
                email_template.send_mail(
                    emp_id, force_send=True, raise_exception=True
                )
        return True

    @api.model
    def run_send_email_cron(self):
        param_obj = self.env['ir.config_parameter']
        emp_records = self.search([])
        reminder_doc_expiring_in_30_days = eval(
            param_obj.get_param('reminder_doc_expiring_in_30_days', 'False')
        )
        reminder_doc_expired = eval(param_obj.get_param(
            'reminder_doc_expired', 'False'
        ))
        document_env = self.env['hr.document']
        if emp_records:
            if reminder_doc_expiring_in_30_days:
                doc_records = document_env.get_doc_expiring_30_days()
                if doc_records:
                    self.send_email(
                        emp_records.ids[0],
                        'email_template_hr_document_expiring_30_days'
                    )
            if reminder_doc_expired:
                doc_records = document_env.get_doc_expired()
                if doc_records:
                    self.send_email(
                        emp_records.ids[
                            0], 'email_template_hr_document_expired'
                    )
        return True
