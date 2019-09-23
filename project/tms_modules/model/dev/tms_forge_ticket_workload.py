from openerp import api, fields, models


class TMSForgeTicketWorkload(models.Model):
    _name = 'tms.forge.ticket.workload'
    _description = 'TMS Forge Ticket Workload'

    forge_ticket_id = fields.Many2one(
        'tms.forge.ticket',
        'Forge Ticket',
    )
    wl_est_id = fields.Many2one(
        'workload.estimation',
        'Workload Estimation',
    )
    wl_est_qty = fields.Integer('Quantity of applied workload estimation')
    wl_risk_id = fields.Many2one(
        'workload.estimation.risk',
        'Workload Estimation Risk',
    )
    std_est = fields.Float(
        'Standard Estimated', compute='_compute_std_est',
        store=True)
    final_est = fields.Float('Final Estimated Workload')
    diff_est = fields.Float(
        'Difference Estimated Workload',
        compute='_compute_diff_est')

    @api.depends('wl_est_id', 'wl_est_id.std_est',
                 'wl_risk_id', 'wl_risk_id.weight',
                 'wl_est_qty')
    def _compute_std_est(self):
        for rec in self:
            std_est = rec.wl_est_id and rec.wl_est_id.std_est or 0
            weight = rec.wl_risk_id and rec.wl_risk_id.weight or 0
            rec.std_est = rec.wl_est_qty * std_est * weight

    @api.multi
    def _compute_diff_est(self):
        for rec in self:
            rec.diff_est = rec.std_est - rec.final_est
