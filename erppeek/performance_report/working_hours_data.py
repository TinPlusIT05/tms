import erppeek
import sys
from datetime import datetime

from trobz.log import logger

PRODUCTION = 2


class WorkingHour:
    def __init__(self, wh_val):
        self.id = wh_val["id"]
        self.date = wh_val["date"]
        self.employee_id = (wh_val["employee_id"] and
                            wh_val["employee_id"][0] or None)
        self.project_id = wh_val["project_id"][0]
        self.activity_id = wh_val["tms_activity_id"][0]
        self.duration_hour = wh_val["duration_hour"]


class WorkingHoursData:

    def _get_wh_dicts(self):
        wh_e_dict = {}
        wh_p_dict = {}
        for wh in self.whs:
            if not wh.employee_id:
                self.log.warning('Skipping working hours (missing '
                                 'employee): %s', wh.id)
                continue
            wh_e_dict[wh.employee_id] = (wh_e_dict.get(wh.employee_id, 0) +
                                         wh.duration_hour)
            wh_p_dict[wh.project_id] = (wh_p_dict.get(wh.employee_id, 0) +
                                        wh.duration_hour)
        return wh_e_dict, wh_p_dict

    def _expected_working_hours(self, dt_start, dt_end):
        if dt_start >= dt_end:
            return 0
        duration = (dt_end - dt_start).days

        '''
          - 8: hours in a day
          - 251: number of working days in a year (=(365*5/7-10))
            - 5/7: 5 working days per week of 7 days
            - 10: public holidays]
        '''
        return duration * 8 * 251 / 365

    def _get_missing_working_hours(self, employees, dt_from, dt_to):

        standard_expected_wh = self._expected_working_hours(dt_from, dt_to)

        missing_whs = {}
        for employee in employees:

            if (employee.department_id and
               employee.department_id.id != PRODUCTION):
                self.log.debug('Skipping employee %s who is not in production '
                               'dept.', employee.name)
                continue

            if not employee.hire_date:
                self.log.debug('Skipping employee %s who is not hired yet.',
                               employee.name)
                continue

            if not employee.active:
                self.log.debug('Skipping employee %s who is not active.',
                               employee.name)
                continue

            employee_expected_wh = standard_expected_wh
            hire_date = employee.hire_date
            dt_hire = datetime.strptime(hire_date, '%Y-%m-%d')
            if dt_hire > dt_from:
                employee_expected_wh = self._expected_working_hours(dt_hire,
                                                                    dt_to)

            input_working_hours = self.wh_e_dict.get(employee.id, 0)
            missing_whs[employee.id] = \
                max(0, employee_expected_wh - input_working_hours)
        return missing_whs

    def write_missing_working_hours(self, worksheet_writer):

        header = ['Employee',
                  'Missing Working Hours']

        rows = []

        report = worksheet_writer.report

        for mwh in self.missing_whs:

            if self.report_data.team_filter:
                employee = self.report_data.get_employee(mwh)
                if not employee.team_id:
                    raise Exception("DATA ERROR: Employee %s missing a team" %
                                    employee.name)
                employee_team = employee.team_id.id
                if employee_team != self.report_data.team_filter:
                    continue

            if self.missing_whs[mwh] > 0:
                name = self.report_data.get_employee(mwh).name
                row = [
                    [name, report.styleText],
                    [self.missing_whs[mwh], report.styleNumber]
                ]
                rows.append(row)

        worksheet_writer.write("Missing Working Hours", header, rows)

        return True

    def __init__(self, report_data):
        self.log = logger('WorkingHoursData')

        self.report_data = report_data

        WH = self.report_data.client.model('tms.working.hour')

        wh_fields = ["id", "employee_id", "project_id", "tms_activity_id",
                     "duration_hour", "date"]

        whs = WH.read([('date', '>=', self.report_data.date_from),
                       ('date', '<=', self.report_data.date_to)],
                      fields=wh_fields)

        self.whs = [WorkingHour(w) for w in whs]

        self.wh_e_dict, self.wh_p_dict = self._get_wh_dicts()

        self.missing_whs = self._get_missing_working_hours(
            self.report_data.employees,
            self.report_data.dt_from,
            self.report_data.dt_to)
