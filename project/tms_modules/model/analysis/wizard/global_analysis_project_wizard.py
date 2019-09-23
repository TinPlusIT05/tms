# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2017 Trobz (<http://trobz.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import fields, models, api
from datetime import date
from dateutil.rrule import DAILY, rrule, MO, TU, TH, FR, WE
from dateutil.parser import parse


class GlobalAnalysisProjectWizard(models.TransientModel):
    _name = 'global.analysis.project.wizard'
    _description = "Analysis Project Wizard"

    @api.model
    def _get_default_start_date(self):
        """
            TO DO:
                {Return the first date of current month}
        """
        return date(date.today().year, date.today().month, 1)

    project_id = fields.Many2one(
        comodel_name='tms.project',
        string="Project", required=True)
    start_date = fields.Date(
        string="Start Date",
        required=True,
        default=_get_default_start_date)
    end_date = fields.Date(
        string="End Date",
        required=True,
        default=fields.Date.context_today)
    activity_ids = fields.Many2many(
        'tms.activity',
        'global_analysis_partner_activity_rel',
        'analysis_id', 'activity_id',
        string='Activities')
    result = fields.Html(string='Result', readonly=True)

    @api.multi
    def button_view_analytics_result(self):
        """
            TO DO:
            - Button to render report
        """
        html = self.env['report'].get_html(
            self, "tms_modules.template_analysis_project",
        )
        self.write({'result': html})
        return True

    # get all activities of project
    @api.model
    def get_project_activities(self):
        """
            TO DO:
            - Get all activities of project
        """
        self.ensure_one()
        activities_cases = ['&', '|', '|', '|', '&', '&']
        activities_conditions = [('start_date', '>=', self.start_date),
                                 ('start_date', '<', self.end_date),
                                 '&', ('planned_date', '>=', self.start_date),
                                 ('planned_date', '<', self.end_date),
                                 '&', ('start_date', '<=', self.start_date),
                                 ('planned_date', '>=', self.end_date),
                                 '&', ('start_date', '>=', self.end_date),
                                 ('planned_date', '=', False),
                                 ('project_id', '=', self.project_id.id)]
        activities = self.env['tms.activity'].search([
            ('day_sold', '!=', 0.0), ('day_sold_dev', '!=', 0.0),
            ('project_id', '=', self.project_id.id)])
        working_hours = self.env['tms.working.hour'].search([
            ('tms_activity_id', 'not in', activities.ids),
            ('tms_activity_id.project_id', '=', self.project_id.id),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)])
        activities_wh = working_hours.mapped('tms_activity_id')
        list_activity = activities.ids + activities_wh.ids

        if self.activity_ids:
            activities_conditions.append(('id', 'in', self.activity_ids.ids))
        else:
            activities_conditions.append(('id', 'in', list_activity))
        domain = activities_cases + activities_conditions
        return self.env['tms.activity'].search(domain)

    @api.model
    def get_min_date(self, project_id):
        sql = '''SELECT Min(date)
                FROM tms_working_hour
                WHERE project_id  = %s
            ''' % (project_id)
        self.env.cr.execute(sql)
        mindate = self.env.cr.fetchall()
        if not mindate:
            return False
        return mindate[0][0]

    @api.model
    def get_project_all_activities(self, project_id):
        sql = '''SELECT id
                FROM tms_activity
                WHERE project_id  = %s
            ''' % (project_id)
        self.env.cr.execute(sql)
        activities = self.env.cr.fetchall()
        if not activities:
            return []
        activity_ids = [activity[0] for activity in activities]
        return self.env['tms.activity'].browse(activity_ids)

    @api.onchange('project_id')
    def onchange_project_id(self):
        """
            TO DO:
            - Filter the activities which are in the selected project
        """
        if not self.project_id:
            return {}
        return {'domain':
                {'activity_ids': [('project_id', '=', self.project_id.id)]}}

    @api.model
    def get_trobz_public_holidays_day(self, start_date, end_date):
        """
            TO DO:
            - Get trobz public day from "start date" to "end date"
        """
        pulic_holidays = self.env['hr.public.holiday'].search(
            [('date', '>=', start_date),
             ('date', '<=', end_date),
             ('is_template', '=', False)])
        pulic_holiday = [phol.date for phol in pulic_holidays]
        return pulic_holiday

    @api.model
    def get_date_work(self, start_date, end_date):
        """
            TO DO:
            - Get working dates
        """
        list_date_work = list(rrule(DAILY, byweekday=(MO, TU, WE, TH, FR),
                                    dtstart=parse(start_date),
                                    until=parse(end_date)))
        return list_date_work

    @api.model
    def count_day_work(self, start_date, end_date):
        """
            TO DO:
            - Count number of working days
            - working days = total working days - total public holidays
        """
        count_list_date_work = len(self.get_date_work(start_date, end_date))
        count_pulic_holiday = len(self.get_trobz_public_holidays_day(
            start_date, end_date))
        return count_list_date_work - count_pulic_holiday

    @api.model
    def compute_progress(self):
        """
            TO DO:
            - Compute average progress percent all activities of project
            to date
        """
        self.ensure_one()
        progress = 1.0
        activities_progress = []
        activities = self.get_project_activities()

        for activity in activities:
            if not activity.planned_date or \
                    activity.planned_date < self.end_date:
                activities_progress.append(100)
            else:
                days_work = self.count_day_work(
                    activity.create_date, activity.planned_date)
                days_progress = self.count_day_work(
                    activity.create_date, self.end_date)
                if not days_work:
                    activities_progress.append(100)
                else:
                    activities_progress.append(days_progress * 100 / days_work)
        if not activities_progress:
            return progress
        progress = round(
            sum(activities_progress) / len(activities_progress) / 100.0, 2)
        return progress

    @api.model
    def compute_progress_activity(self, activity):
        """
            TO DO:
            - Compute average progress percent an activity of project
            to date
        """
        self.ensure_one()
        progress = 1.0
        if not activity.planned_date or \
                activity.planned_date < self.end_date:
            return 1
        else:
            days_work = self.count_day_work(
                activity.create_date, activity.planned_date)
            days_progress = self.count_day_work(
                activity.create_date, self.end_date)
            if not days_work:
                return 1
            else:
                return round(days_progress * 1.0 / days_work, 2)
        return progress

    def get_number_of_days_spent_for_activities(
            self, activity_id, start_date, end_date, project_id=-1):
        sql = """
        SELECT CAST(SUM(duration_hour/8) as DECIMAL(18,2))
        FROM tms_working_hour as twh
        LEFT JOIN tms_activity AS ta ON twh.tms_activity_id = ta.id
        LEFT JOIN tms_project AS tp ON tp.id = ta.project_id
        LEFT JOIN res_users AS ru ON ru.id = twh.user_id
        LEFT JOIN hr_employee AS he ON he.id = ru.employee_id
        LEFT JOIN hr_job AS hj ON hj.id = he.job_id
        WHERE hj.id in (
            SELECT id
            FROM hr_job
            WHERE name IN (
                'Senior Technical Consultant',
                'Technical Expert (Trainee)',
                'Technical Expert',
                'Technical Consultant (Trainee)',
                'Technical Consultant',
                'Lead Technical Consultant'))
        AND twh.date BETWEEN '%(date_from)s' AND '%(date_to)s'
        AND ( --if activity_id = -1 is get all activity
                (-1 = ANY(ARRAY[%(activity_id)s])) AND ta.id != -1
                OR --or not
                (NOT -1 = ANY(ARRAY[%(activity_id)s]))
                    AND
                   ta.id = ANY(ARRAY[%(activity_id)s])
            )

        AND
            ( --if project_id = -1 is get all activity
                (-1 = ANY(ARRAY[%(project_id)s])) AND tp.id != -1
                OR --or not
                (NOT -1 = ANY(ARRAY[%(project_id)s])) AND
                   tp.id = ANY(ARRAY[%(project_id)s])
            )
        """ % {
            'date_from': start_date,
            'date_to': end_date,
            'activity_id': activity_id,
            'project_id': project_id}
        self._cr.execute(sql)
        day_spent = self._cr.fetchone()[0]
        return day_spent and day_spent or 0

    def get_activity_spent_on_forge_ticket(self, activity_ids,
                                           start_date, end_date):
        """
            TO DO:
            - Get time spent global for an activity
        """
        sql = """
        SELECT CAST(SUM(duration_hour/8) as DECIMAL(18,2))
        FROM tms_working_hour as twh
        LEFT JOIN tms_activity AS ta ON twh.tms_activity_id = ta.id
        LEFT JOIN tms_project AS tp ON tp.id = ta.project_id
        WHERE twh.date BETWEEN '%(date_from)s' AND '%(date_to)s'
        AND ta.id = ANY(ARRAY[%(activity_id)s])
        """ % {
            'date_from': start_date,
            'date_to': end_date,
            'activity_id': activity_ids}
        self._cr.execute(sql)
        day_spent = self._cr.fetchone()[0]
        return day_spent and day_spent or 0

    # get time for dev
    def get_spent_on_forge_ticket(self, start_date, end_date):
        forge_env = self.env['tms.forge.ticket']
        if start_date and end_date:
            domain = [('project_id', '=', self.project_id.id),
                      ('create_date', '>=', start_date),
                      ('create_date', '<=', end_date)]
        elif start_date:
            domain = [('project_id', '=', self.project_id.id),
                      ('create_date', '>=', start_date)]
        elif end_date:
            domain = [('project_id', '=', self.project_id.id),
                      ('create_date', '<=', end_date)]
        else:
            domain = [('project_id', '=', self.project_id.id)]
        indicators = forge_env.get_forge_indicators(domain)
        day_spent = float(indicators['spent']) / 8.0
        return day_spent

    # get time for activity
    def get_working_hours_activity(self, activity_id, start_date, end_date):
        if start_date and end_date:
            domain = [('tms_activity_id', '=', activity_id),
                      ('date', '>=', start_date),
                      ('date', '<=', end_date)]
        elif start_date:
            domain = [('tms_activity_id', '=', activity_id),
                      ('date', '>=', start_date)]
        elif end_date:
            domain = [('tms_activity_id', '=', activity_id),
                      ('date', '<=', end_date)]
        else:
            domain = [('tms_activity_id', '=', activity_id)]
        working_hours = self.env['tms.working.hour'].search(domain)
        sum_working_hour = sum(working_hours.mapped('duration_hour')) / 8
        return sum_working_hour

    # get time for project
    def get_working_hours_project(self, activities_ids, start_date, end_date):
        if start_date and end_date:
            domain = [('project_id', '=', self.project_id.id),
                      ('date', '>=', start_date),
                      ('date', '<=', end_date)]
        elif start_date:
            domain = [('project_id', '=', self.project_id.id),
                      ('date', '>=', start_date)]
        elif end_date:
            domain = [('project_id', '=', self.project_id.id),
                      ('date', '<=', end_date)]
        else:
            domain = [('project_id', '=', activities_ids)]
        if activities_ids != -1:
            domain += [('tms_activity_id', 'in', activities_ids)]
        working_hours = self.env['tms.working.hour'].search(domain)
        sum_working_hour = sum(working_hours.mapped('duration_hour')) / 8
        return sum_working_hour

    def get_support_ticket_by_user(self):
        date_from = self.start_date
        date_to = self.end_date
        return self.project_id.get_support_ticket_by_user(
            date_from, date_to, False)

    def get_forge_ticket_by_user(self):
        date_from = self.start_date
        date_to = self.end_date
        return self.project_id.get_forge_ticket_by_user(
            date_from, date_to, False)

    # calculate background-color
    def get_background_color(self, percent):
        if not percent or percent <= 90:
            return 'background-color:#A3E4D7;text-align:right !important;'
        if percent <= 102:
            return 'background-color:#D5F5E3;text-align:right !important;'
        if percent <= 110:
            return 'background-color:#F39C12;text-align:right !important;'
        return 'background-color:#E74C3C;text-align:right !important;'
