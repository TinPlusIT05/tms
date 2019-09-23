# -*- coding: utf-8 -*-
##############################################################################
# from openerp.osv import osv, fields
from openerp import models, api, fields
from datetime import date, datetime


class StaffWorkingAttendanceWizard(models.TransientModel):
    _name = "staff.working.attendance.wizard"

    year = fields.Selection(
        selection='get_year_values',
        string="Year", required=True,
        default=str(datetime.now().year))
    month = fields.Selection(
        selection='get_month_values',
        string="Month", required=True,
        default=str(datetime.now().month))
    employee_ids = fields.Many2many(
        "hr.employee", "staff_working_attendance_employee_rel",
        "wizard_id", "employee_id", string="Employees")

    def get_year_values(self):
        """
        Return value from start of company to current year
        """
        start_year = 2009
        td = datetime.now()
        cur_year = td.year
        vals = []
        for year in range(start_year, cur_year + 1):
            vals.append((str(year), str(year)))
        return vals

    def get_month_values(self):
        vals = []
        for month in range(1, 13):
            vals.append((str(month), str(month)))
        return vals

    @api.multi
    def button_print_staff_working_attendance_report(self):
        # Get wizard data and empty compose domain holder
        input = self[0]
        # Update export data
        wizard_input_data = {
            "year": input.year,
            "month": input.month,
            "employee_ids":
            input.employee_ids and input.employee_ids.ids or [],
            "ids": self.ids,
            "model": "staff.working.attendance.wizard"
        }
        # Return a report and pass wizard input data to report parser
        return {
            "datas": wizard_input_data,
            "type": "ir.actions.report.xml",
            "report_name": "staff_working_attendance",
            "name": u"Staff Working Attendance ({0})".format(date.today())
        }
