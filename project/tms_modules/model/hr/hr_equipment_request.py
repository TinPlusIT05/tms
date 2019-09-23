# -*- coding: utf-8 -*-
from openerp import models, fields, api, SUPERUSER_ID
from openerp.exceptions import Warning
from lxml import etree
from openerp.osv.orm import setup_modifiers

DEPRECATION_PERIOD = [
    ('0', 'None'),
    ('6', '6 months'),
    ('12', '12 months'),
    ('24', '2 years'),
    ('36', '3 years')
]


class HrEquipmentRequest(models.SecureModel):

    _inherit = 'hr.equipment.request'
    _order = 'request_date'

    benefit_start = fields.Date(
        string='Benefit Start Date',
        compute='_compute_benefit',
        store=True)
    balance_benefit = fields.Float(
        string='Balance Benefit',
        compute='_compute_benefit',
        store=True)
    supplier = fields.Many2one(string="Supplier",
                               comodel_name="res.partner",
                               domain="[('supplier', '=', True)]")
    number = fields.Integer(
        string="# Items", default=1,
        help="Number of Item which is requested."
        "If there is larger than 1, "
        "there will automatically create assets record "
        "has same information but separated by"
        " internal code.")
    type = fields.Selection(
        [
            ('trobz', "Trobz's Assets"),
            ('personal', "Personal Asset")],
        string="Asset Type", default='personal')
    employee_id = fields.Many2one(
        'hr.employee', string='Employee',
        required=False, readonly=True, track_visibility='onchange',
        default=lambda self: self.env.user.employee_id.id,
        states={'draft': [('readonly', False)]})
    asset_ids = fields.One2many(
        string="Assets",
        comodel_name="tms.asset",
        inverse_name="request_id")
    depreciation_period = fields.Selection(
        DEPRECATION_PERIOD, string="Depreciation Period", default='0')
    total_amount = fields.Float(
        "Total Estimate Amount", compute='_compute_total_amount')
    est_price = fields.Float(
        string='Estimated Price',
        help='This price is the price that get from\
        several website or given by employee. It is not official price from \
        our supplier.', store=True,
        track_visibility='onchange',
        readonly=True,
        states={'draft': [('readonly', False)]})
    delivery_date = fields.Date(
        string='Delivery Date', track_visibility='onchange',
        require=False, readonly=True,
        states={'request_apprvd': [('required', False), ('readonly', False)],
                'purchase_apprvd': [('required', True), ('readonly', False)]})
    schd_pur_date = fields.Date(
        string='Scheduled Purchase Date', readonly=True,
        track_visibility='onchange',
        states={'draft': [('readonly', False)],
                'confirmed': [('readonly', False)]},
        help='Date at which it is approved to buy equipment', )
    request_date = fields.Date(
        string='Request Date', required=True,
        default=lambda self: fields.Date.today(),
        readonly=True, track_visibility='onchange',
        states={'draft': [('readonly', True)]})
    unit_price = fields.Float(
        string='Unit Purchase Price', readonly=False, require=False,
        track_visibility='onchange',
        states={'purchase_apprvd': [('required', True)]},
        help="Price of each items")
    # Because of wrong in data, replace fields purchase_price by
    # total_purchase_amount. Data will be copy on postobject
    total_purchase_amount = fields.Float(
        string='Total Purchase Amount', require=False,
        compute='_compute_total_purchase_amount', store=True,
        track_visibility='onchange',
        states={'purchase_apprvd': [('required', True)]},
        help="Total cost to purchase all items for this request"
        " (#Item * Unit Purchase Price)")
    purchase_price = fields.Float(
        string='Total Purchase Amount', readonly=False, require=False,
        track_visibility='onchange',
        states={
            'purchase_apprvd': [('required', True)]
        },
        help="Total cost to purchase all items for this request"
        " (#Item * Unit Purchase Price)")
    invoicing_date = fields.Date(
        string='Invoicing Date',
        track_visibility='on_change',
        help="Date at which the vendor invoice is received at Trobz",
        groups="base.group_hr_manager"
    )
    supp_invoice = fields.Char(
        string='Supplier Invoice Ref TFA',
        readonly=False, require=False,
        track_visibility='onchange',
        states={
            'purchase': [('readonly', True)],
            'cancel': [('readonly', True)]
        },
        groups="base.group_hr_manager")
    trobz_contr_amt = fields.Float(
        string='Trobz Contribution Amount',
        help="This is amount that Trobz contribute to buy asset. If request is"
        " partial approved, this value is input manually. Else, this value "
        "is equal purchase price")
    warning = fields.Text('Warning',
        compute='compute_equipment_request_warning',
        help='Raise waring if there is any information conflict with assets')
    state = fields.Selection(string='State',
                             selection=[('draft', 'Draft'),
                                        ('confirmed', 'Confirmed'),
                                        ('request_apprvd', 'Request Approved'),
                                        ('purchase_apprvd',
                                         'Purchase Approved'),
                                        ('purchased', 'Purchased'),
                                        ('cancel', 'Canceled')],
                             default='draft',
                             track_visibility='onchange',
                             help='''+ Draft: Employee is creating his request.
+ Confirmed: Employee confirms his request.
+ Request Approved: user with TMS HR Manager will approve the request,\
 and quotation can be requested to supplier(s).
+ Purchase Approved: user with TMS HR Manager will approve the PO and PO can\
 be done on Scheduled Purchase Date.
+ Purchased: The Equipment has been purchased.\n+ Canceled: The request is\
 canceled.''')

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
        Onchange benefit start and balance_benefit on employee
        """
        if self.employee_id:
            self.benefit_start = self.employee_id.benefit_start
            self.balance_benefit = self.employee_id.balance_benefit

    @api.depends('est_price', 'number')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.number * rec.est_price

    @api.depends('unit_price', 'number')
    def _compute_total_purchase_amount(self):
        for rec in self:
            rec.total_purchase_amount = rec.number * rec.unit_price

    @api.depends('employee_id')
    def _compute_benefit(self):
        for rec in self:
            if not rec.employee_id:
                continue
            rec.balance_benefit = rec.employee_id.balance_benefit
            rec.benefit_start = rec.employee_id.benefit_start

    @api.multi
    def compute_equipment_request_warning(self):
        """
        Raise warning if conflict on:
        - unit price of asset and request
        """
        for rec in self:
            if not rec.asset_ids:
                continue
            warnings = []
            for asset in rec.asset_ids:
                if asset.purchased_price != rec.unit_price:
                    warnings.append(
                        'Conflict between %s and %s' % (
                            rec.name, asset.internal_code))
            rec.warning = '\n'.join(warnings)

    @api.constrains('number')
    def _constrains_number(self):
        for record in self:
            if record.number < 1:
                raise Warning('Invalid number of purchasing items!')

    @api.constrains('est_price', 'unit_price')
    def _constrains_prices(self):
        for record in self:
            if record.est_price < 0:
                raise Warning('Estimate price is invalid!')
            if record.unit_price < 0:
                raise Warning('Unit price is invalid!')
            # Update purchased_price on asset follow unit_price on request
            if not record.asset_ids:
                continue
            if not record.partial_apprv:
                record.trobz_contr_amt = record.total_purchase_amount
            updated_vals = {
                'purchased_price': record.unit_price,
                'trobz_contribution': record.trobz_contr_amt / record.number
            }
            record.asset_ids.write(updated_vals)

    @api.onchange('type')
    def onchange_partial_apprv(self):
        if self.type == 'trobz':
            self.partial_apprv = False
            self.employee_id = None

    @api.onchange('partial_apprv', 'total_purchase_amount')
    def onchange_asset_type(self):
        if self.partial_apprv:
            self.type = 'personal'
        if not self.partial_apprv:
            self.trobz_contr_amt = self.total_purchase_amount

    @api.constrains('total_purchase_amount')
    def onchange_total_purchase_amount(self):
        if self.total_purchase_amount >= 0.0:
            if not self.partial_apprv:
                self.trobz_contr_amt = self.total_purchase_amount

    @api.multi
    def button_confirm(self):
        return self.write({'state': 'confirmed'})

    @api.multi
    def button_request(self):
        for rec in self:
            if not rec.schd_pur_date:
                raise Warning(
                    'Schedule Purchase Date of %s is empty!' % rec.name)
            if rec.partial_apprv and rec.trobz_contr_amt <= 0.0:
                raise Warning(
                    'Trobz Contribution Amount of %s is invalid!' % rec.name)
            self.write({'state': 'request_apprvd'})

    @api.multi
    def button_purchase(self):
        return self.write({'state': 'purchase_apprvd'})

    @api.multi
    def button_done(self):
        for rec in self:
            if not rec.delivery_date:
                raise Warning(
                    'Delivery Date of %s is empty!' % rec.name)
            if rec.total_purchase_amount <= 0.0:
                raise Warning(
                    'Purchase Price of %s is invalid!' % rec.name)
            rec.write({'state': 'purchased'})
            # Automatically creating asset(s) of request
            rec.button_force_create_assets()
        return True

    @api.multi
    def button_cancel(self):
        if self.state != 'confirmed':
            if self.env['res.users'].has_group('base.group_hr_manager'):
                return self.write({'state': 'cancel'})
            else:
                return True
        return self.write({'state': 'cancel'})

    @api.multi
    def button_draft(self):
        for rec in self:
            if rec.state == 'purchased':
                raise Warning(
                    'Request %s has been purchased!' % rec.name)
            rec.partial_apprv = False
            rec.trobz_contr_amt = 0
            rec.total_purchase_amount = 0
            rec.write({'state': 'draft'})

    @api.multi
    def button_force_create_assets(self):
        '''
        Create assets of request. Number of assets generated will be number of
        items of each request.
        The conditions is the request has no assets created before.
        '''
        asset_env = self.env['tms.asset']
        for record in self:
            if len(record.asset_ids) > 0:
                # TODO Check and create  asset which is not genrerated
                # Ex: If there is 6 items, 3 assets already created, create
                # 3 remain assets
                raise Warning("The assets for this request has been created. "
                              "Please try to edit on menu `Assets` instead "
                              "changing at here.")
            vals = {
                'category_id': record.category_id.id,
                'type': record.type,
                'request_id': record.id,
                'purchased_date': record.delivery_date,
                'purchased_price': record.unit_price,
                'supplier_id': record.supplier.id,
                'depreciation_period': record.depreciation_period,
                'assigning_date': record.delivery_date,
                'trobz_contribution': record.trobz_contr_amt / record.number,
            }
            if record.type == 'personal':
                vals.update(
                    {
                        'owner_id': record.employee_id.id,
                        'assignee': record.employee_id.id,
                    })

            for _ in range(record.number):
                asset_env.create(vals)

    @api.depends('request_date', 'employee_id')
    def _generate_name(self):
        """"
        Personal Request
            Generate Name for Request
            {Employee_Name}-{Request_date YYYY-MM-DD}
        Trobz Request
            {Trobz}-{Request_date YYYY-MM-DD}
        """
        for rec in self:
            if rec.employee_id:
                rec.name = rec.employee_id.name + \
                    "-Request Date " + rec.request_date
            else:
                rec.name = "Trobz" + "-Request Date " + rec.request_date

    @api.multi
    def write(self, vals):
        res = super(HrEquipmentRequest, self).write(vals)
        change_state = (
            'request_apprvd', 'purchase_apprvd', 'purchased', 'cancel')
        if 'state' in vals:
            if vals['state'] == 'confirmed':
                self.send_email_confirm_equipment_request(self.ids[0])
            elif vals['state'] in change_state:
                self.send_email_change_equipment_request(self.ids[0])
        return res

    def send_email_confirm_equipment_request(self, request_id):
        """
        When an equipment request is confirmed, send email to HR
        """
        if not request_id:
            return
        request = self.env['hr.equipment.request'].search(
            [('id', '=', request_id)], limit=1)
        hr_mail = self.env.ref(
            'tms_modules.email_hr',
            raise_if_not_found=False).value
        # Send email
        template = self.env.ref(
            "tms_modules.email_template_notify_hr_equipment_request_confirmed")
        if template:
            template.with_context(
                subject='[New Equipment Request]' + request.name,
                request=request,
                email_to=hr_mail).send_mail(request.id, force_send=True)

    def get_request_user_name(self, request_id):
        rq = self.env['hr.equipment.request'].search([('id', '=', request_id)])
        return rq.employee_id.name or ''

    def generate_equipment_request_url(self, request_id):
        """
        (self, int) -> string
        Generate url of equipment request whick has id as request_id
        """
        baseurl = self.env['ir.config_parameter'].get_param('web.base.url')
        ex_url = 'web?#id=%s&view_type=form&model=hr.equipment.request' + \
            '&menu_id=%s&action=%s'
        menu_id = self.env.ref(
            'it_equipment_bonus.menu_hr_benefit_equipment_request').id
        action_id = self.env.ref(
            'it_equipment_bonus.action_hr_equipment_request').id
        url = baseurl + '/' + ex_url % (request_id, menu_id, action_id)
        return url

    def send_email_change_equipment_request(self, request_id):
        """
        When an equipment request is approve, approve to purchase, purchased,
        send email to HR Team and requester
        """
        if not request_id:
            return
        request = self.env['hr.equipment.request'].search(
            [('id', '=', request_id)], limit=1)
        hr_mail = self.env.ref(
            'tms_modules.email_hr',
            raise_if_not_found=False).value
        # Send email
        template = self.env.ref(
            "tms_modules.email_template_notify_equipment_request_change_state")
        content = self.get_equipment_request_change_email_content(request_id)
        if request.employee_id:
            email_to = hr_mail + "," + request.employee_id.user_id.email
        else:
            email_to = hr_mail
        if template:
            template.with_context(
                subject='[Equipment Request Change]' + request.name,
                request=request,
                content=content,
                email_to=email_to).send_mail(request.id, force_send=True)

    def get_equipment_request_change_email_content(self, request_id):
        """
        Generate the email content of email "Daily Activities"
        """
        request = self.env['hr.equipment.request'].search(
            [('id', '=', request_id)], limit=1)
        body = """
<p>
    The equipment request %s is %s.
</p>
<p>
%s
</p>
"""
        request_name = request.name
        state_str = ''
        cont = ''
        if request.state == 'request_apprvd':
            state_str = 'approved'
            cont = \
                ' The scheduled purchase date is %s.' % request.schd_pur_date
        elif request.state == 'purchase_apprvd':
            state_str = 'approved to purchase'
            cont = '<p>- The supplier is %s </p>' % request.supplier_code
            cont += '<p>- Total Purchase Amount is %s </p>' % request.\
                total_purchase_amount
        elif request.state == 'purchased':
            state_str = 'purchased'
            cont = 'The estimated delivery date is %s.' % request.delivery_date
        elif request.state == 'cancel':
            state_str = 'cancelled'
        return body % (request_name, state_str, cont)

    @api.multi
    def open_employee_assets(self):
        """
        Open tree view of all assets of employee of request
        """
        owner_id = len(self) > 0 and self[0].employee_id.id or False
        if owner_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Assets',
                'res_model': 'tms.asset',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'context': {'search_default_owner_id': owner_id},
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Assets',
                'res_model': 'tms.asset',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'domain': [('owner_id', '=', False)],
            }

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False,
                        submenu=False):
        res = super(HrEquipmentRequest, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if not self.env['res.users'].has_group('base.group_hr_manager'):
            if view_type in {'tree', 'form'}:
                doc = etree.XML(res['arch'])
                if res['type'] == 'form':
                    nodes = doc.xpath("//field")
                    for node in nodes:
                        node.set('attrs', "{'readonly': [('state', 'in', ['purchased', 'cancel'])]}")
                        setup_modifiers(node, None)
                res['arch'] = etree.tostring(doc)
        return res

    # ========================================================================
    # OTHER FUNCTIONS
    # ========================================================================
    @api.multi
    def _security_https_password(self):
        """
        @param requests: recordset hr.equipment.request
        @return:
            - tms_modules.group_profile_tms_admin, return True
            - tms_modules.group_profile_fc_admin, return True
            - tms_modules.group_profile_hr_officer, return True
            - The rest, return False
        """
        if self._uid == SUPERUSER_ID:
            return True
        mod_obj = self.env['ir.model.data']
        user_profile = self.env.user.group_profile_id.id
        fn = mod_obj.get_object_reference
        group_admins = [
            fn('tms_modules', 'group_profile_tms_admin')[1],
            fn('tms_modules', 'group_profile_fc_admin')[1],
            fn('tms_modules', 'group_profile_hr_officer')[1]]
        # If this user is a Sysadmin and has full access
        if user_profile in group_admins:
            return True
        return False
