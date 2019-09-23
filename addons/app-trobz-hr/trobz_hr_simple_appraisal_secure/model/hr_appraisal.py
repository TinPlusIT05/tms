from openerp import fields, api, _
from openerp.addons.field_secure import models
from openerp.exceptions import Warning


class HrAppraisal(models.SecureModel):

    _inherit = "hr.appraisal"

    interview_result = fields.Secure(
        string="Interview result",
        security='_password_security_interview_result', password=False)
    salary_information = fields.Secure(
        string="Salary information",
        security='_password_security_salary',
        help="For the Manager to record employees expectations")

    @api.multi
    def _password_security_salary(self):
        """
        HR manager and the Manager of the employee can see and edit
            Salary Information
        """
        employee_env = self.env['hr.employee']
        user_env = self.env['res.users']
        employee_obj = employee_env.search([('user_id', '=', self._uid)])
        is_allow = False
        for rec in self:
            if user_env.has_group('base.group_hr_manager') or \
                    employee_obj.id == rec.manager_id.id:
                is_allow = True
            else:
                is_allow = False
                break
        return is_allow

    @api.multi
    def _password_security_interview_result(self):
        """
        Interview Result
        - HR manager and the Manager of the employee can see and edit
        - Employee can see
        """

        employee_env = self.env['hr.employee']
        user_env = self.env['res.users']
        employee_obj = employee_env.search([('user_id', '=', self._uid)])
        is_allow = False
        for rec in self:
            if user_env.has_group('base.group_hr_manager') or \
                    employee_obj.id == rec.manager_id.id or \
                    employee_obj.id == rec.employee_id.id:
                is_allow = True
            else:
                is_allow = False
                break
        return is_allow

    @api.multi
    def write(self, vals):
        """
        Security: Only HR manager and Employee Manager can edit appraisal
        Chatter: Change message (NOT show encrypted string)
        """
        if vals and not self._password_security_salary():
            # interview_result without password confirmation
            # So Check here to avoid employee edit this field.
            raise Warning(
                _("Only HR manager and manager of employee "
                  "can update this appraisal"))
        if 'interview_result' in vals:
            self.message_post(
                body=_('The interview result has been update'))
        if 'salary_information' in vals:
            self.message_post(
                body=_('The salary information has been update'))
        return super(HrAppraisal, self).write(vals)
