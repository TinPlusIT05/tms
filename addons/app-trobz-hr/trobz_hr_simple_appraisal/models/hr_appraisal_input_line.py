from openerp import models, fields, api, _
from openerp.exceptions import Warning


class HrAppraisalInputLine(models.Model):
    _name = 'hr.appraisal.input.line'
    _description = 'Appraisal input line'

    input_id = fields.Many2one(
        'hr.appraisal.input', string="Input", readonly=True,
        ondelete='cascade')
    question_id = fields.Many2one(
        'hr.appraisal.question', string="Question", readonly=True)
    sequence = fields.Integer(
        string="Sequence", related='question_id.sequence', readonly=True)
    qualification = fields.Selection(
        [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], string="Qualification")
    explanation = fields.Text(string="Explanation")
    state = fields.Selection(
        [('requested', 'Requested'), ('done', 'Done')],
        string="Status", related='input_id.state', readonly=True, store=True)
    group_name = fields.Char(
        string="Group", related='question_id.group_id.name', readonly=True)
    question_help = fields.Text(
        'Help', related="question_id.help", readonly=True)

    @api.multi
    def write(self, vals):
        """
        Security on appraisal input line :
        - Manual update: only author can update his input
        - Auto update state from appraisal: HR manager can update all inputs.
        """
        context = self._context or {}
        current_user_id = self._uid
        for appraisal in self:
            author_user_id = appraisal.input_id.author_id.user_id and \
                appraisal.input_id.author_id.user_id.id or False
            auto_update = context.get('auto_update_from_appraisal')
            if not auto_update and vals and author_user_id != current_user_id:
                raise Warning(_("Only author can update his appraisal input."))
        return super(HrAppraisalInputLine, self).write(vals)
