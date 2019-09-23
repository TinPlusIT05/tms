# -*- coding: utf-8 -*-
##############################################################################
from datetime import datetime, timedelta
from openerp import models, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
import calendar as calendar
from itertools import groupby
from xlsxwriter import utility


class HrEmLeaveSummaryReportXlsx(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, objects):
        self.row = 0
        self.objects = objects

        # get year information
        self.year = data.get("year")

        # get monnth and period information
        (month, period) = data.get("update_to").strip().split("-")

        # convert month
        try:
            self.month = int(month)
        except Exception:
            # set month default is January
            self.month = 1
            Warning("Value of month had error")

        # get period information
        self.period = period or False

        # get filter condition
        self.team_ids = data.get("team_ids")
        self.condition_1 = data.get("condition_1")
        self.team_leader_ids = data.get("team_leader_ids")
        self.condition_2 = data.get("condition_2")
        self.leave_manager_ids = data.get("leave_manager_ids")

        # create and configuration workbook
        self._define_formats(workbook)
        self.sheet = workbook.add_worksheet(_(
            'Dedicated Team Leave ({0}-{1})'.format(
                data.get('year'), data.get('update_to')
            )))

        # generate report content
        self.generate_content()

    def generate_content(self):
        self._set_default_format()
        self.sheet.freeze_panes(2, 2)
        self.generate_headers()
        self.generate_table_content()
        self.gererate_footer()

    def generate_table_content(self):
        # get activity id
        # - the default is Day Off
        activities = []
        for name in ["Days Off"]:
            activity = self.env["tms.activity"].search(
                [("name", "=", name.strip())], limit=1
            )
            if activity:
                activities.append(activity.id)

        # get working day list exclude weekends and holiday
        if self.period and self.period == "1":
            # period = 1
            start_date = datetime(year=self.year, month=self.month, day=1)
            end_date = datetime(year=self.year, month=self.month, day=15)
            _, working_days = self._count_working_day(start_date, end_date)
        elif self.period and self.period == "2":
            # period = 2
            start_date = datetime(year=self.year, month=self.month, day=1)
            end_date = datetime(
                year=self.year, month=self.month,
                day=calendar.monthrange(self.year, self.month)[1]
            )
            _, working_days = self._count_working_day(start_date, end_date)

        # build employee filter condition 
        condition = ""
        #  - team condition
        team = "emp.team_id IN (" + ", ".join(map(str, self.team_ids)) + ")" \
            if self.team_ids else ""
        #  - team leader condition
        team_leader = "emp.parent_id IN (" + ", ".join(
            map(str, self.team_leader_ids)) + ")" \
            if self.team_leader_ids else ""
        #  - leave manager condition
        leave_manager = "emp.leave_manager_id IN (" + ", ".join(
            map(str, self.leave_manager_ids)) + ")" \
            if self.leave_manager_ids else ""
        #  - condition operator
        condition_1 = "" if not self.condition_1 else self.condition_1
        condition_2 = "" if not self.condition_2 else self.condition_2

        # condition processing
        #  - we must use the complicated merge condition because advoid sql error
        condition = condition + " {0} {1}".format(team, condition_1) \
            if self.team_ids else condition
        condition = condition + " {0}".format(team_leader) \
            if self.team_leader_ids else condition
        condition = condition + " {0} {1}".format(condition_2, leave_manager) \
            if self.leave_manager_ids else condition

        # collect all into params dict for integrate to leave sql 
        params = {
            "days": "(" + ", ".join(map(lambda x: "'{0}'".format(
                x.strftime("%Y-%m-%d")), working_days)) + ")",
            "activities": "(" + ", ".join(map(str, activities)) + ")",
            "condition": " AND ({0})".format(condition.strip())
            if condition != "" else condition,
        }

        # get employee sick leave infomation
        sql = """
            SELECT
                emp.id AS id,
                tms_wk_hr.date AS day,
                SUM(tms_wk_hr.duration_hour) AS hour
            FROM
                tms_working_hour tms_wk_hr
                JOIN res_users rs
                    ON tms_wk_hr.user_id = rs.id
                JOIN hr_employee emp
                    ON rs.employee_id = emp.id
            WHERE
                tms_wk_hr.tms_activity_id IN %(activities)s
                AND tms_wk_hr.date IN %(days)s%(condition)s
            GROUP BY
                emp.id,
                tms_wk_hr.date
            ORDER BY
                emp.id,
                tms_wk_hr.date
        """ % params

        self.env.cr.execute(sql)
        data = self.env.cr.dictfetchall()
        # data structure is list of dict with dict include:
        # {"id": ..., "day"(leave day): ..., "hour"(leave hour on day): ...}

        # get employee list match with employee filter condition
        sql = """
            SELECT
                id
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
                        ru.must_input_working_hour = TRUE
                        AND rs.active = TRUE
                    ) tb
                    ON tb.employee_id = emp.id%(condition)s
            ORDER BY
                id
        """ % ({
            "condition": " WHERE {0}".format(condition.strip())
            if condition != "" else ""
        })

        self.env.cr.execute(sql)
        employee_ids = self.env.cr.dictfetchall()
        # employee only list of dict {"id"(employee id): ...}

        # leave data processing
        #  - convert "working hour" to "working day" unit
        map(lambda x: x.update(
            {"hour": round(float(x.get("hour")) / 8, 2)}), data)
        # group leave data with employeed id and tranform to dict
        leave_data = {}
        for key, group in groupby(data, lambda x: x.get("id")):
            leave_data.update({key: list(group)})

        # generate column index on excel file alias form calendar day
        calendars = map(lambda x: x.strftime("%Y-%m-%d"), [
            start_date + timedelta(day_idx)
            for day_idx in range(0, (end_date - start_date).days + 1)
        ])

        # fill data to excel
        # iterate with employee id list
        for idx, emp_id in enumerate(employee_ids):
            self.row = self.row + 1

            # get employee name
            employee = self.env['hr.employee'].browse(emp_id.get("id"))

            # write "STT"
            self.sheet.write("A{0}".format(self.row + 1),
                             idx + 1, self.content_format)

            # write employee name
            self.sheet.write("B{0}".format(self.row + 1),
                             employee.name, self.content_format)

            # draw border cell for row (if not, some cell will no border)
            for col in range(2, len(calendars) + 2):
                self.sheet.write(self.row, col, "", self.content_format)

            # write leave day information
            #  - iterate on leave data (<dict>) only get "id" on "leave data"
            for item in leave_data.get(emp_id.get("id"), []):
                # if find "leave day" on "leave data"
                if item.get("day") in calendars:
                    # explain some complicated point:
                    #  - calendars.index(item.get("day")): find col to fill data
                    #       is calculated the index of "leave day" on "calendars" list
                    self.sheet.write(
                        self.row, calendars.index(item.get("day")) + 2,
                        item.get("hour"), self.content_number_format
                    )
            # write formula for "Total"
            # explain some complicated point:
            #  - xl_range(0, 0, 0, 3) >>> A0:A2
            self.sheet.write_formula(
                self.row, len(calendars) + 2,
                "= SUM({0})".format(
                    utility.xl_range(self.row, 2, self.row, len(calendars) + 1)
                ),
                self.content_number_format
            )
            # write formula for next col
            # explain some complicated point:
            #  - 17 if len(calendars) > 15 else 2
            #               ==> 17 for "period 2" and 2 for another
            self.sheet.write_formula(
                self.row, len(calendars) + 3,
                "= SUM({0})".format(
                    utility.xl_range(self.row, 17 if len(
                        calendars) > 15 else 2, self.row, len(calendars) + 1)
                ),
                self.content_number_format_w_bg
            )
            # write formula for next col
            # explain some complicated point:
            #  - xl_rowcol_to_cell(1, 1, row_abs=True, col_abs=True) ==> $B$2
            #       absolute cell address
            self.sheet.write_formula(
                self.row, len(calendars) + 4,
                "= {0} - {1}".format(
                    utility.xl_rowcol_to_cell(
                        1, len(calendars) + 4, row_abs=True, col_abs=True),
                    utility.xl_rowcol_to_cell(self.row, len(calendars) + 3)
                ),
                self.content_number_format_w_bg
            )

    def generate_headers(self):
        # define header and title content
        title = u'BẢNG TỔNG HỢP NGÀY NGHỈ PHÉP - DEDICATED TEAM'
        # init header list value
        headers = [
            u"STT",
            u"Tên",
        ]

        # check period; calculate working day and genrerate header
        if self.period and self.period == "1":
            col_range = 15
            # generate header content
            headers.extend([
                datetime(
                    month=self.month, year=self.year, day=day
                ).strftime("%d/%m") for day in range(1, 16)
            ])
            # calculate working day
            start_date = datetime(year=self.year, month=self.month, day=1)
            end_date = datetime(year=self.year, month=self.month, day=15)
            num_worked_day, _ = self._count_working_day(start_date, end_date)
        elif self.period and self.period == "2":
            col_range = calendar.monthrange(self.year, self.month)[1]
            # generate header content
            headers.extend([
                datetime(
                    month=self.month, year=self.year, day=day
                ).strftime("%d/%m") for day in range(1, col_range + 1)
            ])
            # calculate working day
            start_date = datetime(year=self.year, month=self.month, day=16)
            end_date = datetime(
                year=self.year, month=self.month, day=col_range
            )
            num_worked_day, _ = self._count_working_day(start_date, end_date)

        # add the last header col
        headers.append(u"Total")

        # generate title content
        self.row = 0
        self.sheet.merge_range(
            self.row, 0, self.row, col_range + 2,
            title, self.title_format
        )

        # genrate tail content
        self.sheet.write(
            self.row, col_range + 3,
            u"Tổng ngày nghỉ - giai đoạn {0} tháng {1}".format(
                self.period, self.month
            ),
            self.header_format_no_bold_w_bg
        )
        self.sheet.write(
            self.row, col_range + 4,
            u"Tổng số ngày công tính phí - giai đoạn {0} tháng {1}".format(
                self.period, self.month),
            self.header_format_no_bold_w_bg
        )
        # generate header content
        self.row = self.row + 1
        for idx, col in enumerate(headers):
            self.sheet.write(self.row, idx, col, self.header_format)
        self.sheet.write(self.row, col_range + 3, "", self.header_format_w_bg)
        # calculate and return working day
        self.sheet.write(self.row, col_range + 4,
                         num_worked_day, self.header_format_w_bg)

        # store col range
        self.col_range = col_range

    def gererate_footer(self):
        # content for footer
        content = u"Tổng số ngày nghỉ trong tháng"

        # add on sheet
        self.row = self.row + 1
        self.sheet.merge_range(
            self.row, 0, self.row, self.col_range + 1,
            content, self.header_format
        )

        for idx in range(2, 5):
            self.sheet.write_formula(
                self.row, self.col_range + idx,
                "= SUM({0})".format(utility.xl_range(
                    2, self.col_range + idx, self.row - 1, self.col_range + idx
                )),
                self.content_number_format_w_bg
            )

    def _count_working_day(self, start_date, end_date,
                           weekends=["Sat", "Sun"]):
        """
        - start_date    : starting date <datetime>
        - end_date      : ending date   <datetime>
        - weekends      : list of weekend day <list>
            - example: weekends = ["Sat", "Sun"]
        """
        # get list of holiday with year with condition between start day and end date
        # explain >>> search with condition
        #  - holiday must in range `start date` and `end date`
        holidays = self.env["hr.public.holiday"].search(
            [
                ("date", ">=", start_date.strftime("%Y-%m-%d")),
                ("date", "<=", end_date.strftime("%Y-%m-%d"))
            ]
        )

        # get standard day name list ==> return ["Mon", "Tue", ..., "Sun"]
        std_day_name = list(calendar.day_abbr)

        # double check and filter weekend list
        #  - sure for weekend list only day name list
        weekends = filter(lambda x: x in std_day_name, weekends)

        # get working day
        # fitter all day not in weekend and not in holiday list
        working_days = filter(
            lambda x: std_day_name[x.weekday()] not in weekends and
            x.strftime("%Y-%m-%d") not in set(holidays.mapped("date")),
            [
                start_date + timedelta(day_idx)
                for day_idx in range(0, (end_date - start_date).days + 1)
            ]
        )

        return (len(working_days), working_days)

    def _set_default_format(self):
        # two first column
        self.sheet.set_column('A:A', 4)
        self.sheet.set_column('B:B', 30)

        if self.period and self.period == "1":
            # when first period >>> col_range is 15 >>> day 1 -> day 15 of month
            col_range = 15
        elif self.period and self.period == "2":
            # when second period >>> col_range depend on number of day of month
            col_range = calendar.monthrange(self.year, self.month)[1]

        # set column with col_range index
        self.sheet.set_column(2, col_range + 1, 5)
        self.sheet.set_column(col_range + 2, col_range + 2, 8)
        self.sheet.set_column(col_range + 3, col_range + 4, 15)

        # set row
        self.sheet.set_row(0, 70)

    def _define_formats(self, workbook):
        base_format = {
            'border': False,
            'align': 'center',
            'bold': False,
            'italic': False,
            'font_name': 'Times New Roman',
            'font_size': 12,
            'valign': 'vcenter',
            'text_wrap': True,
        }
        self.base_format = workbook.add_format(base_format)

        # title format
        title_format = base_format.copy()
        title_format.update({
            'bold': True,
            'font_size': 14,
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
            'bold': True,
        })
        self.header_format = workbook.add_format(header_format)

        # header format
        header_format_w_bg = header_format.copy()
        header_format_w_bg.update({
            "bg_color": "#D6E7D1",
        })
        self.header_format_w_bg = workbook.add_format(header_format_w_bg)

        # header format no bold
        header_format_no_bold_w_bg = header_format.copy()
        header_format_no_bold_w_bg.update({
            "bold": False,
            "bg_color": "#D6E7D1",
        })
        self.header_format_no_bold_w_bg = workbook.add_format(
            header_format_no_bold_w_bg)

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

        # content format for number
        content_number_format_w_bg = content_format.copy()
        content_number_format_w_bg.update({
            'num_format': '#0.0;(#0.0)',
            "bg_color": "#D6E7D1",
        })
        self.content_number_format_w_bg = workbook.add_format(
            content_number_format_w_bg)


HrEmLeaveSummaryReportXlsx('report.report.dedicated.team.leave.xlsx',
                           'tms.working.hour',)
