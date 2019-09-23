# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from datetime import datetime, date
from dateutil import relativedelta as rld
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp


class DepreciationLines(models.Model):
    _name = 'depreciation.lines'
    _description = 'Depreciation amount in period for calculation.'
    _inherit = ['mail.thread']

    name = fields.Char(string="Name",
                       compute="_compute_line_name")
    asset_id = fields.Many2one(string="Assets",
                               comodel_name="tms.asset")
    amount = fields.Float(string="Depreciation Amount",
                          digits_compute=dp.get_precision('Account'),
                          required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    number_of_days = fields.Integer(string="Number of Days",
                                    compute="_compute_num_of_days")
    is_depreciated = fields.Boolean("Is depreciated?")
    employee_id = fields.Many2one(
        string="Assignee", comodel_name="hr.employee",
        help="Employee who has to pay for depreciation."
        "Set to empty if Trobz pay this depreciation")

    @api.constrains('end_date')
    def _constrains_end_date(self):
        for record in self:
            if record.end_date < record.start_date:
                raise Warning(_('End Date must be greater than Start Date.'))

    @api.constrains('amount')
    def _constrains_amount(self):
        for record in self:
            if record.amount <= 0:
                raise Warning(_('Amount must be greater than 0.'))

    @api.depends('start_date', 'end_date', 'asset_id')
    @api.multi
    def _compute_line_name(self):
        for line in self:
            line.name = \
                "Depreciation Amount for %s in period %s - %s" % \
                (line.asset_id.name, line.start_date, line.end_date)

    @api.depends('start_date', 'end_date', 'asset_id')
    @api.multi
    def _compute_num_of_days(self):
        fmt = "%Y-%m-%d"
        for line in self:
            if line.asset_id and line.start_date and line.end_date:
                start_date = datetime.strptime(line.start_date, fmt)
                end_date = datetime.strptime(line.end_date, fmt)
                line.number_of_days = \
                    abs(rld.relativedelta(start_date, end_date).days) + 1

    @api.model
    def _validate_period(self, depreciation_line):
        for line in depreciation_line.asset_id.depreciation_line_ids:
            if line.id != depreciation_line.id:
                # calculate overlapping days
                if max(depreciation_line.start_date, line.start_date) <= \
                        min(depreciation_line.end_date, line.end_date):
                    return False
        return True

    @api.model
    def create(self, vals):
        td = date.today()
        res = super(DepreciationLines, self).create(vals)
        enddate = datetime.strptime(res.end_date, '%Y-%m-%d').date()
        if enddate < td:
            res.depreciated = True
        if not self._validate_period(res):
            raise Warning(_("This period is overlapping with other."))
        today = datetime.now().date()
        if res.start_date:
            if res.start_date <= str(today):
                res.is_depreciated = True
            else:
                res.is_depreciated = False
        return res

    @api.multi
    def depreciated_line(self):
        return self.write({'depreciated': True})

    @api.model
    def run_update_depreciation_amount(self):
        # get current month
        today = datetime.now()
        lines = self.search([('start_date', '<=', today),
                             ('is_depreciated', '=', False)])
        for line in lines:
            line.is_depreciated = True
        return lines.depreciated_line()
