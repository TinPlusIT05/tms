# -*- coding: utf-8 -*-
##############################################################################
from datetime import datetime, timedelta
from openerp import _
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
import calendar as calendar


class HrEmLeaveSummaryReportXlsx(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, objects):
        self.row = 0
        self.objects = objects
        self.data = data
        self._define_formats(workbook)
        self.sheet = workbook.add_worksheet(_(
            'Medical Leave Summary (%s)' % (data.get('year'))))

        # generate report content
        self.generate_content()

    def _define_formats(self, workbook):
        base_format = {
            'border': False,
            'align': 'center',
            'bold': False,
            'italic': False,
            'font_name': 'Arial',
            'font_size': 11,
            'valign': 'vcenter',
            'text_wrap': True,
        }
        self.base_format = workbook.add_format(base_format)

        # title format
        title_format = base_format.copy()
        title_format.update({
            'bold': True,
            'font_size': 19,
            'bg_color': '#A9D18E'
        })
        self.title_format = workbook.add_format(title_format)

        # sub title format
        sub_title_format = base_format.copy()
        sub_title_format.update({
            'bold': True,
            'font_size': 18,
        })
        self.sub_title_format = workbook.add_format(sub_title_format)

        # header format
        header_format = base_format.copy()
        header_format.update({
            'border': True,
            'bg_color': 'BAE6B0',
        })
        self.header_format = workbook.add_format(header_format)

        # content format
        content_format = base_format.copy()
        content_format.update({
            'border': True
        })
        self.content_format = workbook.add_format(content_format)

        # content format for number
        content_number_format = content_format.copy()
        content_number_format.update({
            'num_format': '#0.0;(#0.0)',
        })
        self.content_number_format = workbook.add_format(content_number_format)

    def generate_content(self):
        self._set_default_format()
        self.sheet.freeze_panes(5, 3)
        self.generate_headers()
        self.generate_table_content()

    def generate_table_content(self):
        data = {}
        # generate sql param
        leave_types = []
        leave_type_param = self.env['ir.config_parameter'].get_param(
            'emergency_medical_type')
        for name_type in eval(leave_type_param):
            leave_type = self.env['hr.holidays.status'].search(
                [('name', '=', name_type.strip())], limit=1)
            if leave_type:
                leave_types.append(leave_type.id)

        params = {
            'from_date': '{0}-01-01'.format(self.data.get('year')),
            'update_to': self.data.get('update_to'),
            'leave_type': '(' + ', '.join(map(str, leave_types)) + ')',
        }

        # get employee sick leave infomation
        sql = """
            SELECT
                emp.id AS employee_id,
                sum(number_of_days_temp) AS sum_leave,
                -- EXTRACT(MONTH FROM leave.last_date) "month",
                EXTRACT(MONTH FROM leave.last_date) "month"
            FROM
                hr_holidays_line leave
                JOIN hr_employee emp
                    ON emp.id = leave.employee_id
            WHERE
                leave.holiday_status_id IN %(leave_type)s
                AND leave.state IN ('validate')
                AND (leave.last_date <= '%(update_to)s')
                AND (leave.last_date >= '%(from_date)s')
            GROUP BY
                emp.id, month
            ORDER BY
                employee_id
        """ % params

        self.env.cr.execute(sql)
        leave_data = self.env.cr.dictfetchall()

        # generate employee list table
        sql = """
            SELECT
                ROW_NUMBER() OVER(ORDER BY emp.id) id,
                emp.id employee_id
            FROM
                hr_employee emp
                JOIN
                    (SELECT
                        ru.id ru_id,
                        ru.employee_id employee_id,
                        rs.name
                    FROM
                        res_users ru
                        INNER JOIN resource_resource rs
                            ON rs.user_id = ru.id
                    WHERE
                        rs.active = TRUE
                    ) tb
                    ON tb.employee_id = emp.id
            ORDER BY
                emp.id
        """
        self.env.cr.execute(sql)
        data = self.env.cr.dictfetchall()

        # init col position
        text_pos = {
            'id': 'A',
            'employee_code': 'B',
            'employee_name': 'C',
            'remark': 'T',
        }
        date_pos = {
            'starting_date': 'D',
        }
        number_pos = {
            'eml_leave_in_year': 'E',
            1: 'F',  # Jan
            2: 'G',  # Feb
            3: 'H',  # Mar
            4: 'I',  # Apr
            5: 'J',  # May
            6: 'K',  # Jun
            7: 'L',  # Jul
            8: 'M',  # Aug
            9: 'N',  # Sep
            10: 'O',  # Oct
            11: 'P',  # Nov
            12: 'Q',  # Dec
        }
        formula_pos = {
            'taken': 'R',
            'balance': 'S'
        }

        # generate data table and export to excel
        self.row = 5
        for info in data:
            # get employee name
            employee = self.env['hr.employee'].browse(info.get('employee_id'))

            # set taken cell value
            info.update({'taken': "SUM(F{0}:Q{0})".format(self.row + 1)})

            # set balance cell value
            info.update(
                {'balance': "+E{0}-SUM(F{0}:Q{0})".format(self.row + 1)}
            )

            # set employee code
            info.update({'employee_code': ''})

            # set employee name
            info.update({'employee_name': employee.name})

            # filter employee with employee id
            for leave in filter(
                    lambda x: x.get('employee_id') == employee.id, leave_data):
                info.update({int(leave.get('month')): -
                             float(leave.get('sum_leave'))})

            # set starting date
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', employee.id),
            ], limit=1, order='id desc')

            def _calculate_sick_leave_month(starting, update_to):
                # calculate sick leave (paid) in year
                update_to_date = datetime.strptime(update_to, "%Y-%m-%d")
                hire_date = datetime.strptime(starting, "%Y-%m-%d")

                # update base vale of 'calculated sick month' (sick_cal_month)
                #     - check condition for month of
                #       'hire date' and 'update to date'
                sick_cal_month = update_to_date.month - hire_date.month \
                    if update_to_date.month > hire_date.month else 0

                # modify condition for 'calculated sick month' (sick_cal_month)
                #     - sick_cal_month + 1 when day of
                #       `update to date` greater than 15
                #     - sick_cal_month - 1 when day of
                #       `hire date` greater than 15
                sick_cal_month = sick_cal_month + 1 \
                    if update_to_date.day >= 15 else sick_cal_month
                sick_cal_month = sick_cal_month - 1 \
                    if hire_date.day >= 15 else sick_cal_month
                sick_cal_month = 0 \
                    if sick_cal_month < 0 else sick_cal_month

                return sick_cal_month

            # some fix number
                # standard emergency date in year
            std_eml = 5
            # check condition for official employee with:
            # - 'contract type' is 'Employee'
            # - 'trial on contract' is 'False'
            if contract.type_id.name != 'Trainee' and not contract.is_trial:
                # check for 'Employee'
                hire_date = datetime.strptime(employee.hire_date, "%Y-%m-%d") \
                    if employee.hire_date else False

                if hire_date and \
                        int(hire_date.year) == int(self.data.get('year')):
                    sick_cal_month = _calculate_sick_leave_month(
                        employee.hire_date,
                        "{0}-12-31".format(self.data.get("year")),
                    )
                    # update value into sheet
                    info.update(
                        {
                            'eml_leave_in_year':
                            round(float(sick_cal_month) * std_eml / 12, 2),
                        }
                    )
                else:
                    info.update({'eml_leave_in_year': std_eml})

                # update value starting date into sheet
                info.update({'starting_date': employee.hire_date})
            else:
                # check for 'Trainee' or 'Probation'
                info.update({'eml_leave_in_year': 0})

            # export to excel file
                # export text column
            for key, value in text_pos.items():
                self.sheet.write(
                    "{0}{1}".format(value, self.row + 1),
                    info.get(key), self.content_format
                )
                # export number column
            for key, value in number_pos.items():
                self.sheet.write(
                    "{0}{1}".format(value, self.row + 1),
                    info.get(key) or '', self.content_number_format
                )
                # export formula column
            for key, value in formula_pos.items():
                self.sheet.write_formula(
                    "{0}{1}".format(value, self.row + 1),
                    info.get(key), self.content_number_format
                )
                # export datetime items
            for key, value in date_pos.items():
                if info.get(key):
                    # convert datetime format
                    export_val = datetime.strptime(
                        info.get(key), "%Y-%m-%d"
                    ).strftime("%d/%m/%Y")
                else:
                    export_val = '-'

                self.sheet.write(
                    "{0}{1}".format(value, self.row + 1),
                    export_val, self.content_number_format
                )

            # increate current excel row
            self.row += 1

    def generate_headers(self):
        # define header and title content
        title = u'TROBZ - EMERGENCY MEDICAL LEAVE SUMMARY'
        sub_title = self.data.get('year')
        decription = 'Updated to:'
        desc_content = datetime.strptime(
            self.data.get('update_to'), "%Y-%m-%d"
        ).strftime("%d/%m/%Y")
        first_header = [
            'No.',
            'Employee Code',
            'Name',
            'Starting Date',
            'Emergency Medical Leave in this year',
            'Sick leave',
            'Taken',
            'Balance',
            'Remarks',
        ]
        second_header = [
            name[0:3] for name in calendar.month_name if name != ''
        ]

        # generate title content
        self.row = 0
        self.sheet.merge_range('A1:T1', title, self.title_format)

        # generate sub-title content
        self.row = 1
        self.sheet.write('T2', sub_title, self.sub_title_format)

        # generate description content
        self.row = 2
        self.sheet.write('S3', decription, self.base_format)
        self.sheet.write('T3', desc_content, self.base_format)

        # generate first header content
        self.row = 3
        column_name = list(map(chr, range(ord('A'), ord('E') + 1)))
        for content, col_name in zip(first_header[0:5], column_name):
            self.sheet.merge_range(
                '{0}{1}:{0}{2}'.format(col_name,
                                       str(self.row + 1),
                                       str(self.row + 2)),
                content, self.header_format
            )

        self.sheet.merge_range(
            'F{0}:Q{0}'.format(str(self.row + 1)),
            first_header[5], self.header_format
        )

        column_name = list(map(chr, range(ord('R'), ord('T') + 1)))
        for content, col_name in zip(first_header[6:], column_name):
            self.sheet.merge_range(
                '{0}{1}:{0}{2}'.format(col_name,
                                       str(self.row + 1),
                                       str(self.row + 2)),
                content, self.header_format
            )
        # generate second header content
        self.row = 4
        column_name = list(map(chr, range(ord('F'), ord('Q') + 1)))
        for content, col_name in zip(second_header, column_name):
            self.sheet.write(
                '{0}{1}'.format(col_name, str(self.row + 1)),
                content,
                self.header_format
            )

    def _set_default_format(self):
        self.sheet.set_column('A:A', 5)
        self.sheet.set_column('B:B', 12)
        self.sheet.set_column('C:C', 25)
        self.sheet.set_column('D:D', 23)
        self.sheet.set_column('E:E', 12)
        self.sheet.set_column('F:F', 6)
        self.sheet.set_column('G:G', 6)
        self.sheet.set_column('H:H', 6)
        self.sheet.set_column('I:I', 6)
        self.sheet.set_column('J:J', 6)
        self.sheet.set_column('K:K', 6)
        self.sheet.set_column('L:L', 6)
        self.sheet.set_column('M:M', 6)
        self.sheet.set_column('N:N', 6)
        self.sheet.set_column('O:O', 6)
        self.sheet.set_column('P:P', 6)
        self.sheet.set_column('Q:Q', 6)
        self.sheet.set_column('R:R', 11)
        self.sheet.set_column('S:S', 11)
        self.sheet.set_column('T:T', 25)

        self.sheet.set_row(0, 50)
        self.sheet.set_row(1, 40)
        self.sheet.set_row(2, 20)
        self.sheet.set_row(3, 20)
        self.sheet.set_row(4, 30)

    def _get_leave_data(self, domain, month, year):
        # copy from month_timesheet_export_report.py
        hr_holiday_obj = self.env['hr.holidays.line']
        holiday_lines = hr_holiday_obj.search(domain)
        ls_day_duration = {}
        for line in holiday_lines:
            first_date = datetime.strptime(
                line.first_date, '%Y-%m-%d').date()
            last_date = datetime.strptime(
                line.last_date, '%Y-%m-%d').date()
            date = first_date
            while date <= last_date:

                date_in_week = date.strftime("%A")
                if date_in_week in ("Saturday", "Sunday"):
                    date = date + timedelta(1)
                    continue

                duration_hour = 8

                if date == first_date:
                    if line.first_date_type in ['morning', 'afternoon']:
                        duration_hour = 4

                elif date == last_date:
                    if line.last_date_type in ['morning', 'afternoon']:
                        duration_hour = 4

                if date.month == month and date.year == year:
                    ls_day_duration.update({
                        date.day: duration_hour
                    })
                date = date + timedelta(1)
        return ls_day_duration


HrEmLeaveSummaryReportXlsx('report.report.em.leave.summary.xlsx',
                           'tms.working.hour',)
