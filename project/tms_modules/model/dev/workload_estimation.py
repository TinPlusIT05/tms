from openerp import fields, models


class WorkloadEstimation(models.Model):
    _name = 'workload.estimation'
    _description = 'Workload Estimation'
    _rec_name = 'code'
    _inherit = ['mail.thread']

    code = fields.Char('Reference', required=1, track_visibility='onchange')
    description = fields.Text(track_visibility='onchange')
    std_est = fields.Float(
        'Standard Estimation (Hours)', track_visibility='onchange')
