from openerp import fields, api, _
from openerp.addons.field_secure import models


class HrAppraisalInput(models.SecureModel):
    _inherit = 'hr.appraisal.input'

    extra_comments = fields.Secure(
        string="Extra Comments", security='_password_security', password=False)

    @api.multi
    def _password_security(self):
        """
        Author can see and edit all secured fields of his appraisal input
        HR manager and Manager of the employee_of_current_user can only see
            all secured fields of all appraisal inputs.
        """
        user_env = self.env['res.users']
        employee_env = self.env['hr.employee']
        employee_obj = employee_env.search([('user_id', '=', self._uid)])
        is_allow = False
        for rec in self:
            manager_id = rec.appraisal_id and\
                rec.appraisal_id.manager_id and\
                rec.appraisal_id.manager_id.id or False
            if user_env.has_group('base.group_hr_manager') or \
                    employee_obj.id == manager_id or \
                    employee_obj.id == rec.author_id.id:
                # Current user is author or employee manager or HR manager
                # can access to all secured fields
                is_allow = True
            else:
                is_allow = False
                break
        return is_allow
