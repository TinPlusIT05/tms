# -*- encoding: utf-8 -*-

import xlwt
from datetime import datetime, timedelta
from openerp.report import report_sxw
from report_xls.report_xls import report_xls
from report_xls.utils import _render
from openerp.tools.translate import translate
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import math
import logging
_logger = logging.getLogger(__name__)

_ir_translation_name = 'hr.attendance.overtime.xls.report'


class hr_attendance_overtime_xls_report_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(hr_attendance_overtime_xls_report_parser, self).__init__(
            cr, uid, name, context=context
        )
        self.context = context
        wanted_list = self._report_xls_fields(cr, uid, context)
        self.localcontext.update({
            'datetime': datetime,
            'wanted_list': wanted_list,
            'template_changes': {},
            '_': self._
        })

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        return translate(self.cr, _ir_translation_name, 'report', lang, src)\
            or src

    # override list in custom module to add/drop columns or change order
    def _report_xls_fields(self, cr, uid, context=None):
        return [
            'date',
            'employee',
            'type',
            'department',
            'manager',
            'hour_in',
            'hour_out',
            'hours_of_presence',
            'working_schedule',
            'overtime_start',
            'overtime_end',
            'overtime_duration',
        ]


class hr_attendance_overtime_xls_report(report_xls):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(hr_attendance_overtime_xls_report, self).__init__(
            name, table, rml, parser, header, store
        )
        # Cell Styles
        _xs = self.xls_styles
        # header
        rh_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rh_cell_style = xlwt.easyxf(rh_cell_format)
        self.rh_cell_style_center = xlwt.easyxf(rh_cell_format + _xs['center'])
        # lines
        aml_cell_format = _xs['borders_all']
        self.aml_cell_style = xlwt.easyxf(aml_cell_format)
        self.aml_cell_style_center = xlwt.easyxf(
            aml_cell_format + _xs['center']
        )
        self.aml_cell_style_right = xlwt.easyxf(
            aml_cell_format + _xs['right']
        )

        # XLS Template
        self.col_specs_template = {
            'date': {
                'header': [1, 13, 'text', _render("_('Date')"),
                           None, self.rh_cell_style_center],
                'lines': [1, 0, 'text', _render("data_xls['date'] or ''"),
                          None, self.aml_cell_style_right],
            },
            'type': {
                'header': [1, 35, 'text', _render("_('Type') or ''"),
                           None, self.rh_cell_style_center],
                'lines': [1, 0, 'text', _render("data_xls['type'] or ''"),
                          None, self.aml_cell_style],
            },
            'employee': {
                'header': [1, 20, 'text', _render("_('Employee')"),
                           None, self.rh_cell_style_center],
                'lines': [1, 0, 'text', _render("data_xls['employee'] or ''"),
                          None, self.aml_cell_style],
            },
            'department': {
                'header': [1, 25, 'text', _render("_('Department')"),
                           None, self.rh_cell_style_center],
                'lines': [1, 0, 'text',
                          _render("data_xls['department'] or ''"),
                          None, self.aml_cell_style],
            },
            'manager': {
                'header': [1, 20, 'text', _render("_('Manager')"),
                           None, self.rh_cell_style_center],
                'lines': [1, 0, 'text', _render("data_xls['manager'] or ''"),
                          None, self.aml_cell_style],
            },
            'working_schedule': {
                'header': [1, 20, 'text', _render("_('Working Schedule')"),
                           None, self.rh_cell_style_center],
                'lines': [1, 0, 'text',
                          _render("data_xls['working_schedule'] or ''"),
                          None, self.aml_cell_style],
            },
            'hour_in': {
                'header': [1, 15, 'text', _render("_('Hour In')"),
                           None, self.rh_cell_style_center],
                'lines': [1, 0, 'text', _render("data_xls['hour_in'] or ''"),
                          None, self.aml_cell_style],
            },
            'hour_out': {
                'header': [1, 15, 'text', _render("_('Hour Out')"),
                           None, self.rh_cell_style_center],
                'lines': [1, 0, 'text', _render("data_xls['hour_out'] or ''"),
                          None, self.aml_cell_style],
            },
            'hours_of_presence': {
                'header': [1, 20, 'text', _render("_('Hours of Presence')"),
                           None, self.rh_cell_style_center],
                'lines': [1, 0, 'text',
                          _render("data_xls['hours_of_presence'] or ''"),
                          None, self.aml_cell_style],
            },
            'overtime_start': {
                'header': [1, 15, 'text', _render("_('Overtime Start')"),
                           None, self.rh_cell_style_center],
                'lines': [1, 0, 'text',
                          _render("data_xls['overtime_start'] or ''"),
                          None, self.aml_cell_style],
            },
            'overtime_end': {
                'header': [1, 15, 'text', _render("_('Overtime End')"),
                           None, self.rh_cell_style_center],
                'lines': [1, 0, 'text',
                          _render("data_xls['overtime_end']  or ''"),
                          None, self.aml_cell_style],
            },
            'overtime_duration': {
                'header': [1, 20, 'text', _render("_('Overtime Duration')"),
                           None, self.rh_cell_style_center],
                'lines': [1, 0, 'text',
                          _render("data_xls['overtime_duration']  or ''"),
                          None, self.aml_cell_style],
            },
        }

    def generate_xls_report(self, _p, _xs, data, objects, wb):
        wanted_list = _p.wanted_list
        self.col_specs_template.update(_p.template_changes)
        _ = _p._

        report_name = _("Attendance Report")
        sheet_name = _("Attendance Report")
        ws = wb.add_sheet(sheet_name)
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 1
        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        # Title
        cell_style = xlwt.easyxf(_xs['xls_title']+_xs['center'])
        c_specs = [
            ('report_name', 12, 0, 'text', report_name),
        ]

        row_data = self.xls_row_template(c_specs, ['report_name'])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style
        )
        row_pos += 1

        c_specs = map(
            lambda x: self.render(x, self.col_specs_template, 'header',
                                  render_space={'_': _p._}),
            wanted_list
        )
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=self.rh_cell_style,
            set_column_size=True
        )
        department_id = data['department_id']
        manager_id = data['manager_id']
        date_from = data['date_from']
        date_to = data['date_to']
        datas_xls = self.prepare_datas_for_xls(
            self.cr, self.uid, department_id, manager_id, date_from, date_to
        )

        for data_xls in datas_xls:
            print data_xls  # to avoid warning
            c_specs = map(
                lambda x: self.render(x, self.col_specs_template, 'lines'),
                wanted_list
            )
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data
            )

    def prepare_datas_for_xls(self, cr, uid, department_id, manager_id,
                              date_from, date_to):
        """
        Get data to show on attendance report
        1. Prepare data
        - schedule_data
        - overtimes_data
        - leave_lines_data
        - attendances_data
        2. Each record shown on report, read data from prepared datas
        """
        hr_holidays_line_obj = self.pool['hr.holidays.line']
        hr_attendance_obj = self.pool['hr.attendance']
        hr_employee_obj = self.pool['hr.employee']
        hr_overtime_obj = self.pool['hr.overtime']
        schedule_obj = self.pool['resource.calendar']
        base_obj = self.pool['trobz.base']

        domain = []
        if department_id:
            domain.append(('department_id', '=', department_id))
        if manager_id:
            domain.append(('parent_id', '=', manager_id))
        employee_ids = hr_employee_obj.search(cr, uid, domain)

        # PREPARE DATA FOR REPORT
        # schedule_data = {(working schedule, weekday): description}
        # overtimes_data = {(employee, date): [start, end, hours]}
        # leave_lines_data = {(employee, date): Absent - leave type}
        # attendances_data = {(employee, date): [start, end, hours]}

        # 1. Schedule data
        schedule_ids = schedule_obj.search(cr, uid, [])
        schedules = schedule_obj.browse(cr, uid, schedule_ids)
        schedule_data = {}
        for schedule in schedules:
            for schedule_line in schedule.attendance_ids:
                key = (schedule.id, int(schedule_line.dayofweek))
                hour_from = self.convert_float_to_time(
                    cr, uid, schedule_line.hour_from
                )
                hour_to = self.convert_float_to_time(
                    cr, uid, schedule_line.hour_to
                )
                if key not in schedule_data:
                    schedule_data[key] = hour_from + '-' + hour_to
                else:
                    schedule_data[key] += ' & ' + hour_from + '-' + hour_to

        # 2. Overtime data
        # Get all confirmed overtime follow by given conditions from wizard
        # group by (employee, date)
        overtime_ids = hr_overtime_obj.search(
            cr, uid, [('employee_id', 'in', employee_ids),
                      ('state', '=', 'confirmed'),
                      ('name', '>=', date_from),
                      ('name', '<=', date_to)]
        )
        overtimes = hr_overtime_obj.read(
            cr, uid, overtime_ids,
            ['employee_id', 'name', 'datetime_start', 'datetime_stop']
        )
        overtimes_data = {}
        for overtime in overtimes:
            key = (overtime['employee_id'][0], overtime['name'])
            # Show overtime at current time zone on report
            tz_ot_start = base_obj.convert_from_utc_to_current_timezone(
                cr, uid, overtime['datetime_start']
            )
            ot_start = tz_ot_start.strftime('%H:%M:%S')
            tz_ot_end = base_obj.convert_from_utc_to_current_timezone(
                cr, uid, overtime['datetime_stop']
            )
            ot_end = tz_ot_end.strftime('%H:%M:%S')
            ot_hours = str(tz_ot_end - tz_ot_start)
            overtimes_data[key] = [
                ot_start,
                ot_end,
                ot_hours
            ]

        # 3. leave request data
        # Get all approved leave lines follow by given conditions from wizard
        # group by (employee, date)
        leave_line_ids = hr_holidays_line_obj.search(
            cr, uid, [('employee_id', 'in', employee_ids),
                      ('state', '=', 'validate'),
                      '|', '|',
                      '&', ('first_date', '<=', date_from),
                      ('last_date', '>=', date_from),
                      '&', ('first_date', '<=', date_to),
                      ('last_date', '>=', date_to),
                      '&', ('first_date', '>=', date_from),
                      ('last_date', '<=', date_to),
                      ]
        )
        leave_lines = hr_holidays_line_obj.browse(cr, uid, leave_line_ids)
        leave_lines_data = {}
        for line in leave_lines:
            employee_id = line.employee_id.id
            min_date_from = max(line.first_date, date_from)
            max_date_to = min(line.last_date, date_to)
            min_date_from = datetime.strptime(min_date_from, DF)
            max_date_to = datetime.strptime(max_date_to, DF)
            delta = max_date_to - min_date_from
            for i in range(delta.days + 1):
                date = (min_date_from + timedelta(days=i)).strftime(DF)
                leave_lines_data[(employee_id, date)] = \
                    'Absent' + ' - ' + line.holiday_status_id.name

        # 4. attendance data
        # Get all attendances follow by given conditions from wizard
        # Get the first sign-in and the last sign-out group by employee
        attendance_ids = hr_attendance_obj.search(
            cr, uid, [('employee_id', 'in', employee_ids),
                      ('day', '>=', date_from),
                      ('day', '<=', date_to)],
            order='name'
        )
        attendances = hr_attendance_obj.browse(
            cr, uid, attendance_ids,
        )
        # Attendances group by (employee, date)
        attendances_data_temp = {}
        for attendance in attendances:
            key = (attendance.employee_id.id, attendance.day)
            if key not in attendances_data_temp:
                attendances_data_temp[key] = []
            attendances_data_temp[key].append(
                [attendance.name, attendance.action]
            )
        # Get the first sign-in and the last sign-out
        # Group by (employee, date)
        attendances_data = {}
        for emp_day in attendances_data_temp.keys():
            # Find the first sign-in
            emp_atts = attendances_data_temp[emp_day]
            first_att = False
            tz_first_att = False
            while emp_atts and not first_att:
                if emp_atts[0][1] == 'sign_in':
                    tz_first_att = \
                        base_obj.convert_from_utc_to_current_timezone(
                            cr, uid, emp_atts[0][0]
                        )
                    first_att = tz_first_att.strftime('%H:%M:%S')
                emp_atts.pop(0)
            # Find the last sign-out
            emp_atts = attendances_data_temp[emp_day]
            last_att = False
            tz_last_att = False
            while emp_atts and not last_att:
                if emp_atts[-1][1] == 'sign_out':
                    tz_last_att = \
                        base_obj.convert_from_utc_to_current_timezone(
                            cr, uid, emp_atts[-1][0]
                        )
                    last_att = tz_last_att.strftime('%H:%M:%S')
                emp_atts.pop(-1)
            att_hours = 0
            if tz_first_att and tz_last_att:
                att_hours = str(tz_last_att - tz_first_att)
            attendances_data[emp_day] = [first_att, last_att, att_hours]

        # GET DATA FROM PREPARED DATA ABOVE
        # INTO DATAS_XLS TO SHOW ON REPORT
        # for each date, for each employee
        # Show a row in report if it exist value
        date_from = datetime.strptime(date_from, DF)
        date_to = datetime.strptime(date_to, DF)
        days = (date_to - date_from).days
        datas_xls = []
        employees = hr_employee_obj.browse(cr, uid, employee_ids)

        for i in range(days + 1):
            date = (date_from + timedelta(days=i)).strftime('%Y-%m-%d')
            day_of_week = (date_from + timedelta(days=i)).weekday()
            for employee in employees:
                # Get schedule from schedule_data
                calendar_id = employee and employee.contract_id \
                    and employee.contract_id.working_hours \
                    and employee.contract_id.working_hours.id
                emp_working_schedule = ''
                if calendar_id:
                    key = (calendar_id, day_of_week)
                    emp_working_schedule = schedule_data.get(key, False)

                key = (employee.id, date)
                emp_att = attendances_data.get(key, False)
                emp_ot = overtimes_data.get(key, False)
                emp_leave = leave_lines_data.get(key, False)
                if emp_working_schedule or emp_att \
                   or emp_ot or emp_leave:
                    # Only show on report for record have as least
                    # one of info below:
                    # - working schedule
                    # - Overtime
                    # - Leave request
                    # - Attendance
                    data_xls = {
                        'date': date,
                        'type': emp_leave or 'Present',
                        'employee': employee.name,
                        'department': employee.department_id.name,
                        'manager': employee.parent_id.name,
                        'hour_in': emp_att and emp_att[0] or '',
                        'hour_out': emp_att and emp_att[1] or '',
                        'hours_of_presence': emp_att and emp_att[2]
                        or None,
                        'working_schedule': emp_working_schedule,
                        'overtime_start': emp_ot and emp_ot[0] or '',
                        'overtime_end': emp_ot and emp_ot[1] or '',
                        'overtime_duration': emp_ot and emp_ot[2] or ''
                    }
                    datas_xls.append(data_xls)
        return datas_xls

    def convert_float_to_time(self, cr, uid, float_time):
        float_minutes = float_time - math.floor(float_time)
        minutes = str(int(float_minutes*60))
        if len(str(int(minutes))) == 1:
            minutes = str(int(minutes)) + '0'
        hours = str(int(math.floor(float_time)))
        return hours + ':' + minutes

hr_attendance_overtime_xls_report(
    'report.hr.attendance.overtime.xls.report',
    'hr.attendance',
    parser=hr_attendance_overtime_xls_report_parser
)
