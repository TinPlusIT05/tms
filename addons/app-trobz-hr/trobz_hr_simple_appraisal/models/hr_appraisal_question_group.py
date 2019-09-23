from openerp import models, fields, _


class HrAppraisalQuestionGroup(models.Model):
    _name = 'hr.appraisal.question.group'
    _description = 'Appraisal question group'

    name = fields.Char(string="Name", required=True)

    _sql_constraints = [
        ('unique_name', 'unique(name)',
         _('This question group is already existed!')),
    ]
