from openerp import fields, models


class hr_applicant(models.Model):
    _inherit = "hr.applicant"

    interview_ids = fields.One2many(
        'hr.applicant.interview', 'applicant_id', 'Interview Feedbacks')
