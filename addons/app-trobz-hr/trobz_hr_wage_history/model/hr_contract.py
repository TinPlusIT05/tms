# -*- coding: utf-8 -*-
from openerp import models, api
from datetime import date
import logging


class hr_contract(models.Model):
    _inherit = "hr.contract"

    @api.model
    def track_wage_history(self, contract, new_wage, date_of_change=False):
        """
        Prepare values of history record
        @param contract: browse_record of the changed contract
        @param new_wage: new wage is updated on contract
        @param date_of_change: if False, get contract date start or today
        """
        his_obj = self.env['hr.wage.history']

        employee = contract.employee_id
        difference = 0
        percentage = 0
        if not date_of_change:
            date_of_change = date.today()

        wage_histories = his_obj.search([('name', '=', employee.id)],
                                        order='date_of_change DESC, id DESC',
                                        limit=1)
        if not wage_histories:
            # The first history record
            # old wage: wage of this contract
            old_wage = contract.wage
            new_wage = contract.wage
            date_of_change = contract.date_start
        else:
            # Change wage on contract
            # old wage: new wage of previous one
            latest_wage_history = wage_histories[0]
            old_wage = latest_wage_history.new_wage
            difference = new_wage - old_wage
            percentage = old_wage > 0 and difference / old_wage * 100 or 0

        wage_history = {
            'name': employee.id,
            'contract_id': contract.id,
            'department_id': contract.department_id
            and contract.department_id.id or False,
            'job_id': contract.job_id and contract.job_id.id or False,
            'current_wage': old_wage,
            'new_wage': new_wage,
            'difference': difference,
            'percentage': percentage,
            'date_of_change': date_of_change,
            'responsible_user_id': self._uid,
        }
        his_obj.create(wage_history)

    @api.model
    def check_previous_wage_history(self, employee):
        last_contract = employee.contract_id
        return last_contract

    @api.model
    def create(self, vals):
        """
        When creating a contract,
        create a wage history to track the first contract wage.
        """
        res = super(hr_contract, self).create(vals)
        self.track_wage_history(res, vals.get('wage', 0))
        return res

    @api.multi
    def write(self, vals):
        """
        When updating the wage on contract,
        create a wage history record to track the current and new contract wage
        """
        hr_contract_obj = self.env['hr.contract']
        if vals.get('wage', False):
            for contract in self:
                hr_contract_obj.track_wage_history(contract, vals['wage'])
        return super(hr_contract, self).write(vals)

    @api.model
    def update_wage_history_for_existed_contracts(self):
        """
        For existed contracts, create the wage history
        The specific project can use this function to update history data
        """
        logging.info('START: update_wage_history_for_existed_contracts')
        contract_obj = self.env['hr.contract']
        employees = self.env['hr.employee'].search(
            ['|', ('active', '=', True), ('active', '=', False)]
        )

        for employee in employees:
            contracts = contract_obj.search(
                [('employee_id', '=', employee.id)],
                order='date_start')
            if contracts:
                is_first_contract = True
                prev_wage = False
                for contract in contracts:
                    wage = contract.wage
                    if is_first_contract or prev_wage != wage:
                        logging.info(
                            'Create (Employee: %s - old wage :%s - wage: %s)'
                            % (contract.employee_id.name, prev_wage, wage)
                        )
                        # Create the wage history record in case
                        # The first contract (is_first_contract = True)
                        # The next contract: current wage is different
                        #    from the previous wage
                        contract_obj.track_wage_history(
                            contract, wage, date_of_change=contract.date_start
                        )
                        prev_wage = wage
                        # is_first_contract set False
                        # after creating the first wage history
                        # for the first contract
                        is_first_contract = False

        logging.info('END: update_wage_history_for_existed_contracts')
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
