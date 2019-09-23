from openerp import models, fields, api
from datetime import datetime
from openerp import SUPERUSER_ID
from openerp.exceptions import Warning


class HrEquipmentRequest(models.SecureModel):

    _name = 'hr.equipment.request'
    _description = 'HR Equipment Request'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', store=True, compute="_generate_name")
    category_id = fields.Many2one('hr.equipment.category', string='Category',
                                  readonly=True,
                                  track_visibility='onchange',
                                  states={'draft': [('readonly', False)]})
    state = fields.Selection(string='State',
                             selection=[('draft', 'Draft'),
                                        ('confirmed', 'Confirmed'),
                                        ('request_apprvd', 'Request Approved'),
                                        ('purchase_apprvd',
                                         'Purchase Approved'),
                                        ('purchased', 'Purchased'),
                                        ('cancel', 'Canceled')],
                             default='draft',
                             track_visibility='onchange')
    request_date = fields.Date(string='Request Date', required=True,
                               default=fields.Date.today(),
                               readonly=True,
                               track_visibility='onchange',
                               states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one(
        'hr.employee', string='Employee',
        required=True, readonly=True, track_visibility='onchange',
        states={'draft': [('readonly', False)]})
    job_id = fields.Many2one('hr.job', string='Position',
                             readonly=True,
                             related='employee_id.job_id')
    reason = fields.Text(string='Reason', required=True, readonly=True,
                         track_visibility='onchange',
                         states={'draft': [('readonly', False)]})
    model_req = fields.Text(
        string='Model', required=True, readonly=True,
        track_visibility='onchange',
        states={'draft': [('readonly', False)]})
    est_price = fields.Float(string='Estimated Price',
                             help='This price is the price that get from\
several website or given by employee. It is not official price from our \
supplier.',
                             track_visibility='onchange',
                             readonly=True,
                             states={'draft': [('readonly', False)]})
    financial_aggr = fields.Secure(multiline=True,
                                   track_visibility='onchange',
                                   string='Financial Agreement',
                                   security="_security_https_password")
    partial_apprv = fields.Boolean(
        string='Partial Approval',
        default=False, readonly=True, track_visibility='onchange',
        states={'draft': [('readonly', False)],
                'confirmed': [('readonly', False)],
                'request_apprvd': [('readonly', False)]})
    trobz_contr_amt = fields.Float(string='Trobz Contribution Amount')
    schd_pur_date = fields.Date(string='Scheduled Purchase Date',
                                readonly=True,
                                track_visibility='onchange',
                                states={'draft': [('readonly', False)],
                                        'confirmed': [('readonly', False)]},
                                help='Date at which it is approved to buy\
 equipment.', )
    # purchase_price is Marked after Purchased Approved
    purchase_price = fields.Float(string='Purchase Price', readonly=True,
                                  track_visibility='onchange',
                                  states={'draft': [('readonly', False)],
                                          'confirmed': [('readonly', False)],
                                          'request_apprvd':
                                          [('readonly', False)]})
    supp_invoice = fields.Char(string='Supplier Invoice Ref TFA',
                               readonly=True,
                               track_visibility='onchange',
                               states={'draft': [('readonly', False)],
                                       'confirmed': [('readonly', False)],
                                       'request_apprvd': [('readonly', False)],
                                       'purchase_apprvd': [('readonly', False)]
                                       })
    delivery_date = fields.Date(string='Delivery Date', readonly=True,
                                track_visibility='onchange',
                                states={'draft': [('readonly', False)],
                                        'confirmed': [('readonly', False)],
                                        'request_apprvd':
                                        [('readonly', False)],
                                        'purchase_apprvd':
                                        [('readonly', False)]
                                        })
    invoicing_date = fields.Date(
        string='Invoicing Date',
        track_visibility='on_change',
        help="Date at which the vendor invoice is received at Trobz"
    )
    extra_info = fields.Text(
        string='Extra Information', track_visibility='onchange')
    schd_pur_month = fields.Date(string="Scheduled Purchase Month",
                                 compute="_get_month", store=True,
                                 track_visibility='onchange')
    supplier_code = fields.Char(string="Supplier Code")

    def _get_month(self):
        """
            Get Months for Filter
        """
        f = '%Y-%m-%d'
        for x in self:
            x.schd_pur_month = str(
                datetime.strptime(x.schd_pur_date, f).month)

    @api.model
    @api.onchange('purchase_price')
    def _update_when_full_approval(self):
        """
            Upgrade Contributed Amount whenever the Request is fully Approved
        """
        if not self.partial_apprv:
            self.trobz_contr_amt = self.purchase_price

    @api.depends('request_date', 'employee_id')
    def _generate_name(self):
        """"
            Generate Name for Request
            {Employee_Name}-{Request_date YYYY-MM-DD}
        """
        for x in self:
            if x.employee_id:
                x.name = x.employee_id.name + "-Request Date " + x.request_date
            else:
                x.name = "New Request"

    @api.multi
    def write(self, vals):
        res = super(HrEquipmentRequest, self).write(vals)
        if not self.partial_apprv and 'purchase_price' in vals:
            self.trobz_contr_amt = vals['purchase_price'] or 0
        return res
