# -*- encoding: utf-8 -*-
from openerp import models, fields, api


class res_partner(models.Model):

    _inherit = "res.partner"

    mailing_list_ids = fields.Many2many(
        'mailman.list', string='Mailing Lists')

    @api.multi
    def button_remove_all_mailing_list(self):
        for rec in self:
            rec.mailing_list_ids = False
        return True

    # TODO: In the future, add the create / write.
    # See comment in the res_partner_view.xml
