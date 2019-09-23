from openerp import models, fields, api, _


class HrAppraisalTemplate(models.Model):
    _name = 'hr.appraisal.template'
    _description = 'Appraisal template'

    name = fields.Char(string="Name")
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date")
    appraisal_question_ids = fields.One2many(
        "hr.appraisal.question", 'template_id', string="List of Questions")

    @api.multi
    def copy(self, default=None):
        """
        Keep the questions when duplicating a template
        """
        self.ensure_one()
        default = default or {}
        default['name'] = _("%s (copy)") % (self.name)
        copy_template = super(HrAppraisalTemplate, self).copy(default=default)
        for question in self.appraisal_question_ids:
            question.copy(default={'template_id': copy_template.id})
        return copy_template
