# -*- encoding: utf-8 -*-

from openerp import fields, models, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    appraisals_count = fields.Integer(string="Appraisals",
                                      compute="_compute_appraisals_count")

    @api.one
    def _compute_appraisals_count(self):
        appraisal_obj = self.env['hr.appraisal']
        self.appraisals_count = appraisal_obj.search_count([
            ('employee_id', '=', self.id)
        ])
