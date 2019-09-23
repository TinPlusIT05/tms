# -*- coding: utf-8 -*-
##############################################################################
from datetime import datetime, timedelta
import calendar
from openerp import models, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.safe_eval import safe_eval
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from xlsxwriter.utility import xl_cell_to_rowcol
import logging

LEAVE_TYPE_FORMAT = {}
MAX_ROW_HEADERS = 3


class MonthlyTimesheetExportReport(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, objects):
        self.row = 0
        self.objects = objects
        self.data = data
        leave_type_ids = self.env['hr.holidays.status'].search([])
        self._define_formats(workbook, leave_type_ids)
        self.sheet = workbook.add_worksheet(_(
            'Monthly Timesheet %s-%s' % (data.get('month'), data.get('year'))))
        # generate report content
        self.generate_content(leave_type_ids)

    def _define_formats(self, workbook, leave_type_ids):
        header_format = {
            'border': 1,
            'align': 'center',
            'bold': True,
            'font_name': 'Times New Roman',
            'valign': 'vcenter',
            'text_wrap': True,
        }
        self.header_format = workbook.add_format(header_format)
        self.merge_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bold': True,
            'text_wrap': True,
            'font_name': 'Times New Roman'
        })
        self.format_header_italic = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'italic': True,
            'font_name': 'Times New Roman'
        })
        self.cell_border = workbook.add_format({
            'border': 1,
        })
        self.cell_border_center = workbook.add_format({
            'border': 1,
            'align': 'center',
            'font_name': 'Times New Roman'
        })
        self.cell_border_left = workbook.add_format({
            'border': 1,
            'align': 'left',
            'font_name': 'Times New Roman'
        })
        self.format_sat = workbook.add_format({
            'border': 1,
            'align': 'center',
            'fg_color': '#ffccb3',
            'font_name': 'Times New Roman'
        })
        self.format_sun = workbook.add_format({
            'border': 1,
            'align': 'center',
            'fg_color': '#9999ff',
            'font_name': 'Times New Roman'
        })
        self.cell_border_pbholiday = workbook.add_format({
            'border': 1,
            'align': 'center',
            'fg_color': '#4dff4d',
            'font_name': 'Times New Roman'
        })
        self.format_ls = workbook.add_format({
            'fg_color': '#ffff33',
            'border': 1,
            'align': 'center',
            'font_name': 'Times New Roman'
        })

        format_leave_type_basic = {
            'border': 1,
            'align': 'center',
            'fg_color': '#ffffff',
            'font_name': 'Times New Roman'
        }

        self.format_leave_type_0 = \
            workbook.add_format(format_leave_type_basic)
        LEAVE_TYPE_FORMAT.update({0: self.format_leave_type_0})
        for leave_type in leave_type_ids:
            format_leave_type_val = format_leave_type_basic.copy()
            format_leave_type_val.update({
                'fg_color': leave_type.color
            })
            self.format_leave_type = \
                workbook.add_format(format_leave_type_val)
            LEAVE_TYPE_FORMAT.update({
                leave_type.id: self.format_leave_type
            })

    def generate_content(self, leave_type_ids):
        self.sheet.freeze_panes(9, 2)
        self.row = 6
        self.column = 0
        self.generate_headers(leave_type_ids)
        self.generate_table_content()

    def generate_headers(self, leave_type_ids):
        cal = calendar.Calendar()
        year = self.data.get('year')
        month = self.data.get('month')
        dayofmonth = calendar.monthrange(year, month)[1]
        public_holiday = self.env['hr.public.holiday']
        day_public_holiday = public_holiday.search_count([
            ('year', '=', year),
            ('is_template', '=', False),
            ('date', '>=', '%s-%02d-%s' % (year, month, 1)),
            ('date', '<', '%s-%02d-%s' % (year, month+1, 1)),
        ])

        # Remark format leave type
        header_row_number = 0

        self.sheet.write('C1', '', self.cell_border_pbholiday)
        self.sheet.write('D1', 'Public Holidays', self.format_header_italic)
        color_row, color_col = xl_cell_to_rowcol('C1')
        descript_row, descript_col = xl_cell_to_rowcol('D1')
        header_row_number += 1

        for leave_type in leave_type_ids:
            if header_row_number < MAX_ROW_HEADERS:
                color_row += 1
                descript_row += 1
                self.sheet.write(
                    color_row, color_col,
                    '',
                    LEAVE_TYPE_FORMAT.get(leave_type.id))
                self.sheet.write(
                    descript_row, descript_col,
                    leave_type.name,
                    self.format_header_italic)
                header_row_number += 1
            else:
                header_row_number = 0
                color_row = descript_row = header_row_number
                color_col += 5
                descript_col += 5
                self.sheet.write(
                    color_row, color_col,
                    '',
                    LEAVE_TYPE_FORMAT.get(leave_type.id))
                self.sheet.write(
                    descript_row, descript_col,
                    leave_type.name,
                    self.format_header_italic)
                header_row_number += 1

        # Header Title
        table_created_col = descript_col + 5
        self.sheet.write(
            2, table_created_col,
            u'Ngày lập bảng:',
            self.format_header_italic)
        self.sheet.write(
            2, table_created_col + 4,
            datetime.today().strftime("%d/%m/%Y"),
            self.format_header_italic)

        self.sheet.set_column('A:A', 4)
        self.sheet.set_column('B:B', 18)
        self.sheet.merge_range(
            'A4:AH4',
            u'BẢNG CHẤM CÔNG %s NĂM %s' % (month, year),
            self.header_format
        )

        self.sheet.write(
            'W5',
            u'Total days in this month:',
            self.format_header_italic
        )
        self.sheet.write('AB5', dayofmonth, self.format_header_italic)

        self.sheet.write(
            'W6',
            u'No. of Business Days:',
            self.format_header_italic
        )
        # numbers of sunday and saturday in a current month
        nums_sat_sun = 0
        for week in calendar.monthcalendar(year, month):
            for day in week:
                if day == 0:
                    continue
                nameday = calendar.weekday(year, month, day)
                if calendar.day_abbr[nameday] in ['Sat', 'Sun']:
                    nums_sat_sun += 1

        self.sheet.write(
            'AB6',
            dayofmonth - nums_sat_sun,
            self.format_header_italic
        )
        headers = [
            'STT', 'EMP NAME', 'DayofMonth', 'Total annual leave ',
            'Total unpaid leave',
            'Total sick leave',
            'Total paid leave',
            'Business Trip',
            'Total actual working days',
            'Total used sick leave in %s' % (int(year)),
            'Total used annual leave in %s' % (int(year)),
            'Annual leave left until last year',
            'Annual Leave Left until this month',
            'Contract Type',
            'Hire Date',
            'Last Day at Work',
            'Remark'
        ]

        self.sheet.set_row(7, 30)
        for header in headers:
            if header != "DayofMonth":
                if header == "Business Trip":
                    self.sheet.merge_range(
                        self.row,
                        self.column,
                        self.row,
                        self.column + 2,
                        header,
                        self.header_format,
                    )
                    # column Inside HCMC
                    self.sheet.write(
                        self.row + 1,
                        self.column,
                        'Inside HCMC',
                        self.header_format,
                    )
                    self.column += 1
                    # column Outside HCMC
                    self.sheet.write(
                        self.row + 1,
                        self.column,
                        'Outside HCMC',
                        self.header_format,
                    )
                    self.column += 1
                    # column Abroad
                    self.sheet.write(
                        self.row + 1,
                        self.column,
                        'Abroad',
                        self.header_format,
                    )
                    self.column += 1
                else:
                    self.sheet.merge_range(
                        self.row,
                        self.column,
                        self.row + 1,
                        self.column,
                        header,
                        self.header_format,
                    )
                    self.column += 1
            else:
                ls_days = [
                    (calendar.day_abbr[
                        calendar.weekday(year, month, day)
                    ], day)
                    for day in cal.itermonthdays(year, month) if day
                ]
                for tod in ls_days:

                    if tod[0] == "Sat":
                        format_day = self.format_sat
                    elif tod[0] == "Sun":
                        format_day = self.format_sun
                    else:
                        format_day = self.cell_border_center
                    self.sheet.set_column(self.column, self.column, 3)
                    self.sheet.write(
                        self.row,
                        self.column, tod[0],
                        format_day)
                    self.sheet.write(
                        self.row+1,
                        self.column, tod[1],
                        format_day)
                    self.column += 1

        # STT yellow row
        num_col = self.column - 1
        col = 1
        while col <= num_col:
            self.sheet.write(8, 0, '', self.format_ls)
            self.sheet.write(8, col, col, self.format_ls)
            col += 1

    def generate_table_content(self):
        self.row += 3
        month = self.data.get('month')
        year = self.data.get('year')
        wk_hours = self.env['monthly.timesheet.sqlview'].search([
            ('month', '=', month),
            ('year', '=', year)
        ], order='employee_id')
        datas = {}
        endday = calendar.monthrange(year, month)[1]
        public_holiday = self.env['hr.public.holiday']
        day_public_holiday = public_holiday.search([
            ('year', '=', year),
            ('is_template', '=', False),
            ('date', '>=', '%s-%02d-%s' % (year, month, 1)),
            ('date', '<', '%s-%02d-%s' % (year, month+1, 1)),
        ])
        ls_public_holiday = [
            datetime.strptime(
                d.date, '%Y-%m-%d').day for d in day_public_holiday
        ]

        hr_contract_obj = self.env['hr.contract']

        # Prepare workday data
        for wk in wk_hours:
            if not datas.get(wk.employee_id, False):
                ls_day_data = {
                    d: 0 for d in range(1, endday+1)
                }
                datas[wk.employee_id] = ls_day_data
                datas[wk.employee_id].update({
                    wk.day: wk.working_time
                })
            else:
                datas[wk.employee_id].update({
                    wk.day: wk.working_time
                })
        stt = 1
        # Processing workday data
        funeral_leave_type = self.env.ref(
            'trobz_hr_holiday_vn.hr_holiday_status_funeral_special').id
        unpaid_type = self.env.ref('hr_holidays.holiday_status_unpaid').id
        sick_leave_type = self.env.ref('hr_holidays.holiday_status_sl').id
        casual_unpaid_type = self.env.ref(
            'trobz_hr_holiday_vn.hr_holiday_status_casual_unpaid').id
        casual_paid_type = self.env.ref('hr_holidays.holiday_status_cl').id
        annual_leave_type = self.env.ref('hr_holidays.holiday_status_cl')
        wedding_type = self.env.ref(
            'trobz_hr_holiday_vn.hr_holiday_status_wedding').id
        child_wedding_type = self.env.ref(
            'tms_modules.hr_holiday_status_children_wedding').id
        sick_leave_paid_type = self.env.ref(
            'trobz_hr_holiday_vn.hr_holiday_status_sick_paid').id,
        maternity_type = self.env.ref(
            'trobz_hr_holiday_vn.hr_holiday_status_maternity').id,
        sick_leave_si_type = self.env.ref(
            'tms_modules.tms_holidays_status_sick_leave_social_insurance').id
        accident_type = self.env.ref(
            'trobz_hr_holiday_vn.hr_holiday_status_accident').id
        compensatory_type = self.env.ref(
            'tms_modules.tms_holidays_status_compensatory_leave').id
        compensatory_work_type = self.env.ref(
            'tms_modules.tms_holidays_status_compensatory_work').id
        company_trip_type = self.env.ref(
            'tms_modules.tms_holidays_status_companytrip').id
        param_obj = self.env['ir.config_parameter']
        leave_type_unpaid_ids = param_obj.get_param(
            'leave_type_unpaid_ids', '[]')
        leave_type_unpaid_ids = safe_eval(leave_type_unpaid_ids)
        for emp in datas:
            emp_name = emp.name_related or ''
            self.sheet.write(self.row, 0, stt, self.cell_border_center)
            self.sheet.write(self.row, 1, emp_name, self.cell_border_left)

            # Prepare day off details
            # leave unpaid
            lu_domain = [
                ('employee_id', '=', emp.id),
                ('holiday_status_id', 'in', [
                    unpaid_type,
                    sick_leave_type,
                    casual_unpaid_type,
                ]),
                ('state', '=', 'validate'),
                '|',
                ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
                ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            ]
            vals_unpaid = self._get_leave_data(lu_domain, month, year)

            # Casual leave (paid)
            clp_domain = [
                ('employee_id', '=', emp.id),
                ('holiday_status_id', 'in', [casual_paid_type]),
                ('state', '=', 'validate'),
                '|',
                ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
                ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            ]
            vals_clp = self._get_leave_data(clp_domain, month, year)

            # Wedding
            wedding_domain = [
                ('employee_id', '=', emp.id),
                ('holiday_status_id', 'in', [
                    wedding_type,
                    child_wedding_type,
                ]),
                ('state', '=', 'validate'),
                '|',
                ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
                ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            ]
            vals_wedding = self._get_leave_data(wedding_domain, month, year)

            # Funeral of parents/parents-in-law/spouse/children
            funeral_domain = [
                ('employee_id', '=', emp.id),
                ('holiday_status_id', 'in', [funeral_leave_type]),
                ('state', '=', 'validate'),
                '|',
                ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
                ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            ]
            vals_funeral = self._get_leave_data(funeral_domain, month, year)

            # Sick leave (paid)
            slp_domain = [
                ('employee_id', '=', emp.id),
                ('holiday_status_id', 'in', [sick_leave_paid_type]),
                ('state', '=', 'validate'),
                '|',
                ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
                ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            ]
            vals_slp = self._get_leave_data(slp_domain, month, year)

            # Maternity
            maternity_domain = [
                ('employee_id', '=', emp.id),
                ('holiday_status_id', 'in', [maternity_type]),
                ('state', '=', 'validate'),
                '|',
                ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
                ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            ]
            vals_maternity = self._get_leave_data(
                maternity_domain, month, year)

            # Sick leave (Social Insurance)
            sli_domain = [
                ('employee_id', '=', emp.id),
                ('holiday_status_id', 'in', [sick_leave_si_type]),
                ('state', '=', 'validate'),
                '|',
                ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
                ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            ]
            vals_sli = self._get_leave_data(sli_domain, month, year)

            for d, wh in datas.get(emp).iteritems():
                format_cell = self.cell_border_center
                if d in ls_public_holiday:
                    format_cell = self.cell_border_pbholiday
                elif d in vals_unpaid:
                    leave_type_id = vals_unpaid.get('leave_type_id', 0)
                    format_cell = LEAVE_TYPE_FORMAT.get(leave_type_id)
                elif d in vals_clp:
                    leave_type_id = vals_clp.get('leave_type_id', 0)
                    format_cell = LEAVE_TYPE_FORMAT.get(leave_type_id)
                elif d in vals_wedding:
                    leave_type_id = vals_wedding.get('leave_type_id', 0)
                    format_cell = LEAVE_TYPE_FORMAT.get(leave_type_id)
                elif d in vals_funeral:
                    leave_type_id = vals_funeral.get('leave_type_id', 0)
                    format_cell = LEAVE_TYPE_FORMAT.get(leave_type_id)
                elif d in vals_slp:
                    leave_type_id = vals_slp.get('leave_type_id', 0)
                    format_cell = LEAVE_TYPE_FORMAT.get(leave_type_id)
                elif d in vals_maternity:
                    leave_type_id = vals_maternity.get('leave_type_id', 0)
                    format_cell = LEAVE_TYPE_FORMAT.get(leave_type_id)
                elif d in vals_sli:
                    leave_type_id = vals_sli.get('leave_type_id', 0)
                    format_cell = LEAVE_TYPE_FORMAT.get(leave_type_id)

                nod = calendar.day_abbr[calendar.weekday(year, month, d)]
                if nod == 'Sun':
                    format_cell = self.format_sun
                elif nod == 'Sat':
                    format_cell = self.format_sat

                self.sheet.write(self.row, d+1, wh or '', format_cell)

            next_column = endday + 2

            # Total annual leave
            al_domain = [
                ('employee_id', '=', emp.id),
                ('holiday_status_id', 'in', [casual_paid_type]),
                ('state', '=', 'validate'),
                '|',
                ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
                ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            ]
            vals_al = self._get_leave_data(al_domain, month, year)
            al = sum([wk for d, wk in vals_al.items()
                      if d != 'leave_type_id'])/8.0
            self.sheet.write(
                self.row, next_column,
                al and al or '',
                self.cell_border_center
            )
            next_column += 1

            # Total unpaid leave
            ul_domain = [
                ('employee_id', '=', emp.id),
                ('holiday_status_id', 'in', leave_type_unpaid_ids),
                ('state', '=', 'validate'),
                '|',
                ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
                ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            ]
            vals_ul = self._get_leave_data(ul_domain, month, year)
            ul = sum([wk for d, wk in vals_ul.items()
                      if d != 'leave_type_id'])/8.0
            self.sheet.write(
                self.row,
                next_column,
                ul and ul or '',
                self.cell_border_center
            )
            next_column += 1

            # Total sick leave
            slp_domain = [
                ('employee_id', '=', emp.id),
                ('holiday_status_id', 'in', [sick_leave_paid_type]),
                ('state', '=', 'validate'),
                '|',
                ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
                ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            ]
            vals_slp = self._get_leave_data(slp_domain, month, year)
            slp = sum([wk for d, wk in vals_slp.items()
                       if d != 'leave_type_id'])/8.0
            self.sheet.write(
                self.row,
                next_column,
                slp and slp or '',
                self.cell_border_center
            )
            next_column += 1

            # Total paid leave
            other_paid_type = leave_type_unpaid_ids + [
                casual_paid_type, sick_leave_paid_type]
            pl_domain = [
                ('employee_id', '=', emp.id),
                ('holiday_status_id', 'not in', other_paid_type),
                ('state', '=', 'validate'),
                '|',
                ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
                ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            ]
            vals_pl = self._get_leave_data(pl_domain, month, year)
            pl = sum([wk for d, wk in vals_pl.items()
                      if d != 'leave_type_id'])/8.0
            self.sheet.write(
                self.row,
                next_column,
                pl and pl or '',
                self.cell_border_center
            )
            next_column += 1
            # inside HCMC
            bti_domain = [
                ('employee_id', '=', emp.id),
                ('holiday_status_id', '=', self.env.ref(
                    'tms_modules.tms_holidays_status_bt_inside_hcmc').id),
                ('state', '=', 'validate'),
                '|',
                ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
                ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            ]
            vals_bti = self._get_leave_data(bti_domain, month, year)
            bti = sum([wk for d, wk in vals_bti.items()
                      if d != 'leave_type_id'])/8.0
            self.sheet.write(
                self.row,
                next_column,
                bti or '',
                self.cell_border_center
            )
            next_column += 1

            # outside HCMC
            bto_domain = [
                ('employee_id', '=', emp.id),
                ('holiday_status_id', '=', self.env.ref(
                    'tms_modules.tms_holidays_status_bt_outside_hcmc').id),
                ('state', '=', 'validate'),
                '|',
                ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
                ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            ]
            vals_bto = self._get_leave_data(bto_domain, month, year)
            bto = sum([wk for d, wk in vals_bto.items()
                      if d != 'leave_type_id'])/8.0
            self.sheet.write(
                self.row,
                next_column,
                bto or '',
                self.cell_border_center
            )
            next_column += 1

            # Abroad
            bta_domain = [
                ('employee_id', '=', emp.id),
                ('holiday_status_id', '=', self.env.ref(
                    'tms_modules.tms_holidays_status_bt_abroad').id),
                ('state', '=', 'validate'),
                '|',
                ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
                ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            ]
            vals_bta = self._get_leave_data(bta_domain, month, year)
            bta = sum([wk for d, wk in vals_bta.items()
                      if d != 'leave_type_id'])/8.0
            self.sheet.write(
                self.row,
                next_column,
                bta or '',
                self.cell_border_center
            )
            next_column += 1

            # Total actual working days
            dayofmonth = endday
            recs = self.env['monthly.timesheet.sqlview'].search([
                ('month', '=', month),
                ('year', '=', year),
                ('employee_id', '=', emp.id),
            ],)
            duration_curr_month = sum([
                wkm.working_time for wkm in recs
            ])/8.0
            self.sheet.write(
                self.row,
                next_column,
                duration_curr_month or '',
                self.cell_border_center
            )
            next_column += 1

            # Total No. of day charged
            # self.sheet.write(
            #     self.row,
            #     next_column,
            #     duration_curr_month + chpl + len(ls_public_holiday) or '',
            #     self.cell_border_center
            # )
            # next_column += 1

            # # Holidays of the government (PH)
            # self.sheet.write(
            #     self.row,
            #     next_column,
            #     len(ls_public_holiday) or '',
            #     self.cell_border_center
            # )
            # next_column += 1

            # # SIL
            # sil_domain = [
            #     ('employee_id', '=', emp.id),
            #     ('holiday_status_id', 'in', [
            #         wedding_type,
            #         child_wedding_type,
            #         funeral_leave_type
            #     ]),
            #     ('state', '=', 'validate'),
            #     '|',
            #     ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            #     ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            # ]
            # vals_sil = self._get_leave_data(sil_domain, month, year)
            # sil = sum([wk for d, wk in vals_sil.items()
            #           if d != 'leave_type_id'])/8.0
            # self.sheet.write(
            #     self.row,
            #     next_column,
            #     sil or '',
            #     self.cell_border_center
            # )
            # next_column += 1

            # # SIUL
            # siul_domain = [
            #     ('employee_id', '=', emp.id),
            #     ('holiday_status_id', 'in', [
            #         accident_type,
            #         maternity_type
            #     ]),
            #     ('state', '=', 'validate'),
            #     '|',
            #     ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            #     ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            # ]
            # vals_siul = self._get_leave_data(siul_domain, month, year)
            # siul = sum([wk for d, wk in vals_siul.items()
            #            if d != 'leave_type_id'])/8.0
            # self.sheet.write(
            #     self.row,
            #     next_column,
            #     siul or '',
            #     self.cell_border_center
            # )
            # next_column += 1

            # # CL (Compensatory leave)
            # cl_domain = [
            #     ('employee_id', '=', emp.id),
            #     ('holiday_status_id', '=', compensatory_type),
            #     ('state', '=', 'validate'),
            #     '|',
            #     ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            #     ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            # ]
            # vals_cll = self._get_leave_data(cl_domain, month, year)
            # cll = sum([wk for d, wk in vals_cll.items()
            #           if d != 'leave_type_id'])/8.0
            # self.sheet.write(
            #     self.row,
            #     next_column,
            #     cll or '',
            #     self.cell_border_center
            # )
            # next_column += 1

            # # CW (Compensatory Work)
            # cwl_domain = [
            #     ('employee_id', '=', emp.id),
            #     ('holiday_status_id', '=', compensatory_work_type),
            #     ('state', '=', 'validate'),
            #     '|',
            #     ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            #     ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            # ]
            # vals_cwl = self._get_leave_data(cwl_domain, month, year)
            # cll = sum([wk for d, wk in vals_cwl.items()
            #           if d != 'leave_type_id'])/8.0
            # self.sheet.write(
            #     self.row,
            #     next_column,
            #     '',
            #     self.cell_border_center
            # )
            # next_column += 1

            # # CT (Company trip)
            # ct_domain = [
            #     ('employee_id', '=', emp.id),
            #     ('holiday_status_id', '=', company_trip_type),
            #     ('state', '=', 'validate'),
            #     '|',
            #     ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            #     ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            # ]
            # vals_ct = self._get_leave_data(ct_domain, month, year)
            # ct = sum([wk for d, wk in vals_ct.items()
            #          if d != 'leave_type_id'])/8.0
            # self.sheet.write(
            #     self.row,
            #     next_column,
            #     ct or '',
            #     self.cell_border_center
            # )
            # next_column += 1

            # Total used sick leave in year
            total_used_sl_paid_domain = [
                ('employee_id', '=', emp.id),
                ('holiday_status_id', 'in', [sick_leave_paid_type]),
                ('state', '=', 'validate'),
                ('first_date', '>=', '%s-%02d-%s' % (year, 1, 1)),
            ]
            vals_used_slp = self._get_leave_data(
                total_used_sl_paid_domain, month, year)
            used_slp = sum([wk for d, wk in vals_used_slp.items()
                           if d != 'leave_type_id'])/8.0
            self.sheet.write(
                self.row,
                next_column,
                used_slp and used_slp or '',
                self.cell_border_center
            )
            next_column += 1

            # Total used annual leave in year
            total_used_al_paid_domain = [
                ('employee_id', '=', emp.id),
                ('holiday_status_id', 'in', [casual_paid_type]),
                ('state', '=', 'validate'),
                ('first_date', '>=', '%s-%02d-%s' % (year, 1, 1)),
            ]
            vals_used_al = self._get_leave_data(
                total_used_al_paid_domain, month, year)
            used_al = sum([wk for d, wk in vals_used_al.items()
                          if d != 'leave_type_id'])/8.0
            self.sheet.write(
                self.row,
                next_column,
                used_al and used_al or '',
                self.cell_border_center
            )
            next_column += 1

            # Annual leave left until last year
            allocation_left_last_year = annual_leave_type.get_days(
                emp.id, date_to='%s-12-31' % (year-1)
            )
            allocation_left_last_year = allocation_left_last_year[
                annual_leave_type.id]['remaining_leaves']
            self.sheet.write(
                self.row,
                next_column,
                allocation_left_last_year,
                self.cell_border_center
            )
            next_column += 1

            # Annual Leave Left until this month
            last_year = year
            last_month = month - 1
            if month == 1:
                last_year -= 1
                last_month = 12
            last_day = calendar.monthrange(last_year, last_month)[1]
            allocation_left_last_month = annual_leave_type.get_days(
                emp.id, date_to='%s-%s-%s' % (
                    last_year, last_month, last_day)
            )
            allocation_left_last_month = allocation_left_last_month[
                annual_leave_type.id]['remaining_leaves']
            self.sheet.write(
                self.row,
                next_column,
                allocation_left_last_month,
                self.cell_border_center
            )
            next_column += 1

            # # Annual Leave Left from current year
            # vals_hl = self._get_leave_data(hl_domain, month, year)
            # cpl = sum([wk for d, wk in vals_hl.items()
            #           if d != 'leave_type_id'])/8.0

            # if month == 1:
            #     num_annual = 12
            # else:
            #     f_month = 1
            #     cpl_curr = 0.0
            #     while f_month < month:
            #         cl_current_year_domain = [
            #             ('employee_id', '=', emp.id),
            #             ('holiday_status_id', '=', casual_unpaid_type),
            #             ('state', '=', 'validate'),
            #             '|',
            #             ('first_date', '>=', '%s-%02d-%s' % (year, f_month, 1)),
            #             ('last_date', '>=', '%s-%02d-%s' % (year, f_month, 1)),
            #         ]
            #         vals_curr_hl = self._get_leave_data(
            #             cl_current_year_domain, f_month, year)
            #         cpl_curr += sum([wk for d, wk in vals_curr_hl.items()
            #             if d != 'leave_type_id'])/8.0
            #         f_month += 1
            #     num_annual = 12 - cpl_curr

            # self.sheet.write(
            #     self.row,
            #     next_column,
            #     num_annual,
            #     self.cell_border_center
            # )
            # next_column += 1

            # # Emergency Medical Leave (EML)
            # heml_domain = [
            #     ('employee_id', '=', emp.id),
            #     ('holiday_status_id', '=', sick_leave_paid_type),
            #     ('state', '=', 'validate'),
            #     '|',
            #     ('first_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            #     ('last_date', '>=', '%s-%02d-%s' % (year, month, 1)),
            # ]
            # vals_heml = self._get_leave_data(heml_domain, month, year)
            # eml = sum([wk for d, wk in vals_heml.items()
            #     if d != 'leave_type_id'])/8.0
            # self.sheet.write(
            #     self.row,
            #     next_column,
            #     eml or '',
            #     self.cell_border_center
            # )
            # next_column += 1

            # # Balancing
            # self.sheet.write(
            #     self.row,
            #     next_column,
            #     num_annual - cpl or '',
            #     self.cell_border_center
            # )
            # next_column += 1

            # Type Contract
            contract = hr_contract_obj.search([
                ('employee_id', '=', emp.id),
            ], limit=1, order='id desc')

            self.sheet.write(
                self.row,
                next_column,
                contract.type_id.name,
                self.cell_border_center
            )
            next_column += 1

            # Hire date
            if contract.type_id.name == 'Trainee':
                hire_date = last_day_work = '-'
            else:
                hire_date = emp.hire_date
                last_day_work = contract.date_end

            self.sheet.write(
                self.row,
                next_column,
                hire_date,
                self.cell_border_center
            )
            next_column += 1

            # last day at work
            self.sheet.write(
                self.row, next_column,
                last_day_work and last_day_work or '-',
                self.cell_border_center
            )
            next_column += 1

            # Remark
            self.sheet.write(self.row, next_column, '',
                             self.cell_border_center)
            next_column += 1

            self.row += 1
            stt += 1

    def _get_leave_data(self, domain, month, year):
        hr_holiday_obj = self.env['hr.holidays.line']
        holiday_lines = hr_holiday_obj.search(domain)
        ls_day_duration = {}

        leave_type_id = 0
        holiday_status_id = holiday_lines.mapped('holiday_status_id')
        if holiday_status_id and len(holiday_status_id) == 1:
            leave_type_id = holiday_status_id[0].id
        ls_day_duration.update({'leave_type_id': leave_type_id})

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
                    if date.day in ls_day_duration:
                        ls_day_duration[date.day] += duration_hour
                    else:
                        ls_day_duration.update({
                            date.day: duration_hour
                        })
                date = date + timedelta(1)
        return ls_day_duration

MonthlyTimesheetExportReport('report.report.workinghour.timesheet.xlsx',
                             'tms.working.hour',)
