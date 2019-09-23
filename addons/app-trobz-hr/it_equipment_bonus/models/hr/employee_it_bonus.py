from openerp import models, fields, api


class employee_it_bonus(models.Model):
    _name = 'employee.it.bonus'
    _description = 'It Equipment Bonus for Employee'
    _order = 'apply_date DESC'

    employee_id = fields.Many2one(
        'hr.employee',
        'Employee',
        required=True
    )
    contract_id = fields.Many2one(
        'hr.contract',
        'Contract',
        required=True
    )
    apply_date = fields.Date('Applied Date')
    amount = fields.Float('Amount')

    @api.onchange('contract_id')
    def _onchange_contract(self):
        self.amount = self.contract_id and self.contract_id.amt_benefit or 0
