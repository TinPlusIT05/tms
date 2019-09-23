# -*- encoding: utf-8 -*-

from openerp import api, fields, models
from datetime import date, datetime
from lxml import etree
from openerp.osv.orm import setup_modifiers
from dateutil.relativedelta import relativedelta
import logging


class ProjectSupportContracts(models.Model):

    _inherit = ['mail.thread']
    _name = "project.support.contracts"
    _description = "Project Support Contracts"

    name = fields.Char(
        string="Name", required=True, track_visibility='onchange')
    partner_id = fields.Many2one(
        'res.partner', domain="[('customer', '=', True)]", required=True,
        string="Customer", track_visibility='onchange')
    project_ids = fields.Many2many(
        'tms.project', 'ref_project_contract',
        'contract_id', 'project_id',
        string="Project", track_visibility='onchange')
    project_activity_ids = fields.Many2many(
        'tms.activity',
        'ref_activity_contracts',
        'contract_id', 'activity_id',
        string="Activity",
        track_visibility='onchange')
    budget = fields.Float(
        string="Budget (d)", digits=(6, 2), track_visibility='onchange')
    start_date = fields.Date(
        string="Date Start", track_visibility='onchange', required=True)
    end_date = fields.Date(
        string="Date End", track_visibility='onchange', required=True)
    spent = fields.Float(string="Spent (d)", compute="_compute_spent_days")
    prorata_budget = fields.Float(
        compute="_compute_prorata_data",
        digits=(6, 2)
    )
    prorata_consumption = fields.Float(
        compute="_compute_prorata_data",
        digits=(6, 2)
    )
    state = fields.Selection(
        selection=[
            ('planned', 'Planned'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
        ],
        default='planned',
        string="Status"
    )
    auto_renew = fields.Boolean(string="Auto Renewal?", default=False)
    forecasted_date_done = fields.Date(
        compute="_compute_prorata_data",
        string="Forecasted Date Done"
    )
    wh_count = fields.Integer(
        "Working Hours Count",
        compute="_compute_spent_days")
    is_over_budget = fields.Boolean(compute="_compute_is_over_budget",
                                    store=True)

    @api.constrains('start_date', 'end_date')
    def _check_period(self):
        """
        Check start date and end date of contracts
        """
        for contract in self:
            if contract.end_date <= contract.start_date:
                raise Warning('Date End must be greater than Date Start!')
            today = date.today()
            start = datetime.strptime(contract.start_date, '%Y-%m-%d').date()
            end = datetime.strptime(contract.end_date, '%Y-%m-%d').date()
            if contract.state == 'done':
                continue
            if today < start:
                contract.state = 'planned'
            elif start <= today and today <= end:
                contract.state = 'in_progress'
            elif today > end:
                contract.state = 'done'
        return True

    @api.constrains('start_date', 'end_date', 'project_activity_ids')
    def _check_overlap_contracts(self):
        """
        Check contracts's overlapping of each partner
        Can not have 2 project activities in support contratcs at same time
        Using a dictionary
        {
            act_id1: [(contract_id, start, end), (contract_id, start, end)],
            act_id2: [(contract_id, start, end), (contract_id, start, end)]
        }
        """
        data = {}
        contracts = self.env['project.support.contracts'].search(
            [('state', 'in', ('planned', 'in_progress'))])
        for contract in contracts:
            for act in contract.project_activity_ids:
                start1 = contract.start_date
                end1 = contract.end_date
                if act.id in data.keys():
                    for dt in data[act.id]:
                        if dt[0] == contract.id:
                            continue
                        start2 = dt[1]
                        end2 = dt[2]
                        if (start1 <= start2 and start2 <= end1) or \
                                (start2 <= start1 and start1 <= end2):
                            raise Warning(
                                'Can not have same activity in 2 contracts' +
                                'with overlapped period')
                        else:
                            data[act.id].append((contract.id, start1, end1))
                else:
                    data[act.id] = [(contract.id, start1, end1)]
        return True

    @api.multi
    def _compute_spent_days(self):
        for record in self:
            act_ids = record.project_activity_ids.ids
            act_ids.extend([-1, 0])
            sql = '''
            SELECT SUM(duration_hour), COUNT(id)
            FROM tms_working_hour AS wh
            WHERE wh.tms_activity_id IN %s
                AND wh."date" >= '%s'
                AND wh."date" <= '%s'
            ''' % (tuple(act_ids), record.start_date, record.end_date)
            self._cr.execute(sql)
            wh = self._cr.fetchone()
            if wh:
                record.spent = wh[0] and round(wh[0] / 8, 2) or 0.0
                record.wh_count = wh[1] or 0

    @api.depends('budget', 'spent')
    def _compute_is_over_budget(self):
        for record in self:
            act_ids = record.project_activity_ids.ids
            act_ids.extend([-1, 0])
            sql = '''
            SELECT SUM(duration_hour)
            FROM tms_working_hour AS wh, tms_activity AS act
            WHERE wh.tms_activity_id IN %s
                AND act.state not in ('closed', 'canceled')
                AND act.id = wh.tms_activity_id
                AND wh."date" >= '%s'
                AND wh."date" <= '%s'
            ''' % (tuple(act_ids), record.start_date, record.end_date)
            self._cr.execute(sql)
            wh = self._cr.fetchone()
            if wh:
                spent = wh[0] and round(wh[0] / 8, 2) or 0.0
            if spent > record.budget:
                record.is_over_budget = True
            else:
                record.is_over_budget = False

    @api.model
    def update_renew_support_contract(self):
        """
        Set status of Support Contract whose state is not 'done'
        by start_date and end_date.
        _______________________________________
        |---------start------------end--------|
        |_planned__|__in_progress___|___done__|
        """
        contracts = self.env[
            'project.support.contracts'].search(
                [('state', '!=', 'done')]
        )
        today = date.today()
        for contract in contracts:
            start = datetime.strptime(contract.start_date, '%Y-%m-%d').date()
            end = datetime.strptime(contract.end_date, '%Y-%m-%d').date()
            if contract.state == 'done':
                continue
            if today < start:
                contract.state = 'planned'
            elif start <= today and today <= end:
                contract.state = 'in_progress'
            elif today > end:
                contract.state = 'done'

    @api.multi
    def button_mark_done(self):
        for rec in self:
            rec.state = 'done'

    def fields_view_get(
        self, cr, uid, view_id=None, view_type=None,
            context=None, toolbar=False, submenu=False):
        res = super(
            ProjectSupportContracts, self).fields_view_get(
                cr, uid, view_id=view_id, view_type=view_type,
                context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            # Set all fields read only when state is close.
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field"):
                node.set('attrs', "{'readonly': [('state', '=', 'done')]}")
                node_name = node.get('name')
                setup_modifiers(node, res['fields'][node_name])
            res['arch'] = etree.tostring(doc)
        return res

    @api.constrains('project_ids')
    def check_project_ids(self):
        msg = "Can not add projects which have state is Done or Asleep!"
        for contract in self:
            for project in contract.project_ids:
                if project.state in ('done', 'asleep'):
                    raise Warning(msg)

    @api.constrains('project_activity_ids')
    def check_project_activity_ids(self):
        msg = "Can not add project activities " + \
              "which have state is Done or Cancel!"
        for contract in self:
            for activity in contract.project_activity_ids:
                if activity.state in ('closed', 'canceled'):
                    raise Warning(msg)

    @api.multi
    def write(self, vals):
        """
        When done a support contract, create new contract with same values
        if auto_renew is checked
        """
        contract_env = self.env['project.support.contracts']
        res = super(ProjectSupportContracts, self).write(vals)
        if 'state' in vals and vals['state'] == 'done':
            for contract in self:
                if not contract.auto_renew:
                    continue
                if not (contract.end_date and contract.start_date):
                    logging.INFO(
                        "Start date or end date of contract is not set!")
                    continue
                start = datetime.strptime(
                    contract.start_date, '%Y-%m-%d').date()
                end = datetime.strptime(
                    contract.end_date, '%Y-%m-%d').date()
                delta = relativedelta(end, start)
                new_start = end + relativedelta(days=1)
                new_end = new_start + delta
                vals = {
                    'name': contract.name,
                    'partner_id': contract.partner_id.id,
                    'budget': contract.budget,
                    'spent': contract.spent,
                    'start_date': new_start.isoformat(),
                    'end_date': new_end.isoformat(),
                    'auto_renew': contract.auto_renew,
                    'state': 'planned',
                    'project_ids': [(6, 0, contract.project_ids.ids)],
                    'project_activity_ids':
                        [(6, 0, contract.project_activity_ids.ids)],
                }
                contract_env.create(vals)
        return res

    @api.multi
    def _compute_prorata_data(self):
        today = date.today()
        for contract in self:
            start = datetime.strptime(
                contract.start_date, '%Y-%m-%d').date()
            end = datetime.strptime(
                contract.end_date, '%Y-%m-%d').date()
            total_days = (end - start).days
            current_days = (today - start).days
            # Compute pro-rata budgetq
            if total_days == 0:
                contract.prorata_budget = 0.0
            else:
                contract.prorata_budget = (100.0 * current_days) / total_days
            # Compute pro-rata consumption
            if current_days == 0 or total_days == 0 or contract.budget == 0:
                contract.prorata_consumption = 0.0
            else:
                cons = (contract.spent * total_days) / \
                    (contract.budget * current_days)
                contract.prorata_consumption = 100.0 * cons
            # Compute Forecasted date Done
            if contract.spent == 0:
                contract.forecasted_date_done = None
            else:
                delta = (contract.budget * current_days * 1.0) / contract.spent
                contract.forecasted_date_done = \
                    start + relativedelta(days=(delta - 1))

    @api.onchange('partner_id')
    def onchange_projects(self):
        """
        Reset projects if user change customer to another which not same as
        customer on projects
        """
        if not self.partner_id.id:
            return
        is_reset = False
        for project in self.project_ids:
            if project.partner_id.id != self.partner_id.id:
                is_reset = True
                break
        if is_reset:
            self.project_ids = None

    @api.multi
    def view_working_hours(self):
        ctx = self.env.context.copy()
        sql = '''
        SELECT activity_id
        FROM ref_activity_contracts
        WHERE contract_id = %s
        '''
        self._cr.execute(sql % self.id)
        act_ids = [i[0] for i in self._cr.fetchall()]
        act_ids.append(0)
        start = str(self.start_date)
        end = str(self.end_date)
        domain = "[('tms_activity_id', 'in', %s),"
        domain += "('date', '>=', '%s'), ('date', '<=', '%s')]"
        domain = domain % (tuple(act_ids), start, end)
        return {
            'name': 'Working Hours',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'tms.working.hour',
            'type': 'ir.actions.act_window',
            'context': ctx,
            'domain': domain,
            'target': 'current',
        }
