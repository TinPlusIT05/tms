# -*- coding: utf-8 -*-
from openerp import models, api


class trobz_crm_lead2opportunity_partner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    @api.model
    def default_get(self, fields):
        """
            Default get for name, opportunity_ids
            if there is an exisitng  partner link to the lead, find all
            existing opportunity link with this partnet to merge
            all information together
        """
        ctx = self._context or {}
        lead_obj = self.env['crm.lead']

        res = super(
            trobz_crm_lead2opportunity_partner, self).default_get(fields)

        if ctx.get('active_id', False):
            lead = lead_obj.browse(ctx['active_id'])
            if lead.partner_id:
                res['partner_id'] = lead.partner_id.id
                res['action'] = 'exist'
        return res

    @api.multi
    def _convert_opportunity(self, vals):
        res = False
        lead_env = self.env['crm.lead']
        data = self[0]
        lead_ids = vals.get('lead_ids', [])
        lead_objs = lead_env.browse(lead_ids)
        partner_id = vals.get('partner_id', False)
        team_id = vals.get('section_id', False)
        user_ids = vals.get('user_ids', False)

        for lead in lead_objs:
            partner_id = self._create_partner(
                lead.id, data.action, partner_id or lead.partner_id.id)
            res = lead.convert_opportunity(partner_id, user_ids, team_id)
        return res

    @api.multi
    def _merge_opportunity(self, opportunity_ids, action='merge'):
        #  TOFIX: is it usefully ?
        res = False
        merge_opportunity_env = self.env['crm.merge.opportunity']
        ctx = self._context and self._context.copy() or {}

        #  If we convert in mass, don't merge if there is no other opportunity
        # but no warning
        if action == 'merge'\
                and (len(opportunity_ids) > 1 or not ctx.get('mass_convert')):
            self.write({'opportunity_ids': [(6, 0, [opportunity_ids[0].id])]})
            ctx.update({
                'lead_ids': ctx.get('active_ids', []),
                "convert": True
            })
            res = merge_opportunity_env.with_context(
                ctx).merge(opportunity_ids)
        return res

    @api.multi
    def action_apply(self):
        """
        This converts lead to opportunity and opens Opportunity view
        """
        lead_env = self.env['crm.lead']
        lead_ids = self._context.get('active_ids', [])
        data = self[0]
        self._convert_opportunity({'lead_ids': lead_ids})
        self._merge_opportunity(data.opportunity_ids, data.action)
        return lead_env.redirect_opportunity_view(lead_ids[0])

trobz_crm_lead2opportunity_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
