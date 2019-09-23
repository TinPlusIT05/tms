# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime
from openerp.exceptions import Warning


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def _check_contract_time(self):
        today = datetime.now().strftime("%Y-%m-%d")
        contracts = self.env['hr.contract'].search([])
        for contract in contracts:
            if contract['date_end'] and contract['date_end'] < today:
                contract['contract_time'] = 'past'
            if (contract['date_end'] and contract['date_end'] > today) or \
                    (contract['date_end'] is False and
                     contract['date_start'] < today):
                contract['contract_time'] = 'current'
            if contract['date_start'] > today:
                contract['contract_time'] = 'future'

    is_trial = fields.Boolean(
        default=False, string="Is Trial", help="This is in trial period"
    )
    contract_time = fields.Selection(
        [('past', 'Past'), ('current', 'Current'), ('future', 'Future')],
        string="Contract Time", compute=_check_contract_time
    )
    department_id = fields.Many2one(
        'hr.department', string='Department',
        related='employee_id.department_id', store=True,
        depends=('employee_id', 'employee_id.department_id')
    )
    in_progress_date = fields.Date(
        "In progress at the date"
    )

    def get_contract(
            self, cr, uid, employee_id, date_from, date_to, context=None):
        """
        @param employee: employee_id
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee
        that need to be considered for the given dates
        """
        contract_obj = self.pool.get('hr.contract')
        # a contract is valid if it ends between the given dates
        clause_1 = [
            '&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = [
            '&', ('date_start', '<=', date_to),
            ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end
        # (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|',
                    ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [
            ('employee_id', '=', employee_id),
            '|', '|'] + clause_1 + clause_2 + clause_3
        contract_ids = contract_obj.search(
            cr, uid, clause_final, context=context)
        return contract_ids

    @api.constrains('date_start', 'date_end', 'employee_id')
    def _check_date(self):
        for record in self:
            employee_id = record.employee_id.id
            # previous contracts without date end
            contracts_no_date_end = self.search(
                [('date_start', '<=', record.date_start),
                 ('date_end', '=', False),
                 ('employee_id', '=', employee_id),
                 ('id', '!=', record.id)])
            if contracts_no_date_end:
                raise Warning(
                    _("The previous contract (ID: %s, %s) must be ended "
                      "before creating a new contract." %
                      (contracts_no_date_end[0].id,
                       contracts_no_date_end[0].name))
                )
            elif record.date_end:
                contracts = self.search(
                    [('date_start', '<=', record.date_end),
                     ('date_end', '>=', record.date_start),
                     ('employee_id', '=', employee_id),
                     ('id', '!=', record.id)])
            elif not record.date_end:
                contracts = self.search(
                    [('date_end', '>=', record.date_start),
                     ('employee_id', '=', employee_id),
                     ('id', '!=', record.id)])
            if contracts:
                raise Warning(
                    _("You cannot have 2 contracts of an employee "
                      "overlapped on the same duration."))

    # TODO: Override copy function
    # allow duplicate contract with
    # date start = date end of the previous contract +1
    # def copy(self):

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
