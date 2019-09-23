# -*- coding: utf-8 -*-
##############################################################################
# from openerp.osv import osv, fields
from openerp import models, api, fields
from datetime import date


class HrMothlyTimesheetWizard(models.TransientModel):
    _name = "hr.monthly.timesheet.wizard"

    month = fields.Selection(
        string='Month',
        selection=[
            (1, 'January'),
            (2, 'February'),
            (3, 'March'),
            (4, 'April'),
            (5, 'May'),
            (6, 'June'),
            (7, 'July'),
            (8, 'August'),
            (9, 'September'),
            (10, 'October'),
            (11, 'November'),
            (12, 'December'),
        ],
        default=lambda self: date.today().month,
        required=True
    )
    year = fields.Selection(
        string='Year',
        selection=[(y, '%s' % y) for y in range(2010, 2051)],
        default=lambda self: date.today().year,
        required=True
    )

    @api.multi
    def button_export_monthly_timesheet_report(self):
        self.ensure_one()
        wizard_input_data = {
            "month": self.month,
            "year": self.year,
            "model": "hr.monthly.timesheet.wizard"
        }
        return {
            "datas": wizard_input_data,
            "type": "ir.actions.report.xml",
            "report_name": "report.workinghour.timesheet.xlsx",
            "name": u"Monthly-Timesheet-{0}-{1}".format(self.month, self.year)
        }

    @api.multi
    def button_export_monthly_ot_report(self):
        self.ensure_one()
        wizard_input_data = {
            "month": self.month,
            "year": self.year,
            "model": "hr.monthly.timesheet.wizard"
        }
        return {
            "datas": wizard_input_data,
            "type": "ir.actions.report.xml",
            "report_name": "report.workinghour.timesheet.ot.xlsx",
            "name": u"OT Summarize-{0}-{1}".format(self.month, self.year)
        }
