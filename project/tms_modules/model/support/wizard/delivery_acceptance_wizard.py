# -*- coding: utf-8 -*-
from openerp import fields, api, models


class DeliveryAcceptanceWizard(models.TransientModel):
    _name = "delivery.acceptance.wizard"

    project_ids = fields.Many2many('tms.project', string='Projects')
    start_date = fields.Date("Start Date", required=True)
    end_date = fields.Date("End Date", required=True)
    activity_ids = fields.Many2many('tms.activity', string='activities')

    @api.constrains('start_date', 'end_date')
    def _check_constraint_start_date_and_end_date(self):
        """
        Check Overlapping date_start and date_end
        """
        if self.end_date < self.start_date:
            raise Warning("""End date must be equal or greater than start date.
                """)

    @api.multi
    def button_export_delivery_acceptance(self):
        wizard = self[0]
        if not wizard.project_ids:
            raise Warning("""You should input at least 1 project.""")
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'delivery_acceptance_report'}
