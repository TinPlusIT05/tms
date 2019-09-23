# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp import SUPERUSER_ID


class hr_employee(models.Model):
    _inherit = "hr.employee"

    @api.multi
    def _wage_history_count(self):
        """
        Count number of wage history records
        """
        for employee in self:
            wage_history = self.env['hr.wage.history']
            employee.wage_history_count = wage_history.search_count(
                [('name', '=', employee.id)])

    wage_history_count = fields.Integer(
        string='Wage History', compute="_wage_history_count")
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
