# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2017 Trobz (<http://trobz.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import fields, api
from openerp.addons.field_secure import models
from openerp import SUPERUSER_ID


class HrAppraisalInput(models.SecureModel):
    _inherit = 'hr.appraisal.input'

    expect_salary_raise = fields.Secure(
        string="Expected Salary Raise (%)", password=True,
        security="_security_https_password")

    @api.multi
    def _security_https_password(self):
        """
        Only author of input and Admin profile can see expect_salary_raise
        """
        user = self.env.user
        can_access = False
        for rec in self:
            if user.id == SUPERUSER_ID or rec.author_id.user_id.id == user.id:
                can_access = True
            if user.has_group('tms_modules.group_profile_tms_admin'):
                can_access = True
        return can_access

    @api.multi
    def _password_security(self):
        """
        Author can see and edit all secured fields of his appraisal input
        HR manager and Manager of the employee_of_current_user and Evaluators
        of appraisal can only see all secured fields of all appraisal inputs.
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
                    employee_obj.id == rec.author_id.id or \
                    employee_obj.id == rec.appraisal_id.employee_id.id or \
                    rec._uid in rec.appraisal_id.evaluators_user_ids.ids:
                    # Current user is author or employee manager or HR manager
                    # or evaluator of appraisal can access to all secured
                    # fields
                is_allow = True
            else:
                is_allow = False
                break
        return is_allow
