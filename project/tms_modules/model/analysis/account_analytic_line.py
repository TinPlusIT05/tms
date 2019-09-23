# -*- encoding: UTF-8 -*-
from openerp import models, fields


class account_analytic_line(models.Model):

    _inherit = "account.analytic.line"

    analytic_secondaxis_id = fields.Many2one(
        'analytic.secondaxis', 'Analytic second axis')
