# -*- coding: utf-8 -*-

from openerp import models, fields, api


class HrAddEvaluatorsWizard(models.TransientModel):
    _name = 'hr.add.evaluators.wizard'

    evaluators_ids = fields.Many2many("hr.employee", string="Evaluators")

    @api.multi
    def button_add_evaluators(self):
        """
        - Add selected evaluators on wizards to appraisal
        - Create appraisal input for those evaluator using
            the evaluator template defined on the appraisal
        """
        AppraisalObj = self.env['hr.appraisal']
        InputObj = self.env['hr.appraisal.input']
        appraisal_ids = self._context.get('active_ids')
        appraisals = AppraisalObj.browse(appraisal_ids)
        selected_evaluators = self.evaluators_ids
        to_add_evaluator_ids = []
        for appraisal in appraisals:
            to_add_evaluator_ids = [x.id for x in appraisal.evaluators_ids]
            for evaluator in selected_evaluators:
                # If the input of this evaluator is created
                # No need to re-create the input.
                # Only need to do this for the re-opened appraisal.
                # For new appraisal, create input for all evaluators
                evaluator_input = InputObj.search(
                    [('author_id', '=', evaluator.id),
                     ('appraisal_id', '=', appraisal.id)])
                if evaluator_input:
                    continue
                vals = {
                    'appraisal_id': appraisal.id,
                    'author_id': evaluator.id}
                appraisal_input = InputObj.create(vals)
                AppraisalObj.generate_input_line(
                    appraisal_input.id, appraisal.template_evaluator_id)
                to_add_evaluator_ids.append(evaluator.id)
            appraisals.evaluators_ids = [(6, 0, to_add_evaluator_ids)]
