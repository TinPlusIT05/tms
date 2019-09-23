from openerp import fields, models


class WorkloadEstimationRisk(models.Model):
    _name = 'workload.estimation.risk'
    _description = 'Workload Estimation Risk'
    _rec_name = 'code'
    _inherit = ['mail.thread']

    code = fields.Char('Reference', required=1, track_visibility='onchange')
    level = fields.Char('Risk Level', track_visibility='onchange')
    description = fields.Text(track_visibility='onchange')
    weight = fields.Float(
        'Weight of risk', track_visibility='onchange')
