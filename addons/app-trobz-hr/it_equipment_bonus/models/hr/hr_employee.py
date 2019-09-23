from openerp import models, fields, api
from datetime import datetime
from dateutil import relativedelta


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    benefit_start = fields.Date(
        string='Benefit Start', readonly=True,
        compute='_get_benefit_start',
        store=True,
        help='Calculated as MAX(2014-01-01,employee_hire_date)')
    cred_benefit = fields.Float(
        string='Credited Benefit', readonly=True,
        compute='_get_cred_benefit',
        store=True,
        help='Total IT Equipment Bonus from Benefit Start')
    debit_benefit = fields.Float(
        string='Debited Benefit', readonly=True,
        compute='_get_debit_benefit',
        store=True,
        help='Total amount that this employee has used to purchase equipments')
    balance_benefit = fields.Float(
        string='Balance Benefit', readonly=True,
        compute='_get_balance_benefit',
        store=True,
        help='Remaining amount that employee can use to purchase equipment')

    amt_req_made = fields.Integer(
        string='Equipment Requests Made', compute='_get_all_request')
    amt_benefit = fields.Integer(
        string='Amount input for Benefit', compute='_get_amount_benefit')
    it_equipment_bonus_ids = fields.One2many(
        'employee.it.bonus',
        'employee_id',
        'Bonus'
    )

    @api.multi
    def _get_amount_benefit(self):
        """
            Setup Parameter for System Config
        """
        ir_config_param_env = self.env['ir.config_parameter']
        numb = ir_config_param_env.get_param('amt_benefit', '')
        for rec in self:
            rec.amt_benefit = numb

    @api.depends('hire_date')
    def _get_benefit_start(self):
        """
            Calculate the Benefit Start Date
        """
        ir_config_param_env = self.env['ir.config_parameter']
        start_date = \
            ir_config_param_env.get_param('benefit_it_eq_bonus_start_date',
                                          '2014-01-01')
        for employee in self:
            employee.benefit_start = max(start_date, employee.hire_date)

    @api.depends('it_equipment_bonus_ids', 'it_equipment_bonus_ids.amount',
                 'it_equipment_bonus_ids.apply_date')
    def _get_cred_benefit(self):
        """
            Credit Benefit = \
            Total IT Equipemnt Bonus from benefit_start date
        """
        for employee in self:
            employee.cred_benefit = sum(
                employee.it_equipment_bonus_ids.filtered(
                    lambda x: x.apply_date >= employee.benefit_start
                ).mapped('amount')
            )

    @api.multi
    def _get_all_request(self):
        """
            Retrieve all Request from current Employee
        """
        for employee in self:
            employee.amt_req_made = self.env['hr.equipment.request'].\
                search_count([('employee_id', '=', employee.id)])

    @api.model
    def _get_debit_benefit(self):
        """
            First, get all the requests that employee had made.
            Debit is caculated as sum of all of Purchased Price or
            Trobz Contribution Amount from the
            Request employee made.
            If the Request is Partial Approved then the amount is used will be
            the Trobz Contribution amount
            If the Request is Fully Approved then the amount is used  will be
            the Purchased Price.
        """
        for employee in self:
            # Search for employe Request with requests that have been approved.
            req_recordset = self.env['hr.equipment.request'].search([
                ('employee_id', '=', employee.id),
                ('state', 'in', ['request_apprvd', 'purchase_apprvd',
                                 'purchased'])])
            total = 0
            for record in req_recordset:
                if record.partial_apprv:
                    total += record.trobz_contr_amt
                else:
                    total += record.purchase_price

            employee.debit_benefit = total

    @api.depends("debit_benefit", 'cred_benefit')
    @api.multi
    def _get_balance_benefit(self):
        """
            Get Current Balance of Employee's Benefit at Trobz
            Balance = Credit Benefit - Debit Benefit
        """
        for employee in self:
            employee.balance_benefit = employee.cred_benefit - \
                employee.debit_benefit
