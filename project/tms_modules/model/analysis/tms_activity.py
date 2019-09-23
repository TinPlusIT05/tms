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

from openerp import api, models, fields
from datetime import date, timedelta, datetime
from openerp.exceptions import Warning
from dateutil.rrule import DAILY, rrule, MO, TU, TH, FR, WE
import logging


class tms_activity(models.Model):
    _inherit = ['mail.thread']
    _name = "tms.activity"
    _description = "Activity"
    _order = "project_id, state, analytic_secondaxis_id, priority, name"

    @api.multi
    @api.depends('tms_forge_ticket_ids.time_spent')
    def _compute_forge_indicators(self):
        for activity in self:
            val = 0.0
            if activity and activity.id:
                sql = '''
                    SELECT sum(time_spent)
                    FROM tms_support_ticket
                    WHERE tms_activity_id = %s
                '''
                self._cr.execute(sql, (activity.id,))
                if self._cr.rowcount:
                    val = float(self._cr.fetchone()[0] or 0.0) / 8.0
            activity.day_spent = val
        return

    @api.depends('tms_support_ticket_ids.state',
                 'project_id.show_project_analysis',
                 'tms_support_ticket_ids.workload_char')
    def _compute_support_indicators(self):
        support_env = self.env['tms.support.ticket']
        for activity in self:
            indicators = support_env.get_support_indicators(
                [('tms_activity_id', '=', activity.id)])
            activity.day_planned = float(indicators['planned'])
            activity.day_remaining = float(indicators['remaining'])
            activity.workload_achieved = float(indicators['work_achive'])
            activity.progress = float(indicators['progress'])
        return

    @api.multi
    @api.depends('related_working_hours',
                 'related_working_hours.duration_hour')
    def _compute_working_hours_indicators(self):
        for activity in self:
            val = 0.0
            if activity and activity.id:
                sql = '''
                    SELECT sum(duration_hour)
                    FROM tms_working_hour
                    WHERE tms_activity_id = %s
                '''
                self._cr.execute(sql, (activity.id,))
                if self._cr.rowcount:
                    val = float(self._cr.fetchone()[0] or 0.0) / 8.0
            activity.day_spent_working_hours = val

    @api.multi
    @api.depends('resource_allocation_ids',
                 'resource_allocation_ids.employee_id')
    def _compute_completion_forecast(self):
        def _get_latest_production_rate(employee_id):
            today = fields.Date.today()
            capacity_env = self.env['hr.employee.capacity']
            latest_capacity = capacity_env.search(
                [('employee_id', '=', employee_id),
                 ('starting_date', '<', today)],
                order='starting_date desc', limit=1)

            if latest_capacity:
                return latest_capacity[0]
            return False

        for activity in self:
            sum_capacity = 0
            for resource in activity.resource_allocation_ids:
                latest_capacity = \
                    _get_latest_production_rate(resource.employee_id.id)

                if not latest_capacity:
                    sum_capacity += 0
                    continue
                sum_capacity += \
                    (resource.occupancy *
                     float(latest_capacity.production_rate) / 10000 * 4.75 / 7)

            today = date.today()
            if sum_capacity > 0:
                num_days = float(activity.day_remaining) / sum_capacity
                activity.completion_forecast = today + timedelta(num_days)
            else:
                activity.completion_forecast = today

    # code field use to sync working activity with TFA
    @api.multi
    @api.depends('name', 'project_id')
    def _get_code_name(self):
        for activity in self:
            if activity.project_id and activity.name:
                self.code = activity.project_id.name + " - " + activity.name

    # columns
    name = fields.Char(
        string='Name', size=128, required=True, help='Short description',
        track_visibility='onchange'
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner', string="Customer",
        readonly=True, required=True
    )
    project_id = fields.Many2one(
        comodel_name='tms.project', string='Project', required=True,
        track_visibility='onchange'
    )
    state = fields.Selection(
        [('planned', 'Planned'),
         ('in_progress', 'In progress'),
         ('closed', 'Done'),
         ('canceled', 'Canceled')],
        string='Global Status', required=True, default='planned',
        track_visibility='onchange'
    )
    analytic_secondaxis_id = fields.Many2one(
        comodel_name='analytic.secondaxis', string='Activity Type',
        required=True, track_visibility='onchange'
    )
    activity_category = fields.Selection(
        string='Activity Category',
        related='analytic_secondaxis_id.type',
        store=True
    )
    activity_reporting_date = fields.Date(
        'Activity Reporting Date', default=fields.Date.today(),
        help="This date will be used for reporting purpose")
    owner_id = fields.Many2one(
        comodel_name='res.users', string="Owner",
        domain="[('is_trobz_member','=', True)]",
        help='The person in charge of making this activity successful: '
             'Happy Customer, Happy Team and Profitable.',
        track_visibility='onchange',
    )
    active = fields.Boolean(
        'Active', track_visibility='onchange', default=True)
    priority = fields.Selection(
        [('high', 'High'),
         ('normal', 'Normal'),
         ('low', 'Low')], string='Priority',
        required=True, default='normal',
    )
    resource_allocation_ids = fields.One2many(
        comodel_name='hr.resource.allocation', inverse_name='activity_id',
        string='Resource Allocation'
    )
    completion_forecast = fields.Date(
        compute='_compute_completion_forecast',
        string='Completion Forecast',
        help="today + Remaining time (in days) / " +
        "(sum(allocation_resource.occupancy_pct allocation_resource." +
        "employee.production_rate(today) 4.75 / 7 )). The 4.75 " +
        "represents the average number of working days per week.",
        store=True
    )
    tms_forge_ticket_ids = fields.One2many(
        comodel_name='tms.forge.ticket',
        inverse_name='tms_activity_id', string='Related Forge Tickets'
    )
    tms_support_ticket_ids = fields.One2many(
        comodel_name='tms.support.ticket', inverse_name='tms_activity_id',
        string='Related Support Tickets'
    )
    planned_date = fields.Date(
        'Delivery Deadline', help='Expected date of issue of the invoice.'
    )
    is_billable = fields.Boolean(
        'Billable', default=True,
        help='This activity is invoiced directly or indirectly. ' +
        'Non billable activities are: Internal' +
        ' Meeting, Happy Hours, Demo...',
        track_visibility='onchange'
    )
    description = fields.Text('Description')
    comment = fields.Text('Comment')
    account_id = fields.Many2one(
        comodel_name='account.analytic.account', string='Analytic Account',
        track_visibility='onchange'
    )
    day_planned = fields.Float(
        compute='_compute_support_indicators', default=0.0,
        string='Estimate on Support Tickets (in days)', store=True
    )
    day_spent = fields.Float(
        compute='_compute_forge_indicators', default=0.0,
        string='Time Spent on Forge Ticket (in days)', store=True
    )
    day_spent_working_hours = fields.Float(
        compute='_compute_working_hours_indicators', default=0.0,
        string='Total Time Spent from Working Hours (in days)', store=True
    )
    day_remaining = fields.Float(
        compute='_compute_support_indicators', default=0.0,
        string='Remaining time (in days)', store=True
    )
    progress = fields.Float(
        compute='_compute_support_indicators', default=0.0,
        string='Progress', store=True
    )
    day_sold_dev = fields.Float(
        'Time Sold for dev (in days)', digits=(16, 2),
        track_visibility='onchange',
    )
    day_sold = fields.Float(
        'Total Time Sold (in days)', digits=(16, 2),
        track_visibility='onchange'
    )
    related_working_hours = fields.One2many(
        comodel_name='tms.working.hour', inverse_name='tms_activity_id',
        string='Related Working Hours'
    )
    working_hours_requires_ticket = fields.Boolean(
        'Working Hours requires ticket',
        help="Employees will need to set a forge ticket \
        or support ticket on the working hours for this activity",
        track_visibility='onchange', default=True
    )
    project_type_id = fields.Many2one(
        related='project_id.project_type_id',
        comodel_name='tms.project.type',
        string='Project Type',
        readonly=True, store=True)
    framework_version_id = fields.Many2one(
        related='project_id.framework_version_id',
        comodel_name='tms.framework.version',
        string='Framework Version',
        readonly=True, store=True)
    invoiceable = fields.Boolean(
        string="Invoiceable by Trobz Vietnam (Default)",
        default=True,
        track_visibility='onchange')
    code = fields.Char(
        compute='_get_code_name',
        size=200, string="Code", store=True
    )
    overide_project_customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Override Project Customer')
    team_id = fields.Many2one(
        'hr.team', string='Team',
        required=True
    )
    status_ids = fields.One2many(
        string='Status',
        comodel_name='activity.status',
        inverse_name='activity_id')
    tasks_ids = fields.One2many(
        string='Tasks',
        comodel_name='activity.task',
        inverse_name='activity_id')
    next_expected_deadline = fields.Date(
        string='Next Expected Deadline',
        compute='_compute_next_expected_deadline')
    next_real_deadline = fields.Date(
        string='Next Review Date')
    links_ids = fields.One2many(
        string='Links',
        comodel_name='activity.link',
        inverse_name='activity_id')
    dtm_workload = fields.Float(
        string='DTM Workload (for next month)')
    recurring_workload = fields.Float(
        string='Recurring Workload (for a month)')
    extra_workload = fields.Float(
        string='Non-recurring Workload (for 3 months)')
    probability = fields.Float(
        string='Probability (%)')
    total_workload = fields.Float(
        string='Total Rough Workload (3 months)',
        compute='_compute_total_workload')
    support_ticket_count = fields.Integer(
        string="Support Tickets",
        compute="_compute_support_ticket_count")
    activity_task_count = fields.Integer(
        string="All Tasks",
        compute="_compute_activity_task_count")
    forge_ticket_count = fields.Integer(
        string="Forge Tickets",
        compute="_compute_forge_ticket_count")
    working_duration_count = fields.Float(
        string="Working Hours",
        compute="_compute_working_hours")
    need_review = fields.Boolean(
        string='Need Review',
        default=True)
    date_start = fields.Date('Date start')
    date_end = fields.Date('Date end')
    workload_achieved = fields.Float(
        compute='_compute_support_indicators', digits=(16, 2),
        string="Workload Achieved (in days)", store=True)

    start_date = fields.Date(
        'Start Date Activity',
        default=fields.Date.context_today)

    job_type_ids = fields.Many2many(
        'tms.job.type',
        'activity_job_type_rel', 'activity_id', 'job_type_id',
        string='Allowed Job Types',
        help='It uses to define the appropriate Job Types for specific '
             'Activity. In case this field is empty, '
             'all Job Types will be allowed.'
    )

    @api.multi
    def name_get(self):
        """
        Override function:
        Display activity: <project name - activity name>
        """
        if not self.ids:
            return []

        result = []
        state = {'planned': 'Planned',
                 'in_progress': 'In progress',
                 'closed': 'Done',
                 'canceled': 'Canceled'}
        for activity in self:
            result.append(
                (activity.id, '%s - %s - %s'
                 % (activity.project_id.name, activity.name,
                    state[activity.state])
                 )
            )
        return result

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = dict(self._context or {})
        if 'search_activities_based_on_project_ids' in context:
            project_vals = context['search_activities_based_on_project_ids']
            project_ids = project_vals[0][2]
            args.append(('project_id', 'in', project_ids))
        if 'search_by_project_ids' in context:
            contract_project_ids = context['search_by_project_ids'][0][2]
            args.append(('project_id', 'in', contract_project_ids))
        return super(tms_activity, self).search(
            args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """
        Override function:
        Allow to search by project name and activity name
        """
        args = args or []
        recs = self.search(args)
        ids = recs.ids
        if name:
            sql = """
            SELECT a.id
            FROM tms_activity a
            JOIN tms_project p
            ON a.project_id = p.id
            WHERE p.name || ' - ' || a.name %s '%%%s%%'
            """ % (operator, name.replace("'", ""))
            self._cr.execute(sql)
            activity_ids = [activity_id[0]
                            for activity_id in self._cr.fetchall()]

            ids = list(set(ids).intersection(activity_ids))
            recs = self.browse(ids)
        return recs.name_get()

    @api.model
    def create(self, vals):
        """
        Set partner on activity = partner on the linked project.
        When the status of an activity is set to Done or Canceled,
        automatically mark the activity as inactive
        """
        if vals.get('project_id', False):
            if not isinstance(vals['project_id'], int):
                vals['project_id'] = int(vals['project_id'])
            project = self.env['tms.project'].browse(vals['project_id'])
            vals['partner_id'] = project and project.partner_id and \
                project.partner_id.id or False
        # Inactive closed/cancelled activity
        if vals.get('state', False) in ['closed', 'canceled']:
            vals['active'] = False
        else:
            vals['active'] = True
        return super(tms_activity, self).create(vals)

    @api.multi
    def write(self, vals):
        """
        Set partner on activity = partner on the linked project.
        When the status of an activity is set to Done or Canceled,
        automatically mark the activity as inactive
        """
        if vals.get('project_id', False):
            if not isinstance(vals['project_id'], int):
                vals['project_id'] = int(vals['project_id'])
            project = self.env['tms.project'].browse(vals['project_id'])
            vals['partner_id'] = project and project.partner_id and \
                project.partner_id.id if project else False

        # Inactive closed/cancelled activity
        if vals.get('state', False) in ['closed', 'canceled']:
            # F#29929 Check support contracts related
            for rec in self:
                rec.check_support_contracts(rec.id)
            vals['active'] = False
        else:
            vals['active'] = True
        res = super(tms_activity, self).write(vals)

        new_vals = {}
        if vals.get('project_id', False):
            new_vals.update({'project_id': vals['project_id']})
        if vals.get('analytic_secondaxis_id', False):
            new_vals.update({
                'analytic_secondaxis_id': vals['analytic_secondaxis_id']})
        if vals.get('account_id', False):
            new_vals.update({'account_id': vals['account_id']})

        if not new_vals:
            return res

        related_working_hour_ids = []
        for tms_act in self:
            if tms_act.related_working_hours:
                related_working_hour_ids += tms_act.related_working_hours.ids

        tms_working_hour_env = self.env['tms.working.hour']
        tms_working_hours = tms_working_hour_env.browse(
            related_working_hour_ids)
        tms_working_hours.write(new_vals)

        return res

    @api.model
    def function_update_conflict_working_hour_related_to_activity(self):
        logging.info("====== START: CONFLICT WORKING HOUR RELATED TO ACTIVITY "
                     "=======")
        for rec in self.search([]):
            for related_working_hour in rec.related_working_hours:
                vals = {}
                if related_working_hour.project_id.id != \
                        rec.project_id.id:
                    vals.update({'project_id': rec.project_id.id})
                if related_working_hour.account_id.id != \
                        rec.account_id.id:
                    vals.update({'account_id': rec.account_id.id})
                if related_working_hour.analytic_secondaxis_id.id != \
                        rec.analytic_secondaxis_id.id:
                    vals.update({
                        'analytic_secondaxis_id':
                            rec.analytic_secondaxis_id.id})
                if not vals:
                    continue
                related_working_hour.write(vals)
        logging.info("====== END: CONFLICT WORKING HOUR RELATED TO ACTIVITY "
                     "=======")
        return True

    @api.onchange('project_id')
    def onchange_project_id(self):
        # TODO return domain
        # proj_partner = self.project_id.partner_id and \
        #    self.project_id.partner_id.id or False
        #    domain = {'account_id': [('partner_id', '=', proj_partner)]}
        if self.project_id:
            self.invoiceable = self.project_id.invc_by_trobz_vn or False

    @api.onchange('team_id')
    def _onchange_team_id(self):
        for activity in self:
            activity.owner_id = activity.team_id.team_manager.user_id

    @api.multi
    def _compute_total_workload(self):
        for activity in self:
            activity.total_workload = activity.recurring_workload * 3 \
                + (activity.extra_workload * activity.probability) / 100

    @api.multi
    def _compute_support_ticket_count(self):
        support_ticket_obj = self.env['tms.support.ticket']
        for activity in self:
            ticket_count = support_ticket_obj.search_count([
                ('tms_activity_id', '=', activity.id),
                ('state', '!=', 'closed')
            ])
            activity.support_ticket_count = ticket_count

    @api.multi
    def _compute_forge_ticket_count(self):
        forge_ticket_obj = self.env['tms.forge.ticket']
        for activity in self:
            ticket_count = forge_ticket_obj.search_count([
                ('tms_activity_id', '=', activity.id)])
            activity.forge_ticket_count = ticket_count

    @api.multi
    def _compute_working_hours(self):
        working_hour_obj = self.env['tms.working.hour']
        for activity in self:
            duration = 0
            activity_wk_hours = working_hour_obj.search([
                ('tms_activity_id', '=', activity.id)])
            for work in activity_wk_hours:
                duration += work.duration_hour
            activity.working_duration_count = round(duration, 2)

    @api.multi
    def _compute_next_expected_deadline(self):
        for activity in self:
            deadline_list = []
            for task in activity.tasks_ids:
                if task.active:
                    deadline_date = task.deadline and datetime.strptime(
                        task.deadline, '%Y-%m-%d').date() or False
                    if deadline_date and deadline_date >= date.today():
                        deadline_list.append(deadline_date)
            activity.next_expected_deadline = deadline_list and \
                min(deadline_list) or ''

    @api.multi
    def _compute_activity_task_count(self):
        activity_task_obj = self.env['activity.task']
        for activity in self:
            task_count = activity_task_obj.search_count([
                ('activity_id', '=', activity.id),
                '|', ('active', '=', True),
                ('active', '=', False)
            ])
            activity.activity_task_count = task_count

    @api.multi
    def get_activity_task(self):
        self.ensure_one()

        domain = [('activity_id', '=', self.id),
                  '|', ('active', '=', True),
                  ('active', '=', False)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Activity Tasks',
            'view_mode': 'tree,form',
            'res_model': 'activity.task',
            'domain': domain
        }

    @api.multi
    def compute_working_hours_in_time(self, date_from, date_to):
        val = 0.0
        for activity in self:
            sql = '''
                SELECT sum(duration_hour)/8
                FROM tms_working_hour
                WHERE tms_activity_id = %s
                AND (date BETWEEN %s AND %s)
            '''
            self._cr.execute(sql, (activity.id, date_from, date_to))
            val += float(self._cr.fetchone()[0] or 0.0)
        return val

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
                                    dtstart=start_date,
                                    until=end_date))
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

    @api.multi
    def compute_day_sold_in_time(self, date_from, date_to, get_type):
        '''Compute day sold for dev in time'''
        date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
        days = 0.0
        for activity in self:
            day_total = 0
            act_start_date = datetime.strptime(activity.start_date,
                                               "%Y-%m-%d").date()
            # get available day of activity
            act_end_date = datetime.strptime(
                activity.planned_date, "%Y-%m-%d").date() \
                if activity.planned_date else datetime.today().date()
            day_total = self.count_day_work(act_start_date, act_end_date)

            # get available day of activity in time

            date_from = date_from if act_start_date <= date_from \
                else act_start_date
            date_to = date_to if date_to <= act_end_date \
                else act_end_date
            day_in_time = self.count_day_work(date_from, date_to)

            if get_type == 'dev':
                days += float(day_in_time) / float(day_total) \
                    * activity.day_sold_dev if day_total > 0 else 0
            elif get_type == 'global':
                days += float(day_in_time) / float(day_total) \
                    * activity.day_sold if day_total > 0 else 0
        return days

    @api.model
    def check_support_contracts(self, activity_id):
        sql = """
            SELECT contract_id FROM ref_activity_contracts WHERE
            activity_id = %s
        """ % (activity_id)
        self._cr.execute(sql)
        datas = self.env.cr.fetchall()
        contract_ids = [data[0] for data in datas]
        contracts = self.env[
            'project.support.contracts'].search(
                [('id', 'in', contract_ids), '|',
                 ('state', '=', 'in_progress'),
                 ('state', '=', 'planned')])
        if contracts:
            raise Warning(
                'Some Support Contracts of this activity '
                'are still "Planned" or "In Process". '
                'Please handle its support contract firstly '
                'if you expect to perform this action.'
            )
