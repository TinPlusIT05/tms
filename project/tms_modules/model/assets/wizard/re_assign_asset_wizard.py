# -*- coding: utf-8 -*-
from openerp import models, api, fields
from datetime import datetime


class re_assign_asset_wizard(models.TransientModel):
    _name = "re.assign.asset.wizard"

    assignee_id = fields.Many2one(
        string="New Assignee", comodel_name="hr.employee",)
    assigning_date = fields.Date(
        string="Assigning Date", default=datetime.now().today())
    item_condition_id = fields.Many2one(
        string="Current Equip. Status", comodel_name="item.condition")
    condition_details = fields.Text(string="Conditional Details")

    @api.multi
    def button_assign_asset(self):
        context = self._context and self._context.copy() or {}
        if self.ids and context.get('active_ids', False):
            asset_ids = context['active_ids']
            obj = self.browse(self.ids[0])
        assets = self.env['tms.asset'].search([('id', 'in', asset_ids)])
        for asset in assets:
            asset_vals = {
                'assignee_id': obj.assignee_id and obj.assignee_id.id,
                'assigning_date': obj.assigning_date,
                'item_condition_id': obj.item_condition_id.id,
                'condition_details': obj.condition_details,
            }
            asset.write(asset_vals)
        return {
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window_close'
        }
