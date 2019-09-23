# -*- encoding: UTF-8 -*-
from datetime import datetime, timedelta

from openerp import api, models


class developer_productivity_in_sprint(models.TransientModel):

    _name = 'developer.productivity.in.sprint'
    _description = 'Developer Productivity In Sprint'

    @api.model
    def get_sprint(self):
        Daily = self.env['daily.mail.notification']
        context = dict(self._context or {})
        if context.get('sprint_date', False):
            sprint_date = context['sprint_date']
        else:
            sprint_date = Daily.get_previous_sprint(Daily.get_current_sprint())
            sprint_date = sprint_date and sprint_date.strftime('%Y-%m-%d') or\
                ''
        return sprint_date

    @api.model
    def get_developer_productivity(self, sprint_date):
        rs = '''
            <style type="text/css">
                table#api-table {
                border-collapse: collapse; font-size: 12.5px;}
                table#api-table tr td, table, tr th
                {padding: 5px; border: 1px solid #333;}
                table#api-table tr th, table tr td:first-child
                {font-weight: bold; text-align: center;}
                table#api-table tr th:not(:first-child)
                { background: #CCC; vertical-align: middle; }
                table#api-table tr td:not(:first-child){ text-align: right; }
            </style>
            <table cellpadding="5" border="1"
            style="border-collapse: collapse" id="api-table">
                <tr style="font-weight:bold; background: #DDD">
                    <th>Week</th>
                    <th>Developer</th>
                    <th>Capacity (%)</th>
                    <th>Capacity (hour)</th>
                    <th>Completed Hours</th>
                    <th>Productivity (%)</th>
                </tr>
        '''
        rs += self.get_productivity(sprint_date)
        rs += '</table>'
        return rs

    @api.model
    def get_productivity(self, sprint_date):
        employees = self.env['hr.employee'].search([
            ('job_id.name', 'ilike', 'Technical Consultant')
        ])
        working_hours = self.env['tms.working.hour']
        working_hours = working_hours.search([
            ('tms_forge_ticket_id', '!=', False),
            ('user_id.employee_id', 'in', employees.ids),
            ('sprint', '=', sprint_date)])
        tr_data = ''
        for employee in employees:
            weekly_capacity = employee.employee_capacity_weekly_ids.filtered(
                lambda c: c.start_date == sprint_date
            )
            production_rate = weekly_capacity and\
                weekly_capacity.production_rate or 0.0
            emp_wh = working_hours.filtered(
                lambda w: w.user_id.employee_id == employee
            )
            capacity_hour = 0.4 * production_rate
            completed_hour = 0
            forge_tickets = emp_wh.mapped('tms_forge_ticket_id')
            for forge_ticket in forge_tickets:
                cards = forge_ticket.card_ids.filtered(
                    lambda c: c.assignee_id.employee_id == employee
                )
                pct_complete = sum(cards.mapped('pct_complete'))
                completed_hour +=\
                    (pct_complete / 100) * forge_ticket.std_development_time
            productivity = capacity_hour and\
                round(100 * completed_hour / capacity_hour, 2) or 0.0
            tr_data += self.compute_tr_employee(
                sprint_date, employee, production_rate, capacity_hour,
                completed_hour, productivity
            )
        return tr_data

    @api.model
    def compute_tr_employee(self, sprint_date, employee, production_rate,
                            capacity_hour, completed_hour, productivity):
        tr_data = ''

        def get_effiency_color(efficiency):
            if efficiency > 80:
                # Green
                return 'green'
            elif efficiency < 70:
                # Red
                return 'red'
            return ''
        color = get_effiency_color(productivity)
        tr_data += '''
    <tr>
    <td style="color: %(color)s">%(sprint_date)s</td>
    <td style="color: %(color)s">%(employee_name)s</td>
    <td align="right" style="color: %(color)s">%(production_rate)s</td>
    <td align="right" style="color: %(color)s">%(capacity_hour)s</td>
    <td align="right" style="color: %(color)s">%(completed_hour)s</td>
    <td align="right" style="color: %(color)s">%(productivity)s</td>
    </tr>
            ''' % {
                'sprint_date': sprint_date,
                'color': color,
                'employee_name': employee.name,
                'production_rate': production_rate,
                'capacity_hour': capacity_hour,
                'completed_hour': completed_hour,
                'productivity': productivity,
                }
        return tr_data
