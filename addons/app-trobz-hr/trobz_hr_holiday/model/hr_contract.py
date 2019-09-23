# -*- coding: utf-8 -*-

from openerp import models, fields


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    monthly_paid_leaves = fields.Float(default=1.0,
                                       string="Monthly Paid leaves",
                                       digits=(1, 1))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
