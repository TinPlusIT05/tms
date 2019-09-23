# -*- encoding: utf-8 -*-
from datetime import datetime, timedelta
from openerp import api, fields, models


class CalculateKpi(models.Model):
    _name = 'calculate.kpi'
    _rec_name = 'sprint'
    _description = 'Calculate KPI'

    sprint = fields.Date(string='Sprint')
    trobz_kpi_global = fields.Text(
        'Trobz KPI')
    trobz_kpi_developer = fields.Text(
        'Developers KPI')
    trobz_kpi_milestone = fields.Text(
        'Milestone KPI')

    @api.multi
    def button_calculate_kpi(self):
        daily_mail_obj = self.env['daily.mail.notification']
        for rec in self:
            sprint_next_day = (
                datetime.strptime(
                    rec.sprint, '%Y-%m-%d') +
                timedelta(days=7)).strftime('%Y-%m-%d')

            vals = {
                'trobz_kpi_global':
                daily_mail_obj.get_trobz_kpi_global(
                    rec.sprint, sprint_next_day),
                'trobz_kpi_developer':
                daily_mail_obj.get_trobz_kpi_developer(
                    rec.sprint, sprint_next_day),
                'trobz_kpi_milestone':
                daily_mail_obj.get_trobz_kpi_milestone(rec.sprint),
            }
            rec.write(vals)
        return True
