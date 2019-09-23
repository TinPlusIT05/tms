# -*- coding: utf-8 -*-
##############################################################################
# from openerp.osv import osv, fields
from openerp import models, api, fields
from datetime import date


class working_hours_export_wizard(models.TransientModel):
    _name = "working.hours.export.wizard"

    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)
    project_ids = fields.Many2many(
        "tms.project", "working_hours_export_project_rel",
        "wizard_id", "project_id", string="Projects list")

    @api.multi
    def button_export_working_hour_to_report(self):
        # Get wizard data and empty compose domain holder
        wizard_input = self[0]
        # Update export data
        wizard_input_data = {
            "from_date": wizard_input.from_date,
            "to_date": wizard_input.to_date,
            "project_ids": wizard_input.project_ids and
            wizard_input.project_ids.ids or [],
            "ids": self.ids,
            "model": "working.hours.export.wizard"
        }
        # Return a report and pass wizard input data to report parser
        return {
            "datas": wizard_input_data,
            "type": "ir.actions.report.xml",
            "report_name": "working_hours_export",
            "name": u"working-hours-report-{0}".format(date.today())
        }

    @api.multi
    def button_export_working_hour_dedicate(self):
        # Get wizard data and empty compose domain holder
        wizard_input = self[0]
        # Update export data
        wizard_input_data = {
            "from_date": wizard_input.from_date,
            "to_date": wizard_input.to_date,
            "project_ids": wizard_input.project_ids and
            wizard_input.project_ids.ids or [],
            "ids": self.ids,
            "model": "working.hours.export.wizard"
        }
        # Return a report and pass wizard input data to report parser
        return {
            "datas": wizard_input_data,
            "type": "ir.actions.report.xml",
            "report_name": "working_hours_dedicate_export",
            "name": u"working-hours-report-{0}".format(date.today())
        }
