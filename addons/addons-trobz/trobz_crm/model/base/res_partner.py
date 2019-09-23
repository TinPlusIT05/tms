# -*- coding: utf-8 -*-
from openerp import models, api, fields


class res_partner(models.Model):

    _inherit = 'res.partner'

    # F#13145 In the tree view of partner,
    # replace the column Phone by "Phone/Mobile"

    @api.multi
    def _get_full_phone(self):
        for record in self:
            full_phone = []
            if record.phone:
                full_phone.append(record.phone)
            if record.mobile:
                full_phone.append(record.mobile)
            record.phone_mobile = " / ".join(full_phone) if full_phone else ''

    @api.depends('is_company')
    def _get_title_domain(self):
        """
        Use for the domain on field Title:
        - NOT Is Company: titles with type `contact`
        - Is Company: titles with type `partner`
        """
        for record in self:
            if record.is_company:
                record.title_domain = 'partner'
            else:
                record.title_domain = 'contact'

    phone_mobile = fields.Char(
        compute='_get_full_phone', string='Phone/Mobile')

    event_ids = fields.One2many(
        comodel_name='trobz.crm.event', inverse_name='partner_id',
        string='Events'
    )
    lead_ids = fields.One2many(
        comodel_name='crm.lead', inverse_name='partner_id', string='Leads'
    )
    skype_contact = fields.Char('Skype Contact', size=64)
    linkedin_profile = fields.Char('Linkedin Profile', size=64)
    create_uid = fields.Many2one(
        comodel_name='res.users', string='Creator')
    create_date = fields.Datetime('Creation Date')
    prospect = fields.Boolean(
        'Prospect', help="Check this box if this contact is a prospect.")
    business_sector_id = fields.Many2one(
        comodel_name='trobz.crm.business.sector', string='Business Sector'
    )
    title_domain = fields.Selection(
        [('contact', 'Contact'), ('partner', 'Partner')],
        'Title Domain', compute='_get_title_domain', store=True
    )

    @api.onchange('customer')
    def check_cutomer(self):
        if self.customer:
            self.prospect = False

    @api.onchange('prospect')
    def check_prospect(self):
        if self.prospect:
            self.customer = False

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        if self.parent_id:
            self.customer = self.parent_id.customer
            self.prospect = self.parent_id.prospect
            self.supplier = self.parent_id.supplier

    # Can not migrate this function because onchange_state is called from Odoo
    def onchange_state(self, cr, uid, ids, state_id, context=None):
        if state_id:
            country_id = self.pool.get('res.country.state').browse(
                cr, uid, state_id, context).country_id.id
            return {'value': {'country_id': country_id}}
        return {}

    @api.model
    def default_get(self, fields):
        ctx = self._context and self._context.copy() or {}
        res = super(res_partner, self).default_get(fields)
        res.update({
            'is_company': False,
        })

        # F#12640 : Update Related User and company for Partner.contact
        # Get customer/prospect/supplier like company
        if ctx.get('default_parent_id', False):
            parent_obj = self.browse(ctx['default_parent_id'])
            res.update({
                'customer': parent_obj.customer,
                'prospect': parent_obj.prospect,
                'supplier': parent_obj.supplier,
                'use_parent_address': True,
            })

        return res

    @api.multi
    def write(self, vals):
        context = self._context and self._context.copy() or {}
        context.update({'from_partner': 1})
        res = super(res_partner, self).write(vals)
        # F#12640: For partner set as is_company, when updating the fields
        # ‘Customer/Supplier/Prospect’, automatically set the same value
        # on the contacts of that company.
        child_new_vals = {}
        if 'customer' in vals:
            child_new_vals['customer'] = vals.get('customer', False)
        if 'prospect' in vals:
            child_new_vals['prospect'] = vals.get('prospect', False)
        if 'supplier' in vals:
            child_new_vals['supplier'] = vals.get('supplier', False)

        if child_new_vals:
            for parent_obj in self:
                if parent_obj.is_company and parent_obj.child_ids:
                    parent_obj.child_ids.write(child_new_vals)
        return res

    @api.multi
    def name_get(self):
        context = self._context or {}
        if not self:
            return []
        res = []
        for r in self:
            if context.get('contact_display', 'contact') == 'partner' and \
                    r.parent_id:
                res.append((r.id, r.parent_id.id))
            else:
                res.append((r.id, r.name or '/'))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        context = dict(self._context)
        if 'crm_partner_id' in context:
            crm_partner_id = context.get('crm_partner_id', False)
            if not crm_partner_id:
                args = [('id', 'in', [])]
            else:
                partners = self.env['res.partner'].search(
                    [('id', '=', crm_partner_id)])
                if partners:
                    partner = partners[0]
                    contact_ids = [contact.id for contact in partner.child_ids]
                    args = [('id', 'in', contact_ids)]

        return super(res_partner, self).name_search(
            name=name, args=args, operator=operator, limit=limit)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
