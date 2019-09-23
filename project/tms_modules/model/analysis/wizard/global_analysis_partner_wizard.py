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
from openerp import models, fields, api
from datetime import date


class GlobalAnalysisPartnerWizard(models.TransientModel):
    _name = "global.analysis.partner.wizard"
    _description = "Global Analysis Partner Wizard"

    @api.model
    def _get_default_date_from(self):
        """
            TO DO:
                {Return the first date of current month}
        """
        return date(date.today().year, date.today().month, 1)

    date_from = fields.Date(
        string='Date From', default=_get_default_date_from,
        required=True)
    date_to = fields.Date(
        string='Date To', default=fields.Date.context_today,
        required=True)
    lang = fields.Char(
        string='Language',
        default=lambda self: self.env.user.lang)
    partner_id = fields.Many2one(
        'res.partner', 'Partner',
        domain=lambda self: [
            ("id", 'in', self.env['tms.project'].search(
                [('trobz_partner_id', '!=', False)]).mapped(
                "trobz_partner_id").ids)])

    project_ids = fields.Many2many(
        'tms.project', 'global_analysic_project_rel',
        'analysis_id', 'project_id', string='Projects',
        required=True,
        domain="[('trobz_partner_id', '!=', False)]")
    activity_ids = fields.Many2many(
        'tms.activity', 'global_analysic_activity_rel',
        'analysis_id', 'activity_id', string='Activities')
    result = fields.Html(string='Result', readonly=True)

    @api.onchange('project_ids')
    def onchange_project_ids(self):
        """
            TO DO:
            Filter the activities which are in the selected projects
        """
        if not self.project_ids:
            return {}
        return {'domain':
                {'activity_ids': [('project_id', 'in', self.project_ids.ids)]}}

    @api.multi
    def button_analyze(self):
        self.ensure_one()
        datas = {
            'form': self.read()[0]
        }
        rpname = 'tms_modules.report_global_analysis_partner_template'
        html = self.env['report'].get_html(self, rpname, data=datas)
        self.write({'result': html})
        return True

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
            TO DO:
            - Filter project of the selected partner
        """
        if not self.partner_id:
            return {}
        project = self.env['tms.project'].search([
            ('trobz_partner_id', '=', self.partner_id.id)])
        if not project:
            return {}
        self.project_ids = [(6, 0, project.ids)]
        return {'domain': {'project_ids': [('id', 'in', project.ids)]}}

    @api.multi
    def get_total_dev_workload(self):
        '''Get total dev workload'''
        date_from = self.date_from
        date_to = self.date_to
        project_ids = self.project_ids.ids if self.project_ids else [-1]
        activity_ids = self.activity_ids.ids if self.activity_ids \
            else [-1]

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
        AND twh.date BETWEEN '%(date_from)s'
        AND '%(date_to)s'
        AND (--if activity_id = -1 is get all activity
                (-1 = ANY(ARRAY[%(activity_id)s])) AND ta.id != -1
                   OR --or not
                   (NOT -1 = ANY(ARRAY[%(activity_id)s])) AND
                   ta.id = ANY(ARRAY[%(activity_id)s])
                ) AND
                ( --if project_id = -1 is get all activity
                   (-1 = ANY(ARRAY[%(project_id)s])) AND tp.id != -1
                   OR --or not
                   (NOT -1 = ANY(ARRAY[%(project_id)s])) AND
                   tp.id = ANY(ARRAY[%(project_id)s])
                )""" % {
            'date_from': date_from,
            'date_to': date_to,
            'activity_id': activity_ids,
            'project_id': project_ids,
        }

        self._cr.execute(sql)
        total_dev_workload = self._cr.fetchone()[0]
        return total_dev_workload

    @api.multi
    def get_total_global_workload(self):
        '''Get total global workload'''

        date_from = self.date_from
        date_to = self.date_to
        project_ids = self.project_ids.ids if self.project_ids else [-1]
        activity_ids = self.activity_ids.ids if self.activity_ids \
            else [-1]

        sql = """
        SELECT CAST(SUM(duration_hour/8) as DECIMAL(18,2))
        FROM tms_working_hour as twh
        LEFT JOIN tms_activity AS ta ON twh.tms_activity_id = ta.id
        LEFT JOIN tms_project AS tp ON tp.id = ta.project_id
        LEFT JOIN res_users AS ru ON ru.id = twh.user_id
        LEFT JOIN hr_employee AS he ON he.id = ru.employee_id
        LEFT JOIN hr_job AS hj ON hj.id = he.job_id
        WHERE twh.date BETWEEN '%(date_from)s'
        AND '%(date_to)s'
        AND ( --if activity_id = -1 is get all activity
                (-1 = ANY(ARRAY[%(activity_id)s])) AND ta.id != -1
                OR --or not
                (NOT -1 = ANY(ARRAY[%(activity_id)s])) AND
                ta.id = ANY(ARRAY[%(activity_id)s])
            ) AND
            ( --if project_id = -1 is get all activity
                (-1 = ANY(ARRAY[%(project_id)s])) AND tp.id != -1
                OR --or not
                (NOT -1 = ANY(ARRAY[%(project_id)s])) AND
                   tp.id = ANY(ARRAY[%(project_id)s])
            )""" % {
            'date_from': date_from,
            'date_to': date_to,
            'activity_id': activity_ids,
            'project_id': project_ids,
        }
        self._cr.execute(sql)
        total_global_workload = self._cr.fetchone()[0]
        return total_global_workload

    @api.multi
    def get_workload_by_project(self):
        '''Get workload by project'''

        date_from = self.date_from
        date_to = self.date_to
        project_ids = self.project_ids.ids if self.project_ids \
            else [-1]
        activity_ids = self.activity_ids.ids if self.activity_ids \
            else [-1]

        sql = """
        WITH project_workload AS
        (SELECT dev.project_name,
                dev.dev_workload,
                global.global_workload
        FROM (
            --=== GET TIME SPENT OF DEVELOPERS ===
            SELECT CAST(SUM(duration_hour/8) as DECIMAL(18,2)) AS dev_workload,
                tp.id AS project_id,
                tp.name AS project_name
            FROM tms_working_hour AS twh
            LEFT JOIN tms_activity AS ta ON twh.tms_activity_id = ta.id
            LEFT JOIN tms_project AS tp ON tp.id = ta.project_id
            LEFT JOIN res_users AS ru ON ru.id = twh.user_id
            LEFT JOIN hr_employee AS he ON he.id = ru.employee_id
            LEFT JOIN hr_job AS hj ON hj.id = he.job_id
            WHERE hj.id IN (
                SELECT id
                FROM hr_job
                WHERE name IN (
                'Senior Technical Consultant',
                'Technical Expert (Trainee)',
                'Technical Expert',
                'Technical Consultant (Trainee)',
                'Technical Consultant',
                'Lead Technical Consultant'))
            AND twh.date BETWEEN '%(date_from)s'
            AND '%(date_to)s'
            AND
               ( --if activity_id = -1 is get all activity
                   (-1 = ANY(ARRAY[%(activity_id)s]))
                                               AND ta.id != -1
                   OR --or not
                   (NOT -1 = ANY(ARRAY[%(activity_id)s])) AND
                   ta.id = ANY(ARRAY[%(activity_id)s])
               ) AND
               ( --if project_id = -1 is get all activity
                   (-1 = ANY(ARRAY[%(project_id)s]))
                                               AND tp.id != -1
                   OR --or not
                   (NOT -1 = ANY(ARRAY[%(project_id)s])) AND
                   tp.id = ANY(ARRAY[%(project_id)s])
               )
            GROUP BY tp.id, tp.name) AS dev
        LEFT JOIN (
            --=== GET TIME SPENT GLOBAL ===
            SELECT CAST(SUM(duration_hour/8) as DECIMAL(18,2)) AS
                global_workload,
                    tp.id AS project_id,
                    tp.name AS project_name
            FROM tms_working_hour AS twh
            LEFT JOIN tms_activity AS ta ON twh.tms_activity_id = ta.id
            LEFT JOIN tms_project AS tp ON tp.id = ta.project_id
            LEFT JOIN res_users AS ru ON ru.id = twh.user_id
            LEFT JOIN hr_employee AS he ON he.id = ru.employee_id
            LEFT JOIN hr_job AS hj ON hj.id = he.job_id
            WHERE twh.date BETWEEN '%(date_from)s'
                                       AND '%(date_to)s'
            AND
               ( --if activity_id = -1 is get all activity
                   (-1 = ANY(ARRAY[%(activity_id)s]))
                                                AND ta.id != -1
                   OR --or not
                   (NOT -1 = ANY(ARRAY[%(activity_id)s])) AND
                   ta.id = ANY(ARRAY[%(activity_id)s])
               ) AND
               ( --if project_id = -1 is get all activity
                   (-1 = ANY(ARRAY[%(project_id)s]))
                                                AND tp.id != -1
                   OR --or not
                   (NOT -1 = ANY(ARRAY[%(project_id)s])) AND
                   tp.id = ANY(ARRAY[%(project_id)s])
               )
             GROUP BY tp.id, tp.name) AS global
                            ON global.project_id = dev.project_id)
        SELECT row_to_json(project_workload)
        FROM project_workload""" % {
            'date_from': date_from,
            'date_to': date_to,
            'activity_id': activity_ids,
            'project_id': project_ids,
        }
        sql += '''
        ORDER BY
            project_name
        '''

        self._cr.execute(sql)
        total_project_workload = self._cr.fetchall()
        return total_project_workload

    @api.multi
    def get_workload_by_activity(self):
        '''Get workload by activity'''

        date_from = self.date_from
        date_to = self.date_to
        project_ids = self.project_ids.ids if self.project_ids \
            else [-1]
        activity_ids = self.activity_ids.ids if self.activity_ids \
            else [-1]

        sql = """
        WITH activity_workload AS
        (SELECT dev.project_name,
                dev.activity_name,
                dev.dev_workload,
                global.global_workload,
                dev.project_name
         FROM
            (-- === GET TOTAL TIME SPENT OF DEVELOPERS ===
                 SELECT CAST(SUM(duration_hour/8) as DECIMAL(18,2))
                 AS dev_workload,
                    ta.id AS activity_id,
                    ta.name AS activity_name,
                    tp.name AS project_name
             FROM tms_working_hour AS twh
             LEFT JOIN tms_activity AS ta ON twh.tms_activity_id = ta.id
             LEFT JOIN tms_project AS tp ON tp.id = ta.project_id
             LEFT JOIN res_users AS ru ON ru.id = twh.user_id
             LEFT JOIN hr_employee AS he ON he.id = ru.employee_id
             LEFT JOIN hr_job AS hj ON hj.id = he.job_id
             WHERE hj.id IN (
                 SELECT id
                 FROM hr_job
                 WHERE name IN
                   ('Senior Technical Consultant',
                    'Technical Expert (Trainee)',
                    'Technical Expert',
                    'Technical Consultant (Trainee)',
                    'Technical Consultant',
                    'Lead Technical Consultant'))
             AND twh.date BETWEEN '%(date_from)s' AND '%(date_to)s'
             AND
               ( --if activity_id = -1 is get all activity
                   (-1 = ANY(ARRAY[%(activity_id)s]))
                                               AND ta.id != -1
                   OR --or not
                   (NOT -1 = ANY(ARRAY[%(activity_id)s])) AND
                   ta.id = ANY(ARRAY[%(activity_id)s])
               ) AND
               ( --if project_id = -1 is get all activity
                   (-1 = ANY(ARRAY[%(project_id)s]))
                                                AND tp.id != -1
                   OR --or not
                   (NOT -1 = ANY(ARRAY[%(project_id)s])) AND
                   tp.id = ANY(ARRAY[%(project_id)s])
               )
             GROUP BY ta.id, ta.name, tp.name) AS dev
         LEFT JOIN
            (-- === GET TOTAL TIME SPENT GLOBAL ===
             SELECT CAST(SUM(duration_hour/8) as DECIMAL(18,2))
                                         AS global_workload,
                    ta.id AS activity_id,
                    ta.name AS activity_name,
                    tp.name AS project_name
             FROM tms_working_hour AS twh
             LEFT JOIN tms_activity AS ta ON twh.tms_activity_id = ta.id
             LEFT JOIN tms_project AS tp ON tp.id = ta.project_id
             LEFT JOIN res_users AS ru ON ru.id = twh.user_id
             LEFT JOIN hr_employee AS he ON he.id = ru.employee_id
             LEFT JOIN hr_job AS hj ON hj.id = he.job_id
             WHERE twh.date BETWEEN '%(date_from)s' AND '%(date_to)s'
             AND
                ( --if activity_id = -1 is get all activity
                   (-1 = ANY(ARRAY[%(activity_id)s]))
                                               AND ta.id != -1
                   OR --or not
                   (NOT -1 = ANY(ARRAY[%(activity_id)s])) AND
                   ta.id = ANY(ARRAY[%(activity_id)s])
               ) AND
               ( --if project_id = -1 is get all activity
                   (-1 = ANY(ARRAY[%(project_id)s]))
                                               AND tp.id != -1
                   OR --or not
                   (NOT -1 = ANY(ARRAY[%(project_id)s])) AND
                   tp.id = ANY(ARRAY[%(project_id)s])
               )
             GROUP BY ta.id, ta.name, tp.name) AS global
                 ON global.activity_id = dev.activity_id)
         SELECT row_to_json(activity_workload)
         FROM activity_workload""" % {
            'date_from': date_from,
            'date_to': date_to,
            'activity_id': activity_ids,
            'project_id': project_ids,
        }
        sql += '''
        ORDER BY
            project_name
        '''

        self._cr.execute(sql)
        total_activity_workload = self._cr.fetchall()
        return total_activity_workload

    @api.multi
    def get_support_ticket_by_user(self):
        '''Get support ticket by user'''

        date_from = self.date_from
        date_to = self.date_to
        project_ids = self.project_ids.ids if self.project_ids \
            else [-1]
        return self.env['tms.project']. \
            search([('id', 'in', project_ids)]). \
            get_support_ticket_by_user(date_from, date_to, False)

    @api.multi
    def get_forge_ticket_by_user(self):
        '''Get forge ticket by user'''

        date_from = self.date_from
        date_to = self.date_to
        project_ids = self.project_ids.ids if self.project_ids \
            else [-1]
        return self.env['tms.project']. \
            search([('id', 'in', project_ids)]). \
            get_forge_ticket_by_user(date_from, date_to, False)
