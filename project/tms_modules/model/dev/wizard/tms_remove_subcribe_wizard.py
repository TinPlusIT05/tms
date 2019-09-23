from openerp import models, fields, api


class TmsRemoveSubscribeWizard(models.TransientModel):
    _name = "tms.remove.subscribe.wizard"
    _description = "Removing subscribe"

    user_ids = fields.Many2many(
        "res.users",
        string="Users",
        required=True,
    )
    project_id = fields.Many2one(
        "tms.project",
        string="Project",
        required=True,
    )

    @api.multi
    def button_remove_subscribe(self):
        self.ensure_one()
        tms_subscriber_to_remove = self.env['tms.subscriber'].search([
            ('forge_id.project_id', '=', self.project_id.id),
            ('name', 'in', self.user_ids.ids)])
        tms_subscriber_to_remove.unlink()
        return True
