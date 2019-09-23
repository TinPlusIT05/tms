# -*- encoding: UTF-8 -*-

from openerp import api, models, fields
import logging


class account_analytic_account(models.Model):

    _inherit = "account.analytic.account"
    _description = "Analytic accounts for TMS."
    _order = "name"

    # Columns
    analytic_secondaxis_ids = fields.Many2many(
        comodel_name='analytic.secondaxis',
        relation='analytic_secondaxis_analytic_rel',
        column1='analytic_id', column2='analytic_secondaxis_id',
        string='Related analytic second axis'
    )

    @api.model
    def function_update_sequence_for_analytic_code(self):
        logging.info('====START Update sequence for analytic code ====')
        ir_sequence_env = self.env['ir.sequence']
        analytic_acc_codes = ir_sequence_env.search(
            [('code', '=', 'account.analytic.account')])
        analytic_acc_code = analytic_acc_codes and \
            analytic_acc_codes[0] or False
        if analytic_acc_code:
            analytic_acc_code.write({'implementation': 'standard'})
            self._cr.execute("""
              SELECT MAX(code)
              FROM account_analytic_account
              WHERE code IS NOT NULL;
            """)
            last_value = self._cr.fetchone()
            if last_value and last_value[0] is not None:
                last_value = last_value[0].replace(
                    analytic_acc_code.prefix, '')
                self._cr.execute("""
                    SELECT SETVAL('ir_sequence_%03d', %d);
                """ % (analytic_acc_code.id, int(last_value)))
        logging.info('====END Update sequence for analytic code ====')
        return True

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        # TODO: return domain = {'partner_id': [('id', '=',
        # parent_partner_id)]}
        if self.parent_id:
            self.partner_id = self.parent_id.partner_id and \
                self.parent_id.partner_id.id or False
