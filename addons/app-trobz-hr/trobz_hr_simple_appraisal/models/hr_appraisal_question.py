from openerp import models, fields


class HrAppraisalQuestion(models.Model):
    _name = 'hr.appraisal.question'
    _description = 'Appraisal question'
    _order = 'sequence asc'

    name = fields.Char(string="Question", size=256, required=True)
    sequence = fields.Integer(string="Sequence")
    group_id = fields.Many2one(
        'hr.appraisal.question.group', string="Group")
    template_id = fields.Many2one(
        'hr.appraisal.template', string="Template")
    help = fields.Text(
        'Help',
        default="Qualification explanations: \n"
                "- 1: \n"
                "- 2: \n"
                "- 3: \n"
                "- 4: \n"
                "- 5: \n"
                "This question must be answered with"
                " both qualification and explanation.")
