# -*- coding: utf-8 -*-

from openerp import fields, api, models
from openerp.tools.translate import _
from openerp.exceptions import Warning


class DowloadAllAttachments(models.Model):
    _name = "dowload.all.attachments"

    name = fields.Char("Name", size=64, required=True, select=1)
    model_id = fields.Many2one(
        'ir.model', 'Model', required=True, select=1)
    ref_ir_act_window = fields.Many2one(
        'ir.actions.act_window', 'Sidebar Action', readonly=True,
        help="Sidebar action to make this template available on records \
             of the related document model")
    ref_ir_value = fields.Many2one(
        'ir.values', 'Sidebar Button', readonly=True,
        help="Sidebar button to open the sidebar action")
    model_ids = fields.Many2many('ir.model', string='Model List')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', _('Name must be unique!')),
    ]

    @api.onchange('model_id')
    def onchange_model_id(self):
        if not self.model_id:
            return {'value': {'model_ids': [(6, 0, [])]}}
        model_ids = [self.model_id.id]
        active_model = self.model_id and self.model_id.model
        active_model_obj = self.env[active_model]
        model_obj = self.env['ir.model']
        if active_model_obj._inherits:
            for key, val in active_model_obj._inherits.items():
                found_model_ids = model_obj.search([('model', '=', key)])
                model_ids += found_model_ids
        return {'value': {'model_ids': [(6, 0, model_ids)]}}

    @api.multi
    def create_action(self):
        vals = {}
        action_obj = self.env['ir.actions.act_window']
        ir_values_obj = self.env['ir.values']
        for data in self:
            src_obj = data.model_id.model
            button_name = _('Dowload All Attachments (%s)') % data.name
            vals['ref_ir_act_window'] = action_obj.create(
                {
                    'name': button_name,
                    'type': 'ir.actions.act_window',
                    'res_model': 'dowload.all.attachments.wizard',
                    'src_model': src_obj,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'auto_refresh': 1,
                })
            vals['ref_ir_value'] = ir_values_obj.create(
                {
                    'name': button_name,
                    'model': src_obj,
                    'key2': 'client_action_multi',
                    'value': (
                        "ir.actions.act_window," +
                        str(vals['ref_ir_act_window'].id)),
                    'object': True
                })
        ref_ir_act_window = vals.get('ref_ir_act_window') and \
            vals.get('ref_ir_act_window').id or False
        ref_ir_value = vals.get('ref_ir_value') and \
            vals.get('ref_ir_value').id or False
        self.write(
            {
                'ref_ir_act_window': ref_ir_act_window,
                'ref_ir_value': ref_ir_value,
            })
        return True

    @api.multi
    def unlink_action(self):
        for template in self:
            try:
                if template.ref_ir_act_window:
                    template.ref_ir_act_window.unlink()
                if template.ref_ir_value:
                    template.ref_ir_value.unlink()
            except:
                raise Warning(
                    _("Warning"),
                    _("Deletion of the action record failed."))
        return True

    @api.multi
    def unlink(self):
        self.unlink_action()
        return super(DowloadAllAttachments, self).unlink()
