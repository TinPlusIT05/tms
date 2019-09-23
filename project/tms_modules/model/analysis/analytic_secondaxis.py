# -*- coding: utf-8 -*-
from openerp import api, models, fields
import openerp.addons.decimal_precision as dp  # @UnresolvedImport


class AnalyticSecondaxis(models.Model):

    _name = "analytic.secondaxis"
    _description = "Second Analytical Axes"

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        acc_ids = []
        context = self._context and self._context.copy() or {}

        if context.get('from_date', False):
            args.append(['date', '>=', context['from_date']])
        if context.get('to_date', False):
            args.append(['date', '<=', context['to_date']])

        if context.get('account_id', False):
            aa_env = self.env['account.analytic.account']
            acc_obj = aa_env.browse(context['account_id'])

            # take the account which has analytic_secondaxis_ids
            acc_who_matters = self._get_first_AA_have_analytic_secondaxis(
                acc_obj)

            if acc_who_matters:
                for i in acc_who_matters.analytic_secondaxis_ids:
                    acc_ids.append(i.id)
                args.append(('id', 'in', acc_ids))

        return super(AnalyticSecondaxis, self).search(
            args, offset, limit, order, count=count)

    @api.model
    def _get_first_AA_wich_have_analytic_secondaxis(self, account):
        """Return the first parent account which have an analytic_secondaxis
           set (goes bottom up, child, then parent)
        """
        if account.analytic_secondaxis_ids:
            return account
        else:
            if account.parent_id:
                return self._get_first_AA_wich_have_analytic_second_axis(
                    account.parent_id)
            else:
                return False

    @api.model
    def name_search(
            self, name, args=None, operator='ilike', context=None, limit=80):
        if not args:
            args = []

        account = self.search([
            ('code', '=', name)] + args, limit=limit)

        if not account:
            account = self.search([
                ('name', 'ilike', '%%%s%%' % name.replace("'", ""))
            ] + args, limit=limit)

        if not account:
            account = self.search(
                [] + args,
                limit=limit)

        # For searching in parent also
        if not account:
            account = self.search([
                ('name', 'ilike', '%%%s%%' % name)
            ] + args, limit=limit)

            newacc = account
            while newacc:
                newacc = self.search([
                    ('parent_id', 'in', newacc)
                ] + args, limit=limit)
                account += newacc

        return account.name_get()

    @api.model
    def _compute_level_tree(self, child_ids, res, field_names):
        def recursive_computation(account, res):
            for son in account.child_ids:
                res = recursive_computation(son, res)
                for field in field_names:
                    if account.currency_id.id == son.currency_id.id or \
                            field == 'quantity':
                        res[account.id][field] += res[son.id][field]
                    else:
                        res[account.id][field] += son.currency_id.compute(
                            son.currency_id.id,
                            account.currency_id.id,
                            res[son.id][field])
            return res

        for account in self:
            if account.id not in child_ids:
                continue
            res = recursive_computation(account, res)
        return res

    @api.multi
    def _debit_credit_bal_qtty(self):
        res = {}
        context = self._context and self._context.copy() or {}
        childs = self.search([('parent_id', 'child_of', self.ids)])
        child_ids = childs.ids

        if not child_ids:
            return res

        where_date = ''
        where_clause_args = [tuple(child_ids)]
        if context.get('from_date', False):
            where_date += " AND l.date >= %s"
            where_clause_args += [context['from_date']]
        if context.get('to_date', False):
            where_date += " AND l.date <= %s"
            where_clause_args += [context['to_date']]
        self._cr.execute("""
            SELECT a.id,
                 sum(
                     CASE WHEN l.amount > 0
                     THEN l.amount
                     ELSE 0.0
                     END
                      ) as debit,
                 sum(
                     CASE WHEN l.amount < 0
                     THEN -l.amount
                     ELSE 0.0
                     END
                      ) as credit,
                 COALESCE(SUM(l.amount),0) AS balance,
                 COALESCE(SUM(l.unit_amount),0) AS quantity
            FROM analytic_secondaxis a
              LEFT JOIN account_analytic_line l
              ON (a.id = l.analytic_secondaxis_id)
            WHERE a.id IN %s
            """ + where_date + """
            GROUP BY a.id
        """, where_clause_args)

        for ac_id, debit, credit, balance, quantity in self._cr.fetchall():
            res[ac_id] = {
                'debit': debit, 'credit': credit,
                'balance': balance, 'quantity': quantity
            }
        res = self._compute_level_tree(
            child_ids, res,
            ['debit', 'credit', 'balance', 'quantity'])
        for analytic_id, vals in res.iteritems():
            analytic_obj = self.browse(analytic_id)
            for key, field_val in vals.iteritems():
                if key == 'debit':
                    analytic_obj.debit = field_val
                if key == 'credit':
                    analytic_obj.credit = field_val
                if key == 'balance':
                    analytic_obj.balance = field_val
                if key == 'quantity':
                    analytic_obj.quantity = field_val

    @api.model
    def _default_company(self):
        user = self.env['res.users'].browse(self._uid)
        if user.company_id:
            return user.company_id.id
        companies = self.env['res.company'].search([('parent_id', '=', False)])
        return companies and companies[0] and companies[0].id or False

    @api.model
    def _default_currency(self):
        user = self.env['res.users'].browse(self._uid)
        return user.company_id and \
            user.company_id.currency_id and \
            user.company_id.currency_id.id or False

    # Columns

    # Second Axis code
    code = fields.Char(
        string='Code', required=True, size=64)

    # name of the code
    name = fields.Char(
        string='Analytic Second Axis', required=True, size=64, translate=True)

    # parent analytic second axis
    parent_id = fields.Many2one(
        'analytic.secondaxis', string='Parent Analytic Second Axis')

    # link to account.analytic account
    project_ids = fields.Many2many(
        comodel_name='account.analytic.account',
        relation='analytic_secondaxis_analytic_rel',
        column1='analytic_secondaxis_id', column2='analytic_id',
        string='Concerned Analytic Account')

    # link to the children activites
    child_ids = fields.One2many(
        comodel_name='analytic.secondaxis', inverse_name='parent_id',
        string='Childs analytic second axis')

    balance = fields.Float(
        compute='_debit_credit_bal_qtty', string='Balance',
        digits_compute=dp.get_precision('Account'))

    debit = fields.Float(
        compute='_debit_credit_bal_qtty', string='Debit',
        digits_compute=dp.get_precision('Account'))

    credit = fields.Float(
        compute='_debit_credit_bal_qtty', string='Credit',
        digits_compute=dp.get_precision('Account'))

    quantity = fields.Float(
        compute='_debit_credit_bal_qtty', string='Quantity')

    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=_default_currency)

    company_id = fields.Many2one(
        'res.company', string='Company', required=False,
        default=_default_company)
    type = fields.Selection(
        string='Type',
        selection=[
            ('billable_production', 'Billable Production'),
            ('billable_not_production', 'Billable Not Production'),
            ('not_billable', 'Not Billable')])
