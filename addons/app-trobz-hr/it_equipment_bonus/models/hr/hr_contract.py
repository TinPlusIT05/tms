from openerp import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    @api.model
    def _get_amount_benefit(self):
        """
            Setup Parameter for System Config
        """
        ir_config_param_env = self.env['ir.config_parameter']
        numb = ir_config_param_env.get_param('amt_benefit', 0)
        return numb

    amt_benefit = fields.Integer(
        string='Amount input for Benefit',
        default=_get_amount_benefit)

    @api.multi
    def action_generate_it_equipment_bonus(self):
        today = fields.Date.today()
        ir_config_param_env = self.env['ir.config_parameter']
        benefit_start = \
            ir_config_param_env.get_param('benefit_it_eq_bonus_start_date',
                                          '2014-01-01')
        it_bonus_env = self.env['employee.it.bonus']
        mid_month_day = 15
        for contract in self.filtered(
                lambda x: not x.date_end or x.date_end > benefit_start):
            employee_id = contract.employee_id.id
            contract_id = contract.id
            amt_benefit = contract.amt_benefit
            # remove old data
            it_bonus_env.search([
                ('contract_id', '=', contract.id)]).unlink()
            # Generate for each month in contract
            date_start = contract.date_start
            date_start = date_start <= benefit_start and\
                benefit_start or date_start
            # Limitless contract
            date_end = contract.date_end and contract.date_end < today and\
                contract.date_end or today
            date_start_obj = datetime.strptime(date_start, DF)
            # First month in contract
            if date_start_obj.day <= mid_month_day:
                # Generate bonus
                # If number of day in month less than 15
                it_bonus_env.create({
                    'contract_id': contract_id,
                    'employee_id': employee_id,
                    'amount': amt_benefit,
                    'apply_date': date_start_obj
                })
            next_date_obj = date_start_obj + relativedelta(months=1)
            date_end_obj = datetime.strptime(date_end, DF)
            while next_date_obj < date_end_obj:
                it_bonus_env.create({
                    'contract_id': contract_id,
                    'employee_id': employee_id,
                    'amount': amt_benefit,
                    'apply_date': next_date_obj.strftime(DF)
                })
                next_date_obj += relativedelta(months=1)

            # For the lastest contract.
            # Exp:
            # date_end is 2019-08-25
            # today is 2019-08-09
            # date_end_obj is 2019-08-09
            # next_date_obj now is 2019-08-24
            # Need to add it equipment bonus for this case
            today_obj = datetime.strptime(today, DF)
            if next_date_obj.year == date_end_obj.year and\
                    next_date_obj.month == date_end_obj.month and\
                    next_date_obj.day > date_end_obj.day:
                it_bonus_env.create({
                    'contract_id': contract_id,
                    'employee_id': employee_id,
                    'amount': amt_benefit,
                    'apply_date': next_date_obj.strftime(DF)
                })

    @api.model
    def cron_monthly_generate_it_eq_bonus(self, today=None):
        if not today:
            today = fields.Date.today()
        active_contracts = self.search([
            ('is_trial', '=', False),
            '|',
            ('date_end', '>', today),
            ('date_end', '=', False)])
        it_bonus_env = self.env['employee.it.bonus']
        for contract in active_contracts:
            it_bonus_env.create({
                'contract_id': contract.id,
                'employee_id': contract.employee_id.id,
                'amount': contract.amt_benefit,
                'apply_date': today
            })
