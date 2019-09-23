#!/usr/bin/env python
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

from openerp.report import report_sxw
from openerp.osv import osv


class ReportGlobalAnalysisPartner(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(ReportGlobalAnalysisPartner, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_total_dev_workload': self.get_total_dev_workload,
            'get_total_global_workload': self.get_total_global_workload,
            'get_workload_by_project': self.get_workload_by_project,
            'get_workload_by_activity': self.get_workload_by_activity,
            'get_support_ticket_by_user': self.get_support_ticket_by_user,
            'get_forge_ticket_by_user': self.get_forge_ticket_by_user,
        })

    def get_total_dev_workload(self, params):
        date_from = params['date_from']
        date_to = params['date_to']
        project_ids = params['project_ids'] if params['project_ids'] else [-1]
        activity_ids = params['activity_ids'] if params['activity_ids'] \
            else [-1]

        sql = """
        SELECT CAST(SUM(twh.duration_hour)/8 as DECIMAL(18,0))
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

        self.cr.execute(sql)
        total_dev_workload = self.cr.fetchone()[0]
        return total_dev_workload

    def get_total_global_workload(self, params):
        date_from = params['date_from']
        date_to = params['date_to']
        project_ids = params['project_ids'] if params['project_ids'] \
            else [-1]
        activity_ids = params['activity_ids'] if params['activity_ids'] \
            else [-1]

        sql = """
        SELECT CAST(SUM(twh.duration_hour)/8 as DECIMAL(18,0))
        FROM tms_working_hour as twh
        LEFT JOIN tms_activity AS ta ON twh.tms_activity_id = ta.id
        LEFT JOIN tms_project AS tp ON tp.id = ta.project_id
        LEFT JOIN res_users AS ru ON ru.id = twh.user_id
        LEFT JOIN hr_employee AS he ON he.id = ru.employee_id
        LEFT JOIN hr_job AS hj ON hj.id = he.job_id
        WHERE twh.date BETWEEN '%(date_from)s' AND '%(date_to)s'
        AND ( --if activity_id = -1 is get all activity
                (-1 = ANY(ARRAY[%(activity_id)s])) AND ta.id != -1
                OR --or not
                (NOT -1 = ANY(ARRAY[%(activity_id)s])) AND
                   ta.id = ANY(ARRAY[%(activity_id)s])
            )
            AND
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

        self.cr.execute(sql)
        total_global_workload = self.cr.fetchone()[0]
        return total_global_workload

    def get_workload_by_project(self, params):
        date_from = params['date_from']
        date_to = params['date_to']
        project_ids = params['project_ids'] if params['project_ids'] \
            else [-1]
        activity_ids = params['activity_ids'] if params['activity_ids'] \
            else [-1]

        sql = """
        WITH project_workload AS
        (SELECT dev.project_name,
                dev.dev_workload,
                global.global_workload
        FROM (
            --=== GET TIME SPENT OF DEVELOPERS ===
            SELECT CAST(SUM(twh.duration_hour)/8 as DECIMAL(18,0))
                    AS dev_workload,
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
            GROUP BY tp.id, tp.name) AS dev
        LEFT JOIN (
            --=== GET TIME SPENT GLOBAL ===
            SELECT CAST(SUM(twh.duration_hour)/8 as DECIMAL(18,0)) AS
                global_workload,
                    tp.id AS project_id,
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
             GROUP BY tp.id, tp.name) AS global
                            ON global.project_id = dev.project_id)
        SELECT row_to_json(project_workload)
        FROM project_workload""" % {'date_from': date_from,
                                    'date_to': date_to,
                                    'activity_id': activity_ids,
                                    'project_id': project_ids}

        self.cr.execute(sql)
        total_project_workload = self.cr.fetchall()
        return total_project_workload

    def get_workload_by_activity(self, params):
        date_from = params['date_from']
        date_to = params['date_to']
        project_ids = params['project_ids'] if params['project_ids'] \
            else [-1]
        activity_ids = params['activity_ids'] if params['activity_ids'] \
            else [-1]

        sql = """
        WITH activity_workload AS
        (SELECT dev.activity_name,
                dev.project_name,
                dev.dev_workload,
                global.global_workload
         FROM
            (-- === GET TOTAL TIME SPENT OF DEVELOPERS ===
             SELECT CAST(SUM(duration_hour/8) as DECIMAL(18,0))
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
             SELECT CAST(SUM(duration_hour/8) as DECIMAL(18,0))
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

        self.cr.execute(sql)
        total_activity_workload = self.cr.fetchall()

        return total_activity_workload

    def get_support_ticket_by_user(self, params):
        result = {}
        date_from = params['date_from']
        date_to = params['date_to']
        project_ids = params['project_ids'] if params['project_ids'] \
            else [-1]
        activity_ids = params['activity_ids'] if params['activity_ids'] \
            else [-1]

        sql = """
         WITH priority_ticket
         AS (SELECT Count(rp.name) AS total_priority_ticket,
                    rp.name        AS assignee,
                    rp.id          AS assignee_id,
                    CASE
                      WHEN tst.priority = 'major' THEN 'High'
                      WHEN tst.priority = 'urgent' THEN 'Very High'
                      WHEN tst.priority = 'normal' THEN 'Normal'
                      WHEN tst.priority = 'minor' THEN 'Low'
                      ELSE 'No Priority'
                    END AS priority
             FROM   tms_support_ticket AS tst
                    left join res_users AS ru
                           ON ru.id = tst.owner_id
                    left join res_partner AS rp
                           ON rp.id = ru.partner_id
             WHERE  tst.state != 'closed'
                    AND ( --if activity_id = -1 is get all activity
                        ( -1 = ANY ( array[%(activity_ids)s] ) )
                        AND ( tst.tms_activity_id != -1
                               OR tst.tms_activity_id IS NULL )
                        OR --or not
                        ( NOT -1 = ANY ( array[%(activity_ids)s] ) )
                        AND tst.tms_activity_id = ANY ( array[%(activity_ids)s]
                        ) )
                    AND ( --if project_id = -1 is get all activity
                        ( -1 = ANY ( array[%(project_id)s] ) )
                        AND tst.project_id != -1
                         OR --or not
                        ( NOT -1 = ANY ( array[%(project_id)s] ) )
                        AND tst.project_id = ANY ( array[%(project_id)s] ) )
             GROUP  BY rp.name,
                       rp.id,
                       tst.priority),
         total_ticket
         AS (SELECT CASE
                      WHEN tst.owner_id IS NULL THEN '-100'
                      ELSE rp.id
                    END AS assignee_id,
                    CASE
                      WHEN tst.owner_id IS NULL THEN 'No Owner'
                      ELSE rp.name
                    END AS assignee,
                    CASE
                      WHEN tst.owner_id IS NULL THEN '0'
                      ELSE tst.workload
                    END AS workload
             FROM   tms_support_ticket AS tst
                    left join res_users AS ru
                           ON ru.id = tst.owner_id
                    left join res_partner AS rp
                           ON rp.id = ru.partner_id
             WHERE  ( --if activity_id = -1 is get all activity
                    ( -1 = ANY ( array[%(activity_ids)s] ) )
                    AND ( tst.tms_activity_id != -1
                           OR tst.tms_activity_id IS NULL )
                     OR --or not
                    ( NOT -1 = ANY ( array[%(activity_ids)s] ) )
                    AND tst.tms_activity_id = ANY ( array[%(activity_ids)s] ) )
                    AND ( --if project_id = -1 is get all activity
                        ( -1 = ANY ( array[%(project_id)s] ) )
                        AND tst.project_id != -1
                         OR --or not
                        ( NOT -1 = ANY ( array[%(project_id)s] ) )
                        AND tst.project_id = ANY ( array[%(project_id)s] ) )),
         group_total_ticket
         AS (SELECT Count(assignee_id) AS total_ticket,
                    assignee_id,
                    assignee,
                    SUM(workload) AS total_workload
             FROM   total_ticket
             GROUP  BY assignee,
                       assignee_id),
         support_ticket_by_user
         AS (SELECT tt.assignee as name,
                    tt.assignee_id as id,
                    tt.total_workload as total_workload,
                    pt.priority,
                    SUM(pt.total_priority_ticket) AS total_priority_ticket,
                    tt.total_ticket
             FROM   group_total_ticket AS tt
                    left join priority_ticket AS pt
                           ON pt.assignee = tt.assignee
             GROUP  BY tt.assignee,
                       tt.assignee_id,
                       pt.priority,
                       tt.total_ticket,
                       tt.total_workload)
         SELECT row_to_json(support_ticket_by_user)
         FROM   support_ticket_by_user """ % {
            'date_from': date_from,
            'date_to': date_to,
            'activity_ids': activity_ids,
            'project_id': project_ids,
        }
        self.cr.execute(sql)
        result['total'] = {'data': {'name': 'Global',
                                    'total': 0,
                                    'Total Workload': 0,
                                    '%': 0.00,
                                    'Very High': 0,
                                    'Normal': 0,
                                    'High': 0,
                                    'Low': 0,
                                    'Open': 0, }, }
        for line in self.cr.fetchall():
            line_id = line[0]['id']
            if not (line_id in result):
                result[line_id] = {}
                result[line_id]['data'] = {
                    'name': line[0]['name'],
                    'total': line[0]['total_ticket'] or 0,
                    'Open': 0,
                    'Total Workload': line[0]['total_workload'] or 0,
                    '%': 0.00,
                    'Very High': 0,
                    'Normal': 0,
                    'High': 0,
                    'Low': 0, }
                result['total']['data']['total'] += \
                    result[line_id]['data']['total']
                result['total']['data']['Total Workload'] += \
                    result[line_id]['data']['Total Workload']
            if line[0]['priority']:
                result[line_id]['data'][line[0]['priority']] = \
                    line[0]['total_priority_ticket']
                result[line_id]['data']['Open'] += \
                    line[0]['total_priority_ticket']
                result['total']['data']['Open'] += \
                    line[0]['total_priority_ticket']
                result['total']['data'][line[0]['priority']] += \
                    result[line_id]['data'][line[0]['priority']]

            else:
                result[line_id]['data']['Very High'] = 0
                result[line_id]['data']['High'] = 0
                result[line_id]['data']['Normal'] = 0
                result[line_id]['data']['Low'] = 0

        res = []
        temp = 0.00
        res.append(result['total'])
        if not float(result['total']['data']['Open']):
            return res
        for key in result:
            if key == 'total':
                continue
            result[key]['data']['%'] = \
                round(float(result[key]['data']['Open']) /
                      float(result['total']['data']['Open']) * 100, 2)
            result['total']['data']['%'] += result[key]['data']['%']
            if result['total']['data']['%'] > 100.00:
                result['total']['data']['%'] = 100.00
                result[key]['data']['%'] = 100.00 - temp
            else:
                temp += result[key]['data']['%']
            res.append(result[key])
        return res

    def get_forge_ticket_by_user(self, params):
        result = {}
        date_from = params['date_from']
        date_to = params['date_to']
        project_ids = params['project_ids'] if params['project_ids'] \
            else [-1]
        activity_ids = params['activity_ids'] if params['activity_ids'] \
            else [-1]

        sql = """
         WITH priority_ticket
         AS (SELECT Count(rp.name) AS total_priority_ticket,
                    rp.name        AS assignee,
                    rp.id          AS assignee_id,
                    CASE
                      WHEN tft.priority = 'high' THEN 'High'
                      WHEN tft.priority = 'very_high' THEN 'Very High'
                      WHEN tft.priority = 'normal' THEN 'Normal'
                      WHEN tft.priority = 'low' THEN 'Low'
                    END AS priority
             FROM   tms_forge_ticket AS tft
                    left join res_users AS ru
                           ON ru.id = tft.owner_id
                    left join res_partner AS rp
                           ON rp.id = ru.partner_id
             WHERE  tft.state != 'closed'
                    AND ( --if activity_id = -1 is get all activity
                        ( -1 = ANY ( array[%(activity_ids)s] ) )
                        AND ( tft.tms_activity_id != -1
                               OR tft.tms_activity_id IS NULL )
                        OR --or not
                        ( NOT -1 = ANY ( array[%(activity_ids)s] ) )
                        AND tft.tms_activity_id = ANY ( array[%(activity_ids)s]
                        ) )
                    AND ( --if project_id = -1 is get all activity
                        ( -1 = ANY ( array[%(project_id)s] ) )
                        AND tft.project_id != -1
                         OR --or not
                        ( NOT -1 = ANY ( array[%(project_id)s] ) )
                        AND tft.project_id = ANY ( array[%(project_id)s] ) )
             GROUP  BY rp.name,
                       rp.id,
                       tft.priority),
         total_ticket
         AS (SELECT CASE
                      WHEN tft.owner_id IS NULL THEN '-100'
                      ELSE rp.id
                    END AS assignee_id,
                    CASE
                      WHEN tft.owner_id IS NULL THEN 'No Owner'
                      ELSE rp.name
                    END AS assignee,
                    CASE
                      WHEN tft.owner_id IS NULL THEN '0'
                      ELSE tft.time_spent
                    END AS time_spent,
                    CASE
                      WHEN tft.owner_id IS NULL THEN '0'
                      ELSE tft.time_spent
                    END AS time_spent_dev
             FROM   tms_forge_ticket AS tft
                    left join res_users AS ru
                           ON ru.id = tft.owner_id
                    left join res_partner AS rp
                           ON rp.id = ru.partner_id
             WHERE  ( --if activity_id = -1 is get all activity
                    ( -1 = ANY ( array[%(activity_ids)s] ) )
                    AND ( tft.tms_activity_id != -1
                           OR tft.tms_activity_id IS NULL )
                     OR --or not
                    ( NOT -1 = ANY ( array[%(activity_ids)s] ) )
                    AND tft.tms_activity_id = ANY ( array[%(activity_ids)s] ) )
                    AND ( --if project_id = -1 is get all activity
                        ( -1 = ANY ( array[%(project_id)s] ) )
                        AND tft.project_id != -1
                         OR --or not
                        ( NOT -1 = ANY ( array[%(project_id)s] ) )
                        AND tft.project_id = ANY ( array[%(project_id)s] ) )),
         group_total_ticket
         AS (SELECT Count(assignee_id) AS total_ticket,
                    assignee_id,
                    assignee,
                    SUM(time_spent) AS total_time_spent,
                    SUM(time_spent_dev) AS total_time_spent_dev
             FROM   total_ticket
             GROUP  BY assignee,
                       assignee_id),
         forge_ticket_by_user
         AS (SELECT tt.assignee as name,
                    tt.assignee_id as id,
                    tt.total_time_spent as total_time_spent,
                    tt.total_time_spent_dev as total_time_spent_dev,
                    pt.priority,
                    SUM(pt.total_priority_ticket) AS total_priority_ticket,
                    tt.total_ticket
             FROM   group_total_ticket AS tt
                    left join priority_ticket AS pt
                           ON pt.assignee = tt.assignee
             GROUP  BY tt.assignee,
                       tt.assignee_id,
                       pt.priority,
                       tt.total_ticket,
                       tt.total_time_spent,
                       tt.total_time_spent_dev)
         SELECT row_to_json(forge_ticket_by_user)
         FROM   forge_ticket_by_user """ % {
            'date_from': date_from,
            'date_to': date_to,
            'activity_ids': activity_ids,
            'project_id': project_ids,
        }
        self.cr.execute(sql)
        result['total'] = {
            'data': {'name': 'Global',
                     'total': 0,
                     'total time spend': 0,
                     'total time spend dev': 0,
                     '%': 0.00,
                     'Very High': 0,
                     'Normal': 0,
                     'High': 0,
                     'Low': 0,
                     'Open': 0, }, }
        for line in self.cr.fetchall():
            line_id = line[0]['id']
            if not (line_id in result):
                result[line_id] = {}
                result[line_id]['data'] = {
                    'name': line[0]['name'],
                    'total': line[0]['total_ticket'] or 0,
                    'total time spend': line[0]['total_time_spent'] or 0,
                    'total time spend dev':
                    line[0]['total_time_spent_dev'] or 0,
                    'Open': 0,
                    '%': 0.00,
                    'Very High': 0,
                    'Normal': 0,
                    'High': 0,
                    'Low': 0, }
                result['total']['data']['total'] += \
                    result[line[0]['id']]['data']['total']
                result['total']['data']['total time spend'] += \
                    result[line[0]['id']]['data']['total time spend']
                result['total']['data']['total time spend dev'] += \
                    result[line[0]['id']]['data']['total time spend dev']
            if line[0]['priority']:
                result[line_id]['data'][line[0]['priority']] = \
                    line[0]['total_priority_ticket']
                result[line_id]['data']['Open'] += \
                    line[0]['total_priority_ticket']
                result['total']['data']['Open'] += \
                    line[0]['total_priority_ticket']
                result['total']['data'][line[0]['priority']] += \
                    result[line_id]['data'][line[0]['priority']]

            else:
                result[line_id]['data']['Very High'] = 0
                result[line_id]['data']['High'] = 0
                result[line_id]['data']['Normal'] = 0
                result[line_id]['data']['Low'] = 0

        res = []
        temp = 0.00
        res.append(result['total'])
        if float(result['total']['data']['Open']) != 0:
            for key in result:
                if key != 'total':
                    result[key]['data']['%'] = \
                        round(float(result[key]['data']['Open']) /
                              float(result['total']['data']['Open']) * 100, 2)
                    result['total']['data']['%'] += result[key]['data']['%']
                    if result['total']['data']['%'] > 100.00:
                        result['total']['data']['%'] = 100.00
                        result[key]['data']['%'] = 100.00 - temp
                    else:
                        temp += result[key]['data']['%']
                    res.append(result[key])
        return res


class GlobalAnalysisPartner(osv.AbstractModel):
    _name = 'report.tms_modules.report_global_analysis_partner_template'
    _inherit = 'report.abstract_report'
    _template = 'tms_modules.report_global_analysis_partner_template'
    _wrapped_report_class = ReportGlobalAnalysisPartner
