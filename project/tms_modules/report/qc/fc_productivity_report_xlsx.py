# -*- coding: utf-8 -*-
##############################################################################
import collections
from datetime import datetime, timedelta
from openerp import models, fields, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
import calendar as calendar

WEEKEND = [5, 6]
DAY_WORK_HOUR = 8


class ReportFcProductivityXlsx(ReportXlsx):

    HEADERS = collections.OrderedDict([
        ('employee_name', 'Name'),
        ('capacity_percent', 'Capacity (%)'),
        ('capacity_hours', 'Capacity (hours)'),
        ('qa_ticket_assigned', 'Total QA ticket assigned'),
        ('qc_estimate', 'Total QC estimate (h)'),
        ('total_time_spent_ticket', 'Total time spent (on ticket)'),
        ('absense_hours', 'Absence (h)'),
        ('total_time_spent_other', 'Total time spent on other activities'),
        ('total_working_hours', 'Total working hour'),
        ('total_tickets_closed', 'Total tickets closed'),
        ('total_tickets_repoened', 'Total tickets reopened'),
    ])

    def generate_xlsx_report(self, workbook, data, objects):
        self.row = 0
        self.objects = objects
        self.data = data
        self._define_formats(workbook)
        self.sheet = workbook.add_worksheet(_('FCs Productivity'))
        self.generate_report()

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
            'bold': True,
            'font_size': 12,
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

    def generate_report(self):
        self._set_default_format()
        self.sheet.freeze_panes(1, 1)
        self.generate_report_header()
        self.generate_report_content()

    def generate_report_header(self):
        col = 0
        for header in self.HEADERS:
            self.sheet.write(
                self.row, col, self.HEADERS.get(header), self.header_format)
            col += 1

    def generate_report_content(self):
        datas = self.get_report_data()
        # generate data table and export to excel
        self.row = 1
        for data in datas:
            col = 0
            for header in self.HEADERS:
                self.sheet.write(
                    self.row, col, data.get(header),
                    self.content_number_format)
                col += 1
            self.sheet.set_row(self.row, 20)
            self.row += 1

    def get_report_data(self):
        wizard_data = self.objects[0]
        from_date = wizard_data.from_date
        to_date = wizard_data.to_date
        work_hours = self.compute_work_hours(from_date, to_date)
        fc_profile = self.env.ref(
            'tms_modules.group_profile_tms_functional_consultant')
        params = {
            'work_hours': work_hours,
            'from_date': from_date,
            'to_date': to_date,
            'fc_profile_id': fc_profile.id,
        }

        sql_get_data = '''
SELECT
    em.id AS employee_id,
    re.name AS employee_name,
    em.current_employee_capacity AS capacity_percent,
    em.current_employee_capacity * %(work_hours)s / 100 AS capacity_hours,
    (
        SELECT COUNT(forge_id) FROM forge_ticket_assign
        WHERE assignee_id = ru.id AND assignee_id = (
            SELECT assignee_id
            FROM forge_ticket_assign
            WHERE DATE(date) >= '%(from_date)s' AND DATE(date) <= '%(to_date)s'
            ORDER BY date DESC
            LIMIT 1
        ) AND DATE(date) >= '%(from_date)s' AND DATE(date) <= '%(to_date)s'
    ) AS qa_ticket_assigned,
    (
        SELECT SUM(qc_estimate) FROM tms_forge_ticket
        WHERE id IN (
            SELECT forge_id FROM forge_ticket_assign
            WHERE assignee_id = ru.id AND assignee_id = (
                SELECT assignee_id
                FROM forge_ticket_assign
                WHERE DATE(date) >= '%(from_date)s'
                    AND DATE(date) <= '%(to_date)s'
                ORDER BY date DESC
                LIMIT 1
            ) AND DATE(date) >= '%(from_date)s' AND DATE(date) <= '%(to_date)s'
        )
    ) AS qc_estimate,
    (
        SELECT SUM(wh.duration_hour)
        FROM tms_working_hour AS wh
            JOIN tms_activity AS act ON act.id = wh.tms_activity_id
        WHERE wh.user_id = ru.id
            AND date >= '%(from_date)s' AND date <= '%(to_date)s'
            AND act.name = 'Functional Test'
            AND wh.tms_forge_ticket_id IN (
                SELECT forge_id FROM forge_ticket_assign
                WHERE assignee_id = ru.id AND date >= '%(from_date)s' AND date <= '%(to_date)s'
            )
    ) AS total_time_spent_ticket,
    (
        SELECT SUM(wh.duration_hour)
        FROM tms_working_hour AS wh
            JOIN tms_activity AS act ON act.id = wh.tms_activity_id
        WHERE wh.user_id = ru.id
            AND date >= '%(from_date)s' AND date <= '%(to_date)s'
            AND act.name = 'Days Off'
    ) AS absense_hours,
    (
        (SELECT SUM(wh.duration_hour)
        FROM tms_working_hour AS wh
        WHERE wh.user_id = ru.id
            AND date >= '%(from_date)s' AND date <= '%(to_date)s') -
        (SELECT SUM(wh.duration_hour)
        FROM tms_working_hour AS wh
            JOIN tms_activity AS act ON act.id = wh.tms_activity_id
        WHERE wh.user_id = ru.id
            AND date >= '%(from_date)s' AND date <= '%(to_date)s'
            AND act.name = 'Functional Test'
            AND wh.tms_forge_ticket_id IN (
                SELECT forge_id FROM forge_ticket_assign
                WHERE assignee_id = ru.id AND date >= '%(from_date)s' AND date <= '%(to_date)s'
            )) -
        (SELECT SUM(wh.duration_hour)
        FROM tms_working_hour AS wh
            JOIN tms_activity AS act ON act.id = wh.tms_activity_id
        WHERE wh.user_id = ru.id
            AND date >= '%(from_date)s' AND date <= '%(to_date)s'
            AND act.name = 'Days Off')
    ) AS total_time_spent_other,
    (
        SELECT SUM(wh.duration_hour)
        FROM tms_working_hour AS wh
        WHERE wh.user_id = ru.id
            AND date >= '%(from_date)s' AND date <= '%(to_date)s'
    ) AS total_working_hours,
    (
        SELECT COUNT(id) FROM tms_forge_ticket
        WHERE closed_by = ru.id AND state='closed'
            AND DATE(closing_datetime) >= '%(from_date)s'
            AND DATE(closing_datetime) <= '%(to_date)s'
    ) AS total_tickets_closed,
    (
        SELECT COUNT(reopen_forge_id)
        FROM (
            SELECT name
            FROM forge_ticket_reopening
            WHERE reopener_id = ru.id AND
                DATE(forge_ticket_reopening) >= '%(from_date)s' AND
                DATE(forge_ticket_reopening) <= '%(to_date)s'
            group by name
        ) AS reopen_forge_id
    ) AS total_tickets_repoened
FROM hr_employee AS em
    JOIN resource_resource AS re ON re.id = em.resource_id
    JOIN res_users AS ru ON ru.id = re.user_id
WHERE re.active = TRUE AND re.id IN (
    SELECT re.id
    FROM res_users AS u
        JOIN res_groups AS g ON u.group_profile_id = g.id
        JOIN resource_resource AS re ON re.user_id = u.id
    WHERE re.active = TRUE AND g.id=%(fc_profile_id)s
)
ORDER BY re.name
        '''
        self.env.cr.execute(sql_get_data % params)
        datas = self.env.cr.dictfetchall()
        return datas

    def _set_default_format(self):
        self.sheet.set_column('A:A', 30)
        self.sheet.set_column('B:B', 18)
        self.sheet.set_column('C:C', 18)
        self.sheet.set_column('D:D', 18)
        self.sheet.set_column('E:E', 18)
        self.sheet.set_column('F:F', 18)
        self.sheet.set_column('G:G', 18)
        self.sheet.set_column('H:H', 18)
        self.sheet.set_column('I:I', 18)
        self.sheet.set_column('J:J', 18)
        self.sheet.set_column('K:K', 18)

        self.sheet.set_row(0, 60)

    def compute_work_hours(self, from_date, to_date):
        """
        Compute work hours in range @from_date to @to_date, exclude public
        holidays and weekends
        """
        public_holiday_env = self.env['hr.public.holiday']
        from_date = fields.Date.from_string(str(from_date))
        to_date = fields.Date.from_string(str(to_date))
        delta = (to_date - from_date).days + 1
        count_days = 0
        for day in range(delta):
            process_date = from_date + timedelta(days=day)
            weekday = process_date.weekday()
            if weekday in WEEKEND:
                continue
            public_holidays = public_holiday_env.search([
                ('date', '=', str(process_date)),
                ('is_template', '=', False)])
            if public_holidays:
                continue
            count_days += 1
        return count_days * DAY_WORK_HOUR


ReportFcProductivityXlsx('report.report.fc.productivity.xlsx',
                           'fc.productivity.wizard',)
