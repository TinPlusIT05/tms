# -*- encoding: UTF-8 -*-
from openerp import fields, models


class HrEmployee(models.Model):

    _inherit = "hr.employee"

    applicant_id = fields.Many2one('hr.applicant', string='Related Applicant')
