# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning
from datetime import datetime
from dateutil import tz  # @UnresolvedImport
from openerp.addons.crm import crm


class trobz_crm_lead(models.Model):
    _inherit = "crm.lead"
    _order = "priority desc, create_date desc"
    _description = "Opportunity"

    _track = {'stage_id': {}}

    @api.model
    def read_group(self, domain, fields, groupby, offset=0,
                   limit=None, orderby=False, lazy=True):
        # Order by Probability Percentage when group by Probability
        if 'probability_id' in groupby:
            orderby = 'probability_id DESC' + \
                (orderby and (',' + orderby) or '')
        return super(trobz_crm_lead, self).read_group(
            domain, fields,
            groupby, offset=0,
            limit=limit,
            orderby=orderby,
            lazy=lazy)

    @api.multi
    def name_get(self):
        """
        Lead name = {Subject}[{Business sector}]
        """
        result = []
        for lead in self:
            lead_name = lead.name or ''
            sector_name = lead.partner_id and \
                lead.partner_id.business_sector_id.name or ''
            res_name = lead_name + ' [' + sector_name + ']'
            if not sector_name:
                res_name = lead_name
            result.append((lead.id, res_name))
        return result

    @api.depends('event_ids', 'event_ids.name', 'event_ids.state',
                 'event_ids.start_date', 'event_ids.start_datetime')
    def _get_next_event_info(self):
        for lead in self:
            date_action = False
            title_action = False
            for event in lead.event_ids:
                if event.state != 'open':
                    continue
                if not date_action and not title_action:
                    date_action = event.start_date or event.start_datetime
                    title_action = event.name or ''
                    continue
                if (event.start_date and date_action > event.start_date) or \
                        (event.start_datetime and
                         date_action > event.start_datetime):
                    date_action = event.start_date or event.start_datetime
                    title_action = event.name or ''
            lead.date_action = date_action or False
            lead.title_action = title_action or False

    @api.depends('name', 'partner_id', 'partner_id.name', 'contact_name')
    def _get_full_name_subject(self):
        for lead in self:
            full_name = ''
            if lead.partner_id:
                full_name = '[%s] %s' % (
                    lead.partner_id.name, lead.name)
            else:
                full_name = lead.contact_name
            lead.full_name = full_name

    @api.depends('related_partner_address_ids',
                 'related_partner_address_ids.name')
    def _get_full_related_contact_name(self):
        for lead in self:
            full_name = ''
            related_partners_address = lead.related_partner_address_ids
            for related_partner in related_partners_address:
                full_name += ", " + related_partner.name \
                    if related_partner.name and full_name else related_partner.name
            # Ticket F#13040 if more than 100 characters, add the suffix " ..."
            lead.full_related_contact_name = full_name \
                if (len(full_name)) < 100 else full_name[0:100] + '...'

    @api.multi
    def _get_business_sector(self):
        '''
        Function to return the business sector as a suffix in
        square braquets: {subject} [{business_sector}]
        '''
        for lead in self:
            lead_name = lead.name or ''
            sector_name = lead.partner_id and \
                lead.partner_id.business_sector_id.name or ''
            res_name = lead_name + ' [' + sector_name + ']'
            if not sector_name:
                res_name = lead_name
            lead.subject_business_sector = res_name

    # Columns
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner',
        ondelete='set null', track_visibility='onchange',
        select=True, default='default_partner_id',
        help="Linked partner (optional). Usually created "
        "when converting the lead.",
        domain="[('is_company','=',True)]"
    )
    related_partner_address_ids = fields.One2many(
        related='partner_id.child_ids',
        comodel_name='res.partner', string='Contact', readonly=True
    )
    event_ids = fields.One2many(
        comodel_name='trobz.crm.event', inverse_name='lead_id', string='Events'
    )

    date_action = fields.Datetime(
        compute='_get_next_event_info', string='Next Action Date',
        store=True
    )
    title_action = fields.Char(
        compute='_get_next_event_info', string='Next Action',
        store=True
    )
    lost_reason_id = fields.Many2one(
        comodel_name='crm.lost.reason', string='Lost Reason'
    )

    full_name = fields.Char(
        compute='_get_full_name_subject',
        string='Full name', store=True
    )
    filter_todo = fields.Boolean(
        string='Filter Todo', default=False
    )

    full_related_contact_name = fields.Char(
        compute='_get_full_related_contact_name',
        string="Contact Names"
    )

    planned_revenue = fields.Float(
        string='Expected Workload', track_visibility='always'
    )
    probability_id = fields.Many2one(
        comodel_name='crm.lead.probability',
        string='Probability', default='default_probability'
    )
    main_contact = fields.Many2one(
        comodel_name='res.partner', string='Main Contact'
    )
    source_detail = fields.Char('Source detail')
    referred_by = fields.Many2one(
        comodel_name='res.partner', string='Referred by',
        domain="[('is_company','=',True),('customer','=',True)]"
    )

    business_sector_id = fields.Char(
        "Business Sector", related="partner_id.business_sector_id.name",
        store=True)

    subject_business_sector = fields.Char(
        compute='_get_business_sector',
        string='Subject')
    priority = fields.Selection(crm.AVAILABLE_PRIORITIES[::-1], 'Priority')

    @api.model
    def default_partner_id(self):
        return self._context.get('partner_id', False)

    @api.model
    def default_sales_team_id(self):
        sales_teams = self.env['crm.case.section'].search([])
        return sales_teams and sales_teams[0].id or False

    @api.model
    def default_probability(self):
        probability = self.env['crm.lead.probability'].search(
            [('name', '=', 'Medium')])
        if probability:
            return probability[0].id
        else:
            raise Warning(
                _('Warning!', '''No value "Medium" in Probability''')
            )

    @api.model
    def default_get(self, fields):
        ctx = self._context and self._context.copy() or {}
        res = super(trobz_crm_lead, self).default_get(fields)
        res.update({
            # We do not want to split lead and opportunity, by default we use
            # opportunity because the related stages are suitable for our
            # workflow.
            'section_id': self.default_sales_team_id(),
            'type': 'opportunity',
        })
        if ctx.get('partner_id', False):
            res['partner_id'] = ctx['partner_id']
        return res

    @api.model
    def redirect_opportunity_view(self, opportunity_id):
        '''
        Redirect to the new Opportunity view
        '''
        model_data_env = self.env['ir.model.data']

        # Get Opportunity views
        form_view = model_data_env.get_object_reference(
            'crm', 'crm_case_form_view_leads')
        tree_view = model_data_env.get_object_reference(
            'crm', 'crm_case_tree_view_oppor')
        return {
            'name': _('Opportunity'),
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'crm.lead',
            'domain': [('type', '=', 'opportunity')],
            'res_id': int(opportunity_id),
            'view_id': False,
            'views': [(form_view and form_view[1] or False, 'form'),
                      (tree_view and tree_view[1] or False, 'tree'),
                      (False, 'calendar'), (False, 'graph')],
            'type': 'ir.actions.act_window',
        }

    @api.model
    def create(self, vals):
        partner_id = vals.get('partner_id', False)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            vals.update({'partner_name': partner.name})
        vals['active'] = True
        res = super(trobz_crm_lead, self).create(vals)
        if partner_id:
            res.set_contact_info(partner_id)
        return res

    @api.multi
    def write(self, vals):
        """
        Update the Partner Lead Name with Partner name.
        Update the Leads' contact.
        Update active=False if stage is Won/Lost
        """
        ctx = self._context and self._context.copy() or {}
        partner_env = self.env['res.partner']
        stage_env = self.env['crm.case.stage']
        for lead in self:
            if ctx and ctx.get('from_partner', False) and \
                    len(vals.keys()) == 1 and 'partner_id' in vals:
                return True

            if vals.get('partner_id', False):
                partner = partner_env.browse(vals['partner_id'])
                vals['partner_name'] = partner and partner.name or ''
                vals.update(self.set_contact(vals['partner_id']))

            if vals.get('stage_id', False):
                stage = stage_env.browse(vals['stage_id'])
                if stage.name in ('Won', 'Lost'):
                    vals.update({'active': False})
            res = super(trobz_crm_lead, lead).write(vals)

        return res

    # Ticket #1099: Automatically set the partner's contact to lead's contact.
    @api.multi
    def set_contact(self, partner_id):
        partner_env = self.env['res.partner']
        partner = partner_env.browse(partner_id)
        partner_address_id = partner.address_get(['default'])

        if not partner_address_id:
            return True
        # The ID of the address.
        partner_address_id = partner_address_id['default']
        partner_address = partner_env.browse(partner_address_id)

        lead_contact_data = {
            'contact_name': partner_address.name,
            'title': partner_address.title.id,
            'street': partner_address.street,
            'street2': partner_address.street2,
            'zip': partner_address.zip,
            'city': partner_address.city,
            'state_id': partner_address.state_id.id,
            'country_id': partner_address.country_id.id,
            'email': partner_address.email,
            'email_from': partner_address.email,
            'phone': partner_address.phone,
            'fax': partner_address.fax,
            'mobile': partner_address.mobile,
            'partner_name': partner.name,
            # skype_contact and linkedin_profile are not in the address info.
        }
        return lead_contact_data

    @api.multi
    def set_contact_info(self, partner_id):
        """
        Set the contact info of leads to their associated partner's
        contact info.
        @param overwrite: If the lead's contact info is existed, this function
        will check this param.
        If it set to true, current lead contact will be overwritten. Otherwise,
        it will be preserved.
        """
        partner_env = self.env['res.partner']
        partner = partner_env.browse(partner_id)
        partner_address_id = partner.address_get(['default'])

        if not partner_address_id:
            return True
        # The ID of the address.
        partner_address_id = partner_address_id['default']
        partner_address = partner_env.browse(partner_address_id)

        lead_contact_data = {
            'contact_name': partner_address.name,
            'title': partner_address.title.id,
            'street': partner_address.street,
            'street2': partner_address.street2,
            'zip': partner_address.zip,
            'city': partner_address.city,
            'state_id': partner_address.state_id.id,
            'country_id': partner_address.country_id.id,
            'email': partner_address.email,
            'email_from': partner_address.email,
            'phone': partner_address.phone,
            'fax': partner_address.fax,
            'mobile': partner_address.mobile,
            'partner_name': partner.name,
            # skype_contact and linkedin_profile are not in the address info.
        }
        self.write(lead_contact_data)
        return True

    # Ticket #1099
    @api.multi
    def button_refresh_lead_contact(self):
        """
        Refresh the contacts of given leads.
        """
        for lead in self:
            if lead.partner_id:
                lead.set_contact_info(lead.partner_id.id)

    @api.multi
    def button_higher_priority(self):
        for lead in self:
            if int(lead.priority) < 4:
                vals = {'priority': str(int(lead.priority) + 1)}
                lead.write(vals)
        return True

    @api.multi
    def button_lower_priority(self):
        for lead in self:
            assert lead.priority > 0
            vals = {'priority': str(int(lead.priority) - 1)}
            lead.write(vals)
        return True

    @api.multi
    def button_higher_probability(self):
        probability = self.env['crm.lead.probability'].search(
            [], order='probability_percentage ASC')
        probability_ids = probability and probability.ids or False
        for lead in self:
            probability_id = False
            index = lead.probability_id and probability_ids.index(
                lead.probability_id.id) or False
            if not lead.probability_id:
                probability_id = probability_ids[0]
            elif index + 1 < len(probability):
                probability_id = probability_ids[index + 1]
            if probability_id:
                lead.probability_id = probability_id
        return True

    @api.multi
    def button_lower_probability(self):
        probability = self.env['crm.lead.probability'].search(
            [], order='probability_percentage ASC')
        probability_ids = probability and probability.ids or False
        for lead in self:
            probability_id = False
            index = lead.probability_id and probability_ids.index(
                lead.probability_id.id) or False
            if not lead.probability_id:
                probability_id = probability_ids[0]
            elif index - 1 >= 0:
                probability_id = probability_ids[index - 1]
            if probability_id:
                lead.probability_id = probability_id
        return True

    def get_formview_id(self, cr, uid, form_id, context=None):
        obj = self.browse(cr, uid, form_id, context=context)
        if obj.type == 'opportunity':
            _, view_id = \
                self.pool.get('ir.model.data').get_object_reference(
                    cr, uid, 'crm', 'crm_case_form_view_leads')
        else:
            view_id = super(trobz_crm_lead, self).get_formview_id(
                cr, uid, form_id, context=context)
        return view_id

    @api.cr_uid_ids_context
    def message_post(self, cr, uid, thread_id, body='', subject=None,
                     type='notification', subtype=None, parent_id=False,
                     attachments=None, context=None, content_subtype='html',
                     **kwargs):
        if context is None:
            context = {}
        crm_lead_obj = self.pool['crm.lead']
        crm_lead = crm_lead_obj.browse(cr, uid, thread_id, context=context)
        if crm_lead:
            subject = crm_lead.full_name
        return super(trobz_crm_lead, self).message_post(
            cr, uid, thread_id, body=body, subject=subject, type=type,
            subtype=subtype, parent_id=parent_id, attachments=attachments,
            context=context, content_subtype=content_subtype, **kwargs)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        is_filter_todo = False
        for idx, arg in enumerate(args):
            if arg[0] == 'filter_todo':
                is_filter_todo = True
                del args[idx]
                break

        user_tz = self._context.get('tz', False)
        cr = self._cr
        if is_filter_todo and user_tz:
            from_zone = tz.gettz('UTC')
            to_zone = tz.gettz(user_tz)

            today = datetime.utcnow().replace(
                tzinfo=from_zone).astimezone(to_zone).replace(
                hour=23, minute=59, second=59)

            sql = "SELECT id FROM crm_lead \
            WHERE date_action AT time zone 'UTC' \
            AT time zone '%s' <= '%s';" % (user_tz, today)

            cr.execute(sql)

            lead_ids = []
            if cr.rowcount:
                lead_ids = [x[0] for x in cr.fetchall()]

            args.append(('id', 'in', lead_ids))

        return super(trobz_crm_lead, self).search(
            args, offset=offset, limit=limit, order=order, count=count)

    # I can't migrate this onchange, because it called from origin Odoo 7
    def onchange_stage_id(self, cr, uid, ids, stage_id, context=None):
        """
        Override function
        Remove source code that auto set values of Opportunity based on Stage
        """
        return {'value': {}}

    @api.onchange('probability_id')
    def on_change_probability_id(self):
        """
        Set probability = probability_percentage from probability_id
        """
        self.probability = float(self.probability_id.probability_percentage) \
            if self.probability_id else 0.0
