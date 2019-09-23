from openerp import fields, api
from openerp.addons.field_secure import models


class HrAppraisalInputLine(models.SecureModel):
    _inherit = 'hr.appraisal.input.line'

    explanation = fields.Secure(string="Explanation",
                                security='_password_security', password=False)

    @api.multi
    def _password_security(self):
        """
        Author can see and edit all secured fields of his appraisal input
        HR manager and Manager of the employee_of_current_user can only see
            all secured fields of all appraisal inputs.
        """
        is_allow = False
        for rec in self:
            if rec.input_id._password_security():
                is_allow = True
            else:
                is_allow = False
                break
        return is_allow
