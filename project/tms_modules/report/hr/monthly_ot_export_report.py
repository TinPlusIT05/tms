# -*- coding: utf-8 -*-
##############################################################################
from datetime import datetime, timedelta
import calendar
from openerp import models, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
import logging


class MonthlyOTExportReport(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, objects):
        self.row = 0
        self.objects = objects
        self.data = data
        self._define_formats(workbook)
        self.sheet = workbook.add_worksheet(_('OT Summarize'))
        self.setup_config()
        # generate report content
        self.generate_content()

    def _define_formats(self, workbook):
        self.header_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'bold': True,
            'font_name': 'Times New Roman',
            'valign': 'vcenter',
            'text_wrap': True,
        })
        self.cell_border_center = workbook.add_format({
            'border': 1,
            'align': 'center',
            'font_name': 'Times New Roman'
        })

    def setup_config(self):
        self.sheet.set_column('A:A', 3)
        self.sheet.set_column('B:B', 20)
        self.sheet.set_column('C:C', 20)
        self.sheet.set_column('D:D', 20)
        self.sheet.set_column('E:E', 20)
        self.sheet.set_column('F:F', 20)
        self.sheet.set_column('G:G', 20)
        self.sheet.set_column('H:H', 20)
        self.sheet.set_column('I:I', 20)

    def generate_content(self):
        self.sheet.freeze_panes(4, 0)
        self.row = 5
        self.column = 0
        self.generate_headers()
        self.generate_table_context()

    def generate_headers(self):
        self.sheet.merge_range('A1:A4', 'STT', self.header_format)
        self.sheet.merge_range('B1:B4', 'Name of Employee', self.header_format)
        self.sheet.write('C1', 'Week Day', self.header_format)
        self.sheet.write('C2', '6:00 AM - 22:00 PM', self.header_format)
        self.sheet.write('C3', '150%', self.header_format)
        self.sheet.write('C4', '', self.header_format)
        self.sheet.merge_range('D1:E1', 'Shift Night WD', self.header_format)
        self.sheet.merge_range('D2:E2', '22:00 PM - 6:00 AM', self.header_format)
        self.sheet.write('D3', '200%', self.header_format)
        self.sheet.write('E3', '210%', self.header_format)
        self.sheet.write('D4', u'Chưa làm thêm ban ngày', self.header_format)
        self.sheet.write('E4', u'Đã làm thêm ban ngày', self.header_format)
        self.sheet.write('F1', 'Weekend', self.header_format)
        self.sheet.write('F2', '6:00 AM - 22:00 PM', self.header_format)
        self.sheet.write('F3', '200%', self.header_format)
        self.sheet.write('F4', '', self.header_format)
        self.sheet.write('G1', 'Shift Night WK', self.header_format)
        self.sheet.write('G2', '22:00 PM - 6:00 AM', self.header_format)
        self.sheet.write('G3', '270%', self.header_format)
        self.sheet.write('G4', '', self.header_format)
        self.sheet.write('H1', 'Holiday', self.header_format)
        self.sheet.write('H2', '6:00 AM - 22:00 PM', self.header_format)
        self.sheet.write('H3', '400%', self.header_format)
        self.sheet.write('H4', '', self.header_format)
        self.sheet.write('I1', 'Shift Night H', self.header_format)
        self.sheet.write('I2', '22:00 PM - 6:00 AM', self.header_format)
        self.sheet.write('I3', '490%', self.header_format)
        self.sheet.write('I4', '', self.header_format)

    def generate_table_context(self):
        month = self.data.get('month')
        year = self.data.get('year')

        ot_wd = self.env.ref('tms_modules.ot_weekday')
        ot_nwd_200 = self.env.ref(
            'tms_modules.ot_shift_night_weekday_200_percent')
        ot_nwd_210 = self.env.ref(
            'tms_modules.ot_shift_night_weekday_210_percent')
        ot_wk = self.env.ref('tms_modules.ot_weekend')
        ot_nwk = self.env.ref('tms_modules.ot_shift_night_weekend')
        ot_holiday = self.env.ref('tms_modules.ot_holiday')
        ot_nholiday = self.env.ref('tms_modules.ot_shift_night_holiday')

        hr_overtime_obj = self.env['monthly.overtime.sqlview']
        list_overtime = hr_overtime_obj.search([
            ('ot_month', '=', month),
            ('ot_year', '=', year)
        ], order='employee_id,overtime_type_id')
        stt = 1

        # prepare data
        datas = {}
        for line in list_overtime:
            if line.employee_id in datas:
                datas[line.employee_id].update({
                    line.overtime_type_id: line.duration})
            else:
                datas[line.employee_id] = {
                    line.overtime_type_id: line.duration}

        for emp in datas:
            # STT
            self.sheet.write(
                'A' + str(self.row),
                stt,
                self.cell_border_center
            )
            # Emp Name
            self.sheet.write(
                'B' + str(self.row),
                emp.name_related,
                self.cell_border_center
            )

            # Week Day
            if ot_wd in datas[emp]:
                self.sheet.write(
                    'C' + str(self.row),
                    '= %.2f * %.2f' % (datas[emp][ot_wd], 1.5),
                    self.cell_border_center,
                    datas[emp][ot_wd] * 1.5
                    )
            else:
                self.sheet.write(
                    'C' + str(self.row),
                    '',
                    self.cell_border_center
                    )
            # Shift Night WD 200
            if ot_nwd_200 in datas[emp]:
                self.sheet.write_formula(
                    'D' + str(self.row),
                    '= %.2f * %.2f' % (datas[emp][ot_nwd_200], 2),
                    self.cell_border_center,
                    datas[emp][ot_nwd_200] * 2
                    )
            else:
                self.sheet.write(
                    'D' + str(self.row),
                    '',
                    self.cell_border_center
                    )
            # Shift Night WD 210
            if ot_nwd_210 in datas[emp]:
                self.sheet.write_formula(
                    'E' + str(self.row),
                    '= %.2f * %.2f' % (datas[emp][ot_nwd_210], 2.1),
                    self.cell_border_center,
                    datas[emp][ot_nwd_210] * 2.1
                    )
            else:
                self.sheet.write(
                    'E' + str(self.row),
                    '',
                    self.cell_border_center
                    )
            # Weekend
            if ot_wk in datas[emp]:
                self.sheet.write_formula(
                    'F' + str(self.row),
                    '= %.2f * %.2f' % (datas[emp][ot_wk], 2),
                    self.cell_border_center,
                    datas[emp][ot_wk] * 2
                    )
            else:
                self.sheet.write(
                    'F' + str(self.row),
                    '',
                    self.cell_border_center
                    )
            # Shift Night WK
            if ot_nwk in datas[emp]:
                self.sheet.write_formula(
                    'G' + str(self.row),
                    '= %.2f * %.2f' % (datas[emp][ot_nwk], 2.7),
                    self.cell_border_center,
                    datas[emp][ot_nwk] * 2.7
                    )
            else:
                self.sheet.write(
                    'G' + str(self.row),
                    '',
                    self.cell_border_center
                    )
            # Holiday
            if ot_holiday in datas[emp]:
                self.sheet.write_formula(
                    'H' + str(self.row),
                    '= %.2f * %.2f' % (datas[emp][ot_holiday], 4.0),
                    self.cell_border_center,
                    datas[emp][ot_holiday] * 4
                    )
            else:
                self.sheet.write(
                    'H' + str(self.row),
                    '',
                    self.cell_border_center
                    )
            # Shift Night Holiday
            if ot_nholiday in datas[emp]:
                self.sheet.write_formula(
                    'I' + str(self.row),
                    '= %.2f * %.2f' % (datas[emp][ot_nholiday], 4.9),
                    self.cell_border_center,
                    datas[emp][ot_nholiday] * 4.9
                    )
            else:
                self.sheet.write(
                    'I' + str(self.row),
                    '',
                    self.cell_border_center
                    )
            self.row += 1
            stt += 1

MonthlyOTExportReport('report.report.workinghour.timesheet.ot.xlsx',
                      'hr.input.overtime',)
