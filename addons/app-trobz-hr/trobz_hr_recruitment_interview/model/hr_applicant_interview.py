# -*- encoding: UTF-8 -*-
##############################################################################

from openerp import fields, models
from openerp.addons.hr_recruitment.hr_recruitment \
    import AVAILABLE_PRIORITIES  # @UnresolvedImport


class hr_applicant_interview(models.Model):
    _name = "hr.applicant.interview"

    date = fields.Date('Date', required=1,
                       default=lambda self: fields.Datetime.now())
    feedback = fields.Text('Feedback', required=1)
    user_id = fields.Many2one('res.users', 'Interviewer')
    priority = fields.Selection(
        AVAILABLE_PRIORITIES, 'Appreciation', required=1)
    applicant_id = fields.Many2one('hr.applicant', 'Applicant')

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid
    }
