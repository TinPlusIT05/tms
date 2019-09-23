# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp


DEPRECATION_PERIOD = [
    ('0', 'None'),
    ('6', '6 months'),
    ('12', '12 months'),
    ('24', '2 years'),
    ('36', '3 years'),
]


class TmsAsset(models.SecureModel):
    _name = 'tms.asset'
    _description = 'IT Assets that allow to manage asset for each employee.'
    _inherit = ['mail.thread']

    name = fields.Char(
        string="Assets", required=False,
        store=True, compute="_compute_asset_name")
    request_id = fields.Many2one(
        string="IT Equipment Request",
        comodel_name="hr.equipment.request",
        track_visibility="onchange")
    trobz_contribution = fields.Float(
        string="Trobz Contribution",
        track_visibility="onchange")
    financial_agreement = fields.Secure(
        password=False, multiline=True,
        track_visibility='on_change',
        string='Financial Agreement')
    purchased_price = fields.Float(
        string="Purchase Price",
        track_visibility="onchange")
    purchased_date = fields.Date(
        string="Purchased Dated",
        default=datetime.now().today())
    category_id = fields.Many2one(
        string="Equipment Category",
        comodel_name="hr.equipment.category")
    residual_value = fields.Float(
        string="Residual Value",
        compute='_compute_residual_value',
        store=True)
    salvage_value = fields.Float(
        string="Salvage Value",
        compute="_compute_salvage_value",
        store=True)
    depreciation_amount = fields.Float(
        string="Depreciation Amount (month)",
        digits_compute=dp.get_precision('Assets'),
        compute="_compute_depreciation_amount",
        store=True)
    depreciation_period = fields.Selection(
        DEPRECATION_PERIOD,
        string="Depreciation Period", default='0')
    owner_id = fields.Many2one(
        string="Owner",
        comodel_name="hr.employee",
        track_visibility="onchange")
    assignee_id = fields.Many2one(
        string="Assignee",
        comodel_name="hr.employee",
        track_visibility="onchange")
    assigning_date = fields.Date(
        string="Latest Assigned Date")
    item_condition_id = fields.Many2one(
        string="Current Equip. Status",
        comodel_name="item.condition")
    condition_details = fields.Text(string="Conditional Details")
    type = fields.Selection(
        [
            ('trobz', "Trobz's Assets"),
            ('personal', "Personal Asset")
        ],
        string="Asset Type",
        default='personal')
    supplier_id = fields.Many2one(
        string="Supplier",
        comodel_name="res.partner",
        domain="[('supplier', '=', True)]")
    internal_code = fields.Char(
        string="Internal Code",
        help="Tracking asset by internal code is good"
        " for management in document.",
        track_visibility="onchange",
        default=lambda self: self.env[
            'ir.sequence'].next_by_code('tms.asset.seq') or 'ASSET-')
    depreciation_line_ids = fields.One2many(
        string="Depriciation Lines",
        comodel_name="depreciation.lines",
        inverse_name="asset_id",
        track_visibility="onchange")
    assign_history_ids = fields.One2many(
        string=u'Asset Assign History',
        comodel_name='asset.assign.history',
        inverse_name='asset_id',
    )
    is_depreciate_it_fund = fields.Boolean(
        string="Is Depreciated From IT Fund?",
        default=False
    )
    state = fields.Selection(
        [
            ('in_use', "In Use"),
            ('no_use', "No Use"),
            ('scrap', "Scrap"),
        ],
        string="Asset State",
        default='in_use')
    partial_type = fields.Selection(
        [
            ('none', "None"),
            ('it_fund', "IT Fund"),
            ('salary', "Salary"),
            ('cash', "Cash"),
        ],
        string="Partial Type", default='none')
    partial_per_month = fields.Float(
        string="Partial Per Month",
        track_visibility="onchange")

    @api.depends('owner_id', 'category_id', 'purchased_date')
    def _compute_asset_name(self):
        """"
            Generate Name for Asset
            {Category}-{Employee_Name}-{Purchased date YYYY-MM-DD}
        """
        for asset in self:
            asset_name = ""
            if asset.category_id:
                asset_name += asset.category_id.name + "-"
            if asset.owner_id:
                asset_name += asset.owner_id.name + "-"
            if asset.purchased_date:
                asset_name += str(asset.purchased_date)
            if not asset_name:
                asset_name = "New Asset"
            asset.name = asset_name

    @api.onchange('type')
    def onchange_asset_type(self):
        if self.type != 'personal':
            self.owner_id = None
            self.partial_type = 'none'
        elif self.type == 'personal':
            self.assignee_id = self.owner_id
            self.residual_value = 0.0
            self.salvage_value = 0.0
            self.is_depreciate_it_fund = False

    @api.onchange('partial_type')
    def onchange_partial_type(self):
        if self.partial_type == 'none':
            self.trobz_contribution = self.purchased_price
        if self.partial_type != 'cash':
            self.partial_per_month = 0.0

    @api.onchange('purchased_price')
    def onchange_purchased_price(self):
        if self.partial_type == 'none':
            self.trobz_contribution = self.purchased_price

    @api.depends("purchased_price", 'depreciation_period',
                 "salvage_value")
    @api.multi
    def _compute_residual_value(self):
        for record in self:
            if record.depreciation_period == '0':
                record.residual_value = 0
            else:
                record.residual_value = \
                    record.purchased_price - record.salvage_value

    @api.depends(
        "purchased_price", 'depreciation_period',
        "depreciation_line_ids", "depreciation_line_ids.is_depreciated")
    @api.multi
    def _compute_salvage_value(self):
        for rec in self:
            amount = 0
            for line in rec.depreciation_line_ids:
                if line.is_depreciated:
                    amount += line.amount
            rec.salvage_value = amount

    @api.depends("purchased_price", 'depreciation_period', "purchased_date")
    @api.multi
    def _compute_depreciation_amount(self):
        for record in self:
            period = int(record.depreciation_period)
            if period != 0 and \
                    record.purchased_price > 0 and record.purchased_date:
                record.depreciation_amount = record.purchased_price / period
            else:
                record.depreciation_amount = None

    def get_asset_assignee(self, asset, start, end):
        """
        Return assignee of asset in period from start to end.
        In a month, if has two owners, get first owner
        """
        if not asset or not (start and end):
            return None
        if start > end:
            raise Warning('Can get owner if start < end!')
        assigns = self.env[
            'asset.assign.history'].search([('asset_id', '=', asset.id)])
        for assign in assigns:
            if not assign.start_date:
                continue
            start_date = datetime.strptime(
                assign.start_date, '%Y-%m-%d')
            start_date = start_date.date()

            if not assign.end_date:
                td = datetime.now()
                end_date = td
            else:
                end_date = datetime.strptime(
                    assign.end_date, '%Y-%m-%d')
            end_date = end_date + relativedelta(months=1)
            end_date = end_date + relativedelta(day=1)
            end_date = end_date.date()

            if start_date <= start and end_date >= end:
                return assign.assignee_id
        return None

    @api.multi
    def generate_depreciation_lines(self):
        """
        Generate depreciation lines for asset.
        """
        depreciation_line_env = self.env["depreciation.lines"]
        for record in self:
            current_value = record.purchased_price
            period = int(record.depreciation_period)
            if period == 0:
                continue
            if not record.purchased_date or not record.purchased_price:
                raise Warning(_("Purchasing information are not correct."))
            # split date
            start = datetime.strptime(record.purchased_date, '%Y-%m-%d').date()
            end = start + relativedelta(months=period)
            if record.depreciation_line_ids:
                line_ids = str(tuple(record.depreciation_line_ids.ids))
                self._cr.execute(
                    """
                    DELETE FROM depreciation_lines WHERE id in %s
                    """ % line_ids
                )
            flag = start
            while flag <= end and current_value:
                # Reset amount every month
                amount = record.depreciation_amount or \
                    (record.purchased_price / period)
                amount = int(amount)
                # compute month_start & month_end
                first_date = flag + relativedelta(day=1)
                end_date = first_date + relativedelta(months=1) - \
                    relativedelta(days=1)
                month_start = max(start, first_date)
                month_end = min(end, end_date)
                delta_days = (month_end - month_start).days + 1
                # Compute depreciation of month
                if first_date != month_start or end_date != month_end:
                    days_of_month = (end_date - first_date).days
                    depre_in_day = 1.0 * amount / days_of_month
                    depre_in_month = depre_in_day * delta_days
                    amount = int(depre_in_month)
                flag = end_date + relativedelta(days=1)
                if month_start <= month_end:
                    assignee = self.get_asset_assignee(
                        record, month_start, month_end)
                    vals = {
                        'asset_id': record.id,
                        'employee_id': assignee and assignee.id or None,
                        'start_date': month_start,
                        'end_date': month_end,
                    }
                    if current_value >= amount:
                        vals['amount'] = amount
                        current_value = current_value - amount
                    elif current_value > 0:
                        vals['amount'] = current_value
                        current_value = 0
                    depreciation_line_env.create(vals)

    @api.model
    def create(self, vals):
        """
        - Create new asset_assignee with start_date and leave end_date empty
        """
        assign_history_env = self.env['asset.assign.history']
        res = super(TmsAsset, self).create(vals)
        self.generate_depreciation_lines()
        if 'assignee_id' not in vals:
            return res
        # Create new Asset Assign History for new asset
        if res.assignee_id and res.assignee_id.id:
            new_assign_history_vals = {
                'asset_id': res.id,
                'assignee_id': res.assignee_id.id,
                'start_date': res.assigning_date or datetime.now().date(),
                'end_date': None
            }
            assign_history_env.create(new_assign_history_vals)
        return res

    @api.multi
    def write(self, vals):
        """
        Creating new Asset Assign History when reassign new Owner to Asset:
        - Checking if asset has previous owner:
            + If yes, search asset_assign_history and set end_date for it
        - Create new Asset Assign History with start_date, leave end_date empty
        """
        for record in self:
            # Check if need re generate depreciation
            is_regenerate_depreciation = False
            depreciation_relation = [
                'assignee_id', 'depreciation_period', 'purchased_price']
            for i in depreciation_relation:
                if i in vals:
                    is_regenerate_depreciation = True

            # Get old assignee if reassigne asset for new employee
            old_assignee = self.assignee_id or None

            super(TmsAsset, self).write(vals)

            if is_regenerate_depreciation:
                record.generate_depreciation_lines()

            # Asset is reassigned when set new assignee
            if 'assignee_id' in vals:
                assigning_date = datetime.strftime(
                    datetime.now().date(), '%Y-%m-%d')
                if 'assigning_date' in vals and vals['assigning_date']:
                    assigning_date = vals['assigning_date']
                record.re_assigne_asset(
                    old_assignee and old_assignee.id or None,
                    record.assignee_id and record.assignee_id.id or None,
                    assigning_date)
        return True

    @api.multi
    def assigne_back_trobz(self):
        """
        Reassign asset back to trobz
        """
        for asset in self:
            asset.assignee_id = None

    @api.multi
    def re_assigne_asset(self, old_assignee_id, assignee_id, assigning_date):
        """
        (self, int, int, datetime) ->
        Reassign asset to new assignee on assigning_date. if no assignee_id,
        asset is assigned back to trobz, ignore create assign history
        """
        assign_history_env = self.env['asset.assign.history']
        for asset in self:
            # If asset has previous assignee, find that old assign history and
            # set end_date of assign history as previous date of assigning_date
            if old_assignee_id:
                old_assign_history = assign_history_env.search(
                    [('asset_id', '=', asset.id),
                     ('assignee_id', '=', old_assignee_id),
                     ('end_date', '=', None)])
                if old_assign_history:
                    assigning_date = datetime.strptime(
                        assigning_date, '%Y-%m-%d')
                    previous_date = assigning_date - timedelta(days=1)
                    old_assign_history[0].end_date = previous_date
            # Create new Asset Assign History if asset has new assignee
            if assignee_id:
                new_assign_history_vals = {
                    'asset_id': asset.id,
                    'assignee_id': asset.assignee_id.id,
                    'start_date': asset.assigning_date,
                    'end_date': None
                }
                assign_history_env.create(new_assign_history_vals)
