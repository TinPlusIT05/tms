# -*- encoding: utf-8 -*-

from datetime import datetime, date, timedelta
from itertools import groupby
import logging
import math
from operator import itemgetter

from openerp import api, models, fields
from openerp import tools
from openerp.addons.tms_modules.model.support \
    import tms_support_ticket  # @UnresolvedImport
from openerp.addons.tms_slack.lib.slack \
    import SlackClient  # @UnresolvedImport
from openerp.exceptions import Warning
from openerp.tools.safe_eval import safe_eval
from dateutil import rrule
from openerp import SUPERUSER_ID
import base64
import zipfile
import tempfile
import os

_logger = logging.getLogger(__name__)


class TmsForgeTicket(models.Model):

    _inherit = "tms.ticket"
    _name = "tms.forge.ticket"
    _description = "Forge Ticket"
    _order = 'sequence desc, state_order, completion_sprint_date desc, ' + \
             'sprint desc'

    FORGE_STATES = [
        ('assigned', 'Assigned'),
        ('wip', 'WIP'),
        ('code_completed', 'Code completed'),
        ('ready_to_deploy', 'Ready To Deploy'),
        ('in_qa', 'QA'),
        ('closed', 'Closed')
    ]
    PRIORITY = [
        ('very_high', 'Very High'),
        ('high', 'High'),
        ('normal', 'Normal'),
        ('low', 'Low')
    ]

    PRIORITY_SEQUENCE_DICT = {
        'very_high': 20,
        'high': 15,
        'normal': 10,
        'low': 5
    }
    STATUS = [
        ('assigned', 'Assigned'),
        ('wip', 'WIP'),
        ('code_completed', 'Code completed'),
        ('ready_to_deploy', 'Ready To Deploy'),
        ('in_qa', 'QA'),
        ('closed', 'Closed')
    ]
    DELIVERY_STATUS = [
        ('in_development', 'In Development'),
        ('in_integration', 'In Integration'),
        ('ready_for_staging', 'Ready for Staging'),
        ('in_staging', 'In Staging'),
        ('in_production', 'In Production'),
        ('no_development', 'No Development')
    ]
    PROJECT_STATE = [
        ('potential', 'Potential'),
        ('active', 'Active'),
        ('done', 'Done'),
        ('asleep', 'Asleep')
    ]

    qc_estimate = fields.Float(
        string='QC Estimate (h)',
    )

    state_order = fields.Integer(
        string='State Order', store=True, readonly=True,
        compute='_get_state_order')

    qc_testcase_ids = fields.One2many(
        comodel_name='qc.testcase',
        inverse_name='forge_ticket_id',
        string='Test Case Table',
    )

    @api.multi
    @api.depends('state')
    def _get_state_order(self):
        """
        Calculate the value of field `state_order`
        This field is used to "order by" on forge tickets.
        """
        state_list = [
            ('assigned', 1),
            ('wip', 2),
            ('code_completed', 3),
            ('ready_to_deploy', 4),
            ('in_qa', 5),
            ('closed', 6),
        ]
        for t in self:
            if not t.state:
                # There is no value for field `State`
                # the ticket will be placed at the end
                t.state_order = 10
            else:
                t.state_order = filter(
                    lambda x: x[0] == t.state, state_list)[0][1]

    @api.depends('tms_working_hour_ids',
                 'tms_working_hour_ids.duration_hour',
                 'tms_working_hour_ids.tms_forge_ticket_id')
    def _get_total_time_spent_by_department(self):
        """
        Get total time spent which categorized by department (profile) of user
        """
        res_groups_env = self.env['res.groups']
        dev_profile_objs = res_groups_env.search(
            [('name', 'in', ('Technical Consultant Profile',
                             'Technical Project Manager Profile'))])

        fc_profile_objs = res_groups_env.search(
            [('name', 'in', ('FC and Admin Profile', 'FC+CRM Profile',
                             'Functional Consultant Profile'))])
        for ticket in self:
            vals = {
                'time_spent_dev': 0,
                'time_spent_fc': 0,
                'time_spent': 0,
            }
            for working_hours in ticket.tms_working_hour_ids:
                profile = working_hours.user_id and \
                    working_hours.user_id.group_profile_id or False
                # total hours for DEV or FC
                if profile and profile in dev_profile_objs:
                    vals['time_spent_dev'] += working_hours.duration_hour
                elif profile and profile in fc_profile_objs:
                    vals['time_spent_fc'] += working_hours.duration_hour

                vals['time_spent'] += working_hours.duration_hour
            ticket.time_spent = vals['time_spent']
            ticket.time_spent_dev = vals['time_spent_dev']
            ticket.time_spent_fc = vals['time_spent_fc']

    @api.depends('child_forge_ticket_ids',
                 'child_forge_ticket_ids.time_spent',
                 'time_spent')
    def _compute_total_time_spent(self):
        for ticket in self:
            time_spent_child_ticket = sum(
                ticket.child_forge_ticket_ids.mapped('time_spent'))
            ticket.total_time_spent =\
                ticket.time_spent + time_spent_child_ticket

    @api.depends('tms_working_hour_ids', 'tms_working_hour_ids.duration_hour')
    def _get_total_time_spent(self):
        return self.env['tms.ticket'].get_total_time_spent(self)

    @api.model
    def remove_milestone(self, rcs_ids, model_name):
        context = self._context and self._context.copy() or {}
        if context is None:
            context = {}
        target_ticket_pool = self.env[model_name]
        target_ticket_pool.with_context(context).\
            browse(rcs_ids).write({"milestone_id": False})

    @api.depends('tms_working_hour_ids',
                 'tms_working_hour_ids.is_fixing_time_ticket',
                 'tms_working_hour_ids.duration_hour',
                 'tms_working_hour_ids.tms_forge_ticket_id')
    def _get_fixing_time_spent(self):
        for ticket in self:
            duration_hours = [working_hours.duration_hour for working_hours in
                              ticket.tms_working_hour_ids if
                              working_hours.is_fixing_time_ticket]
            ticket.fixing_time_spent = sum(duration_hours) \
                if duration_hours else 0.00

    @api.depends('state', 'development_time',
                 'tms_working_hour_ids',
                 'tms_working_hour_ids.duration_hour',
                 'tms_working_hour_ids.tms_forge_ticket_id')
    def _get_remaining_time(self):
        """
            The life-cycle / remaining time is like that:
             - New to WIP: max(100% of Estimate - time spent, 50% of Estimate)
             - code completed: 20% of Estimate
             - ready_to_deploy -> in_qa: 10% of Estimate
             - closed:0
        """
        for ticket in self:
            remaining = 0
            if ticket.state in ('assigned', 'wip'):
                remaining = max(
                    ticket.development_time - ticket.time_spent,
                    ticket.development_time * 0.5)
            elif ticket.state in ('code_completed', 'ready_to_deploy'):
                remaining = ticket.development_time * 0.1
            elif ticket.state == 'in_qa':
                remaining = ticket.development_time * 0.1
            ticket.remaining_time = remaining

    @api.depends('tms_forge_ticket_comment_ids')
    def _get_last_modified_author(self):

        author_dicts = self.env['tms.ticket'].\
            get_last_modified_author(self._ids, 'tms.forge.ticket')
        for ticket in self:
            if ticket.tms_forge_ticket_comment_ids:
                ticket.last_modified_author_id = author_dicts[ticket.id]

    @api.multi
    def get_subscriber_email_list(self, fields_change=[]):
        """
        @return: email-to of the Notification Email
        """
        ctx = self._context
        if ctx.get('email_to', False):
            return ctx['email_to']
        result = self.env['tms.ticket'].get_subscriber_email_list(
            self.ids, 'tms.forge.ticket',
            'forge_ticket_subscriber_ids',
            fields_change=fields_change)
        if len(self.ids) == 1:
            return result[self.ids[0]]
        return result

    @api.depends('sprint')
    def _get_gantt_start(self):
        for ticket in self:
            if ticket.sprint:
                ticket.gantt_start = datetime.strptime(
                    ticket.sprint,
                    '%Y-%m-%d').strftime('%Y-%m-%d 00:00:00')
            else:
                date_start = datetime.now() + timedelta(days=30)
                ticket.gantt_start = date_start.strftime('%Y-%m-%d 00:00:00')

    @api.depends('sprint')
    def _get_gantt_end(self):
        for ticket in self:
            if ticket.sprint:
                ticket.gantt_end = datetime.strptime(
                    ticket.sprint, '%Y-%m-%d'
                ).strftime('%Y-%m-%d 00:00:00')
            else:
                date_end = datetime.now() + timedelta(days=33)
                ticket.gantt_end = date_end.strftime('%Y-%m-%d 00:00:00')

    @api.depends('tms_activity_id',
                 'tms_activity_id.is_billable')
    def _get_is_billable(self):
        for ticket in self:
            if ticket.tms_activity_id:
                ticket.is_billable = ticket.tms_activity_id.is_billable
            else:
                ticket.is_billable = False

    @api.depends('owner_id',
                 'owner_id.employee_id',
                 'owner_id.employee_id.department_id')
    def _get_department_id(self):
        for ticket in self:
            if ticket.owner_id and ticket.owner_id.employee_id:
                employee = ticket.owner_id.employee_id
                ticket.department_id = employee.department_id and \
                    employee.department_id.id or False

    @api.depends('developer_id',
                 'developer_id.employee_id',
                 'developer_id.employee_id.department_id')
    def _get_department_id_from_analysis(self):
        for ticket in self:
            if ticket.developer_id and ticket.developer_id.employee_id:
                employee = ticket.developer_id.employee_id
                ticket.analysis_department_id = employee.department_id and \
                    employee.department_id.id or False

    @api.depends('priority')
    def _compute_sequence(self):
        for ticket in self:
            ticket.sequence = self.PRIORITY_SEQUENCE_DICT[ticket.priority]

    @api.multi
    def name_get(self):
        if self._context.get('display_forge_ticket_id_with_summary', False):
            res = [(rec.name, 'F#' + str(rec.name) + ' - ' +
                    rec.summary) for rec in self]
        else:
            res = [(rec.name, 'F#' + str(rec.name)) for rec in self]
        return res

    @api.model
    def name_search(
            self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []

        if name:
            recs = self.search(
                ['|', ('name', operator, name),
                 ('summary', operator, name)] + args, limit=limit)
        else:
            recs = self.search(args, limit=limit)
        return recs.name_get()

    @api.depends('tms_support_ticket_id', 'tms_support_ticket_id.state')
    def _get_support_ticket_state(self):
        """
        Ticket 1662: add field support ticket state
        """
        for forge in self:
            if forge.tms_support_ticket_id:
                forge.support_ticket_state = forge.tms_support_ticket_id.state

    @api.multi
    def _set_remaining_time(self):
        cr = self._cr
        for forge in self:
            if not forge.remaining_time:
                continue
            sql = """
                    UPDATE tms_forge_ticket
                    SET remaining_time = %s
                    WHERE id = %s
                  """
            cr.execute(sql, (forge.remaining_time, forge.id))

    @api.depends('project_id',
                 'project_id.trobz_partner_id')
    def _get_trobz_partner_id(self):
        for ticket in self:
            ticket.trobz_partner_id = (
                ticket.project_id.trobz_partner_id and
                ticket.project_id.trobz_partner_id.id or False)

    @api.multi
    def _is_subscribed(self):
        """
        If current user is in ticket subscribers > True
        else: False
        Use this field to show the button subscriber/unsubscribe
        """
        for forge in self:
            is_subscribed = False
            user_ids = [x.name.id for x in
                        forge.forge_ticket_subscriber_ids]
            if self._uid in user_ids:
                is_subscribed = True
            forge.is_subscribed = is_subscribed

    @api.depends('formula', 'formula_parameter')
    def _get_evolution_workload_task_type(self):
        for forge in self:
            formula = forge.formula or False
            if not formula:
                forge.evolution_workload_task_type = 0
                continue
            try:
                localdict = forge.formula_parameter or False
                localdict = localdict.replace(" ", "")
                localdict = eval(localdict)
                result = safe_eval(formula, locals_dict=localdict,
                                   mode='eval', nocopy=True)
                forge.evolution_workload_task_type = result
            except Exception:
                forge.evolution_workload_task_type = -1

    @api.depends('development_time')
    def _get_evolution_workload_from_dev(self):
        for forge in self:
            workload_dev = forge.development_time or 0
            evolution_workload = 0.5 * \
                math.ceil(2.0 * (workload_dev * 1.2) / 8)
            forge.evolution_workload_from_dev = evolution_workload

    @api.depends('type_quotation',
                 'type_quotation.risk',
                 'evolution_workload_from_dev',
                 'evolution_workload_task_type')
    def _get_evolution_workload(self):
        for forge in self:
            workload_dev = forge.evolution_workload_from_dev
            risk = forge.type_quotation and \
                forge.type_quotation.risk or 0
            workload_task_type = (
                forge.evolution_workload_task_type / (1 + risk / 100.0))
            evolution_workload_min = min(workload_dev, workload_task_type)
            evolution_workload_max = max(workload_dev, workload_task_type)

            forge.evolution_workload_min = evolution_workload_min
            forge.evolution_workload_max = evolution_workload_max

    @api.depends('evolution_workload_final', 'evolution_workload_min',
                 'evolution_workload_max')
    def _get_evolution_workload_check(self):
        for forge in self:
            evolution_workload_final = forge.evolution_workload_final
            evolution_workload_min = forge.evolution_workload_min
            evolution_workload_max = forge.evolution_workload_max
            if evolution_workload_final < evolution_workload_min:
                forge.evolution_workload_check = "Low estimation"
            elif evolution_workload_final > evolution_workload_max:
                forge.evolution_workload_check = "High estimation"
            else:
                forge.evolution_workload_check = "Standard estimation"

    @api.depends('is_billable')
    def _compute_billable(self):
        for forge in self:
            billable = forge.is_billable
            if billable:
                forge.is_billable_type = 'Billable'
            else:
                forge.is_billable_type = 'Not Billable'

    @api.depends('tms_working_hour_ids',
                 'tms_working_hour_ids.partner_computed_id',
                 'tms_working_hour_ids.tms_forge_ticket_id')
    def _get_partner_computed(self):
        for forge in self:
            partner_computed_id = False
            if forge.tms_working_hour_ids:
                partner_computed_id = \
                    forge.tms_working_hour_ids[0].partner_computed_id and \
                    forge.tms_working_hour_ids[0].partner_computed_id.id or \
                    False
            forge.partner_computed_id = partner_computed_id

    @api.depends('completion_date')
    def _compute_completion_year(self):
        for forge in self:
            completion_date = forge.completion_date
            if completion_date:
                completion_year = datetime.strptime(
                    completion_date, '%Y-%m-%d %H:%M:%S').year
                forge.completion_year = completion_year

    @api.depends("tms_working_hour_ids",
                 "tms_working_hour_ids.tms_job_type_id",
                 "tms_working_hour_ids.duration_hour")
    def _compute_sum_qc_time(self):
        job_functional_test = self.env.ref(
            'tms_modules.tms_job_type_functional')
        for forge in self:

            functional_test_times = forge.tms_working_hour_ids.filtered(
                lambda x: x.tms_job_type_id == job_functional_test
            )

            # sum all duration hour of result
            forge.sum_qc_time = sum(
                functional_test_times.mapped("duration_hour"))

    # Columns fields
    name = fields.Integer(string='Ticket ID', readonly=True)
    tms_functional_block_id = fields.Many2one(
        comodel_name='tms.functional.block', string='Functional Block',
        help='Automatically synchronized with related Forge/Support ticket.',
        domain="['|', ('project_ids', 'ilike', "
               "project_id and [project_id] or []),"
               "('project_ids', '=', False)]")
    tms_project_tag_ids = fields.Many2many(
        string='Tags',
        comodel_name='tms.project.tag',
        relation='forge_ticket_project_tag_rel',
        column1='forge_ticket_id',
        column2='tag_id',
        domain="[('project_id', '=', project_id)]",
        help='Automatically synchronized with related Forge/Support ticket.'
    )
    gantt_start = fields.Datetime(
        compute='_get_gantt_start', string='Start point for the gantt chart')
    gantt_end = fields.Datetime(
        compute='_get_gantt_end', string='End point for the gantt chart')
    closed_by = fields.Many2one(
        'res.users', string='Closed By', readonly=True)
    owner_id = fields.Many2one(
        'res.users', 'Assignee',
        domain="[('is_trobz_member','=',True)]",
        ondelete='restrict')
    yaml_test_status = fields.Selection(
        [('na', 'NA'), ('todo', 'Todo'), ('done', 'Done')],
        'YAML Test Status', required=True, default='na',
    )
    milestone_id = fields.Many2one(
        'tms.milestone', 'Milestone',
        help="Automatically synchronized with related Forge/Support ticket.",
        domain="[('project_id', '=', project_id)]")
    developer_id = fields.Many2one(
        'res.users', 'Developer', domain="[('is_trobz_member','=',True)]",
        ondelete='restrict', readonly=True)

    sprint = fields.Date(string='Sprint')
    state = fields.Selection(FORGE_STATES, 'Status', default='assigned')
    tms_support_ticket_id = fields.Many2one(
        'tms.support.ticket', 'Support ticket', size=256,
        help='Support ticket associated to this ticket.'
    )
    support_ticket_state = fields.Char(
        compute='_get_support_ticket_state',
        string='Support Ticket State'
    )
    support_ticket_type = fields.Selection(
        selection=tms_support_ticket.TmsSupportTicket.list_ticket_type,
        related='tms_support_ticket_id.ticket_type',
        string='Support Ticket Type', store=True
    )
    tms_forge_ticket_comment_ids = fields.One2many(
        'tms.ticket.comment', 'tms_forge_ticket_id', string='Comments',
        domain=[("type", "!=", "test_log")]
    )
    tms_working_hour_ids = fields.One2many(
        'tms.working.hour', 'tms_forge_ticket_id',
        string='Working Hours',
        help='You can input working hours only after selecting an activity.'
    )
    development_time = fields.Float(
        'Dev Estimate (h)', size=256, default=0.01,
        help='Estimation of the time required for development of this ticket '
        '(in hours). This estimation should be specifically given for the '
        'assignee of this ticket.'
    )
    std_development_time = fields.Float(
        'Std Dev Estimate (h)', size=256, default=0.01,
        help='Estimation of the time required to develop this ticket '
        '(in hours). This estimation should be standard and based on the '
        'profile of a "confirmed" developer.'
    )
    completion_time_spent = fields.Float(
        string='Completion Time Spent',
        help='Time spent at first completion', readonly=True
    )
    completion_date = fields.Datetime(
        'Completion date', readonly=True)
    fixing_time_spent = fields.Float(
        compute='_get_fixing_time_spent', string='Fixing Time Spent',
        help='Time spent on this ticket after it was completed the first '
        'time. In hours',
        store=True
    )
    time_spent = fields.Float(
        compute='_get_total_time_spent_by_department',
        string='Time Spent', help='In hours',
        store=True
    )
    time_spent_dev = fields.Float(
        compute='_get_total_time_spent_by_department',
        string='Time Spent Dev', help='In hours',
        store=True
    )
    time_spent_fc = fields.Float(
        compute='_get_total_time_spent_by_department',
        string='Time Spent FC', help='In hours',
        store=True
    )
    total_time_spent = fields.Float(
        compute='_compute_total_time_spent',
        string='Total Time Spent',
        help='Total Time Spent of current ticket and its child forge tickets',
        store=True
    )
    remaining_time = fields.Float(
        compute='_get_remaining_time', inverse='_set_remaining_time',
        string='Est. Remaining Time', help='Estimation of the remaining time',
        store=True
    )
    additional_budget_time = fields.Float(
        string='Additional Budget Time', help='Number of hours estimated '
        'to complete this ticket on top of the Estimate. This field is used '
        'by the "Daily Notification Email > Forge tickets assigned or WIP '
        'with long time spent" which will ignore tickets with time spent '
        'below the sum of "Estimate" and "Additional Budget Time". When '
        'setting this field, the productivity won\'t be increased, but it is '
        'encouraging the setting of a new target without virtually '
        'increasing the productivity and will allow ignoring this ticket '
        'in the Daily Notification email.',
        store=True
    )
    partner_computed_id = fields.Many2one(
        'res.partner', compute='_get_partner_computed',
        string="Partner Computed", store=True
    )
    quotation = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], string='Quotation', required=True,
        help="Quotation ticket don't need to be implemented, "
        "but only estimated", default='no',
    )
    priority = fields.Selection(
        PRIORITY, string='Priority', required=True, default='normal',
        help='Automatically synchronized with related Forge/Support ticket.')
    is_billable = fields.Boolean(
        compute='_get_is_billable', string='Billable', store=True,
        help='A ticket is billable if it is associated' +
        ' to a billable activity.',
    )
    help_time = fields.Text('Help Time')
    sequence = fields.Integer(
        compute='_compute_sequence', string='Sequence',
        store=True
    )
    reopening_times = fields.Integer('Reopening Times', readonly=True)
    delivery_id = fields.Many2many(
        'tms.delivery', 'tms_delivery_forge_ticket_rel',
        'ticket_id', 'delivery_id', string='List Delivery', readonly=True
    )
    completion_sprint_date = fields.Date(string='Completion Sprint')
    delivery_status = fields.Selection(
        DELIVERY_STATUS, 'Delivery Status', readonly=True,
        default='in_development'
    )
    last_modified_author_id = fields.Many2one(
        'res.users', compute='_get_last_modified_author',
        string='Last Updater', store=True
    )
    department_id = fields.Many2one(
        'hr.department', compute='_get_department_id',
        string='Department', store=True
    )
    analysis_department_id = fields.Many2one(
        'hr.department', compute='_get_department_id_from_analysis',
        string='Department',
    )

    project_state = fields.Selection(
        PROJECT_STATE, string="Project State", readonly=True,
        related='project_id.state', store=True,
    )
    trobz_partner_id = fields.Many2one('res.partner',
                                       compute='_get_trobz_partner_id',
                                       string='Partner', store=True
                                       )
    forge_reopening_ids = fields.One2many(
        'forge.ticket.reopening', 'name', string='Reopening Times'
    )
    forge_assign_ids = fields.One2many(
        'forge.ticket.assign', 'forge_id', string='Assign Times'
    )
    milestone_number = fields.Char(
        related="milestone_id.number", string="Milestone", store=True
    )
    parent_forge_ticket_id = fields.Many2one(
        'tms.forge.ticket', 'Parent Forge Ticket')
    child_forge_ticket_ids = fields.One2many(
        'tms.forge.ticket', 'parent_forge_ticket_id',
        string='Children Forge Ticket')
    forge_ticket_subscriber_ids = fields.One2many(
        comodel_name='tms.subscriber',
        inverse_name='forge_id',
        string="Ticket Subscriber"
    )
    is_subscribed = fields.Boolean(
        compute='_is_subscribed', string='Is Subscribed')
    type_quotation = fields.Many2one('tms.ticket.task.type', 'Type')
    formula = fields.Char(related='type_quotation.formula',
                          string="Formula", readonly=True
                          )
    formula_description = fields.Text(
        related='type_quotation.formula_description',
        string="Formula Description", readonly=True
    )
    formula_parameter = fields.Char('Formula Parameter')

    evolution_workload_task_type = fields.Float(
        compute='_get_evolution_workload_task_type',
        string="Evolution Workload Task Type")

    evolution_workload_from_dev = fields.Float(
        compute='_get_evolution_workload_from_dev',
        string='Evolution Workload From Dev')

    evolution_workload_min = fields.Float(
        compute='_get_evolution_workload',
        string='Evolution Workload Min'
    )
    evolution_workload_max = fields.Float(
        compute='_get_evolution_workload',
        string='Evolution Workload Max'
    )
    evolution_workload_final = fields.Float('Evolution Workload Final')
    evolution_workload_check = fields.Text(
        compute='_get_evolution_workload_check',
        string='Evolution Workload Check'
    )

    evolution_workload_comment = fields.Text('Evolution Workload Comment')
    last_completer_id = fields.Many2one(
        'res.users', 'Last completer',
        domain="[('is_trobz_member','=',True)]",
        ondelete='restrict', readonly=True,
        help="Used to set the Responsible in case of ticket re-opening.")
    proj_owner_id = fields.Many2one(
        related='project_id.owner_id',
        string="Project's Owner", store=True
    )
    analytic_secondaxis_id = fields.Many2one(
        related='tms_activity_id.analytic_secondaxis_id',
        string='Second Axis', readonly=True, store=True
    )

    is_billable_type = fields.Char(
        compute='_compute_billable', string='Billable', store=True
    )
    completion_year = fields.Char(
        compute='_compute_completion_year', string="Completion Year",
        size=4, store=True
    )

    wip_start = fields.Datetime(string="WIP Start", readonly=True)

    tracked_fields = ['summary', 'description', 'reporter_id', 'project_id',
                      'milestone_id', 'sprint', 'tms_activity_id',
                      'state', 'priority', 'development_time', 'owner_id',
                      'resolution', 'tms_project_tag_ids',
                      'tms_functional_block_id', 'qc_estimate']

    team_id = fields.Many2one(string='Team', related='project_id.team_id',
                              store=True)
    team_manager_id = fields.Many2one(
        string="Team Manager", related='project_id.team_id.team_manager',
        store=True)
    job_id = fields.Many2one(string='Job',
                             related='owner_id.employee_id.job_id',
                             store=True)
    job_type_id = fields.Many2one(
        string='User Job Type',
        related='owner_id.employee_id.job_id.job_type_id',
        store=True)
    last_assigned_date = fields.Datetime(
        string="Last Assigned Date", readonly=True)
    urgent_changed_date = fields.Datetime(string="Urgent Changed Date",
                                          readonly=True)
    deadline = fields.Date(
        related='tms_support_ticket_id.deadline',
        string='Deadline', readonly=True)
    forge_check_manage_dealine_on_sp_tickets = fields.Boolean(
        string='Manage Deadline on Support Tickets',
        related='project_id.manage_dealine_on_sp_tickets', readonly=True)
    num_support_attachment = fields.Integer(
        compute='_get_num_support_attachment')
    test_log_ids = fields.One2many(
        string='Test Logs',
        comodel_name='tms.ticket.comment',
        inverse_name='tms_forge_ticket_id',
        domain=[("type", "=", "test_log")]
    )
    sum_qc_time = fields.Float(
        string="Sum QC Time",
        readonly=True,
        compute="_compute_sum_qc_time",
        store=True,
    )
    card_ids = fields.One2many(
        'tms.forge.ticket.card',
        'forge_ticket_id',
        'Forge Ticket Cards'
    )
    tms_workload_ids = fields.One2many(
        'tms.forge.ticket.workload',
        'forge_ticket_id',
        'Workload Estimation'
    )
    sum_wl_est = fields.Float(
        'Total WL Estimate', compute='_compute_sum_wl_est',
        store=True)

    @api.depends('tms_workload_ids', 'tms_workload_ids.std_est')
    def _compute_sum_wl_est(self):
        for ticket in self:
            sum_wl_est = 0
            if ticket.tms_workload_ids:
                sum_wl_est = sum(ticket.tms_workload_ids.mapped('std_est'))
            ticket.sum_wl_est = sum_wl_est

    def _get_num_support_attachment(self):
        for forge in self:
            ir_attachment_obj = forge.env['ir.attachment']
            active_model = 'tms.support.ticket'
            support_ticket_id = forge.tms_support_ticket_id.id
            if support_ticket_id:
                forge.num_support_attachment = ir_attachment_obj.search_count(
                    [('res_model', '=', active_model),
                     ('res_id', '=', support_ticket_id)])
            else:
                forge.num_support_attachment = 0

    @api.multi
    def get_state_value_from_key(self):
        for state in self.FORGE_STATES:
            if self[0].state == state[0]:
                return state[1]

    @api.multi
    def get_priority_value_from_key(self):
        for priority in self.PRIORITY:
            if self[0].priority == priority[0]:
                return priority[1]

    @api.model
    def _check_sprint(self, current_sprint):
        """
        The sprint of edited ticket must be equal or
            bigger than the current sprint.
        """
        current_sprint = current_sprint.strftime('%Y-%m-%d')
        ticket_sprint_env = self.env['daily.mail.notification']
        date_start = ticket_sprint_env.get_current_sprint().strftime('%Y-%m-%d')
        if self.sprint and \
                (self.sprint == current_sprint or
                 self.sprint >= date_start):
            return True
        return False

    @api.model
    def _set_vals_with_completion_sprint(self, vals):
        # The ticket is counted as completed ONLY the first time it is
        # completed.
        if not self.completion_sprint_date:
            sprint_date = self.env[
                'daily.mail.notification'].get_sprint_by_date(date.today())
            total_spend = self.time_spent
            vals.update({'completion_sprint_date': sprint_date,
                         'completion_date': str(datetime.now()),
                         'developer_id': self._uid,
                         'completion_time_spent': total_spend})

        return vals

    @api.model
    def get_default_tester_id(self):
        """
        Find the first user that has tester_profile_name profile
             to be the default tester.
        """
        CONFIG_KEY_TESTER_PROFILE_NAME = 'tester_profile_name'

        tester_profile_name = self.env['ir.config_parameter'].get_param(
            CONFIG_KEY_TESTER_PROFILE_NAME)

        if not tester_profile_name:
            raise Warning(
                'Error!',
                '''The configuration parameter with the key %s does not return
                any profile name. The key might not exist or
                 might be misspelled''' % CONFIG_KEY_TESTER_PROFILE_NAME)

        profile_objs = self.env['res.groups'].search(
            [('name', '=', tester_profile_name)])
        default_owner_objs = self.env['res.users'].search(
            [('group_profile_id', 'in', profile_objs.ids)],
            order='id', limit=1)
        if not default_owner_objs:
            logging.warning(
                '''You cannot use this button because
                no default tester could be found.
                A default user has the profile %s as defined in
                the configuration parameter with the key %s.''' %
                (tester_profile_name, CONFIG_KEY_TESTER_PROFILE_NAME))
            return self._uid
        return default_owner_objs.id

    @api.model
    def create(self, vals):
        """
         - if related to support ticket:
            - Update its tag by tag of related support ticket.
            - Type of support ticket is evolution and quotation approved is
            not set:
               - Update "[Workload to Estimate]" to summary
               - Quotation = Yes
               - Milestone = False
            - Otherwise:
               - Update milestone of related support ticket for its

         - if not related to support ticket:
           - Update its support ticket by
           support ticket of parent forge ticket.

         - Update its customer based on project's customer.
         - Update Subscriber.

         - Update ticket's name = its id.
        """
        ctx = self._context and self._context.copy() or {}

        tms_project_env = self.env['tms.project']

        support_id = vals.get('tms_support_ticket_id', False)
        parent_forge_ticket_id = vals.get('parent_forge_ticket_id', False)
        project_id = vals.get('project_id', False)
        owner_id = vals.get('owner_id', False)
        ticket_comment_ids = vals.get("tms_forge_ticket_comment_ids", [])

        # Forge ticket is related to support ticket
        if support_id:
            vals = self.get_vals_of_support_ticket(support_id, vals)

        # Update customer based on project's customer
        project = tms_project_env.browse(project_id)
        vals['customer_id'] = project.partner_id and \
            project.partner_id.id or False

        ticket_creation_vals = [[0, False, {
            'comment': 'Creation of the ticket',
            'type': 'changelog',
            'name': str(datetime.now())}]]
        if ticket_comment_ids:
            vals["tms_forge_ticket_comment_ids"] = ticket_creation_vals + \
                ticket_comment_ids
        else:
            vals["tms_forge_ticket_comment_ids"] = ticket_creation_vals

        # Update subscriber for ticket
        ctx.update({'subscriber_from_forge_ticket': True})
        vals = self.with_context(ctx).get_vals_ticket_subcribers(
            project, owner_id, vals, [])

        if owner_id:
            # update last_assigned_date
            vals.update({'last_assigned_date': datetime.now()})

        forge_ticket = super(TmsForgeTicket, self).create(vals)
        subcribers = forge_ticket.project_id.forge_subscriber_ids
        mail_list = []
        for subcriber in subcribers:
            email_to = subcriber.name and subcriber.name.email
            mail_list.append(email_to)
        if forge_ticket.owner_id:
            email_to = forge_ticket.owner_id.email
            mail_list.append(email_to)
        # Update ticket's name
        self.update_ticket_name(forge_ticket, 'tms_forge_ticket')

        if len(mail_list) > 0:
            # add email-to into context to avoid run this function 2 times
            # get_subscriber_email_list, only read the 'email_to'
            # in context if it's run already in create/write forge ticket.
            ctx.update({'email_to': ",".join(mail_list)})
            email_template = self.env.ref(
                'tms_modules.tms_forge_notification_'
                'email_html_div_template')
            # Send mail to subscribers to notify new changes
            email_template.with_context(ctx).\
                _send_mail_asynchronous(forge_ticket.id, asynchronous=False)
            del ctx['email_to']

        if not support_id and parent_forge_ticket_id:
            # Get support ticket of parent forge ticket
            parent = self.browse(parent_forge_ticket_id)
            forge_ticket.tms_support_ticket_id = parent.tms_support_ticket_id \
                and parent.tms_support_ticket_id.id or False

        forge_ticket.check_sent_comment('tms_forge_ticket_comment_ids')
        return forge_ticket

    @api.model
    def get_vals_of_support_ticket(self, support_id, vals):
        support_env = self.env['tms.support.ticket']
        support = support_env.browse(support_id)
        # support ticket type is evolution and quotation_approved is not set
        if support.ticket_type == 'evolution' and \
                not support.quotation_approved:
            vals['summary'] = u'{0} {1}'.format('[Workload to Estimate]',
                                                vals['summary'])
            vals['quotation'] = 'yes'
            vals['milestone_id'] = False
        else:
            # get milestone of related support ticket
            vals['milestone_id'] = support.milestone_id and \
                support.milestone_id.id or False

        # Get tag of related support ticket
        vals['tms_project_tag_ids'] = [(6, 0, support.tms_project_tag_ids.ids)]
        return vals

    @api.model
    def check_status_assigned(self, new_vals, priority):
        sprint_env = self.env['daily.mail.notification']
        # Reset Delivery Status to In Development
        new_vals.update({'delivery_status': 'in_development',
                         'resolution': False})

        # ticket's sprint should be current sprint or later
        cur_sprint = sprint_env.get_current_sprint()
        is_valid_sprint = self._check_sprint(cur_sprint)
        if not is_valid_sprint:
            priority = priority or self.priority
            if priority not in ['very_high', 'high']:
                # when priority is not high or very high, maybe next sprint
                next_sprint = sprint_env.get_next_sprint(cur_sprint)
                new_vals.update({'sprint': next_sprint.strftime('%Y-%m-%d')})
            else:
                # if very high or high, current sprint, please
                new_vals.update({'sprint': cur_sprint.strftime('%Y-%m-%d')})

        # Calculate the number of reopened times
        # TODO: Can we use context `auto_creation_forge_reopening` instead?
        if self.completion_sprint_date and\
            self.state in ('code_completed', 'ready_to_deploy', 'in_qa',
                           'closed'):
            new_vals.update({
                'reopening_times': self.reopening_times + 1})
        return new_vals

    @api.multi
    def write(self, vals):
        """
            - Update `customer` info based on project.
            - Ticket ‘assigned’:
                - Reset `delivery_status`, `resolution`.
                - Update value for `sprint`.
                - Update `reopening_times` in case of reopening ticket.
                - Update `last_assigned_date`
            - Ticket ‘wip’:
                - Check evolution support ticket.
                - Assign current user as `Assignee`.
                - Assign `wip_start`.
            - Ticket ‘code_completed’:
                - Forbid action if `time_spent` is not set.
                - Update value `completion_sprint_date`, `completion_date`,
                `developer_id`, `completion_time_spent`, `owner_id`,
                `last_completer_id`.
            - Ticket ‘in_qa’:
                - Update `owner_id`.
            - Ticket 'closed':
                - Forbid action if `resolution` is not set.
                - Update value `closing_datetime`, `closed_by`,
                `delivery_status`.

            - if related to support ticket, update values to
             support(`tms_forge_ticket_id`, `project_id`, `milestone_id`,
             `tms_project_tag_ids`, `tms_functional_block_id`,
             `tms_activity_id` ).
            - if not related to support ticket,
             update suport ticket of parent forge ticket to it.

            - Create new record of ‘forge.ticket.reopening’ in case of
             reopening.
            - Reset `development_time` if `resolution` is in
             [‘canceled’, ‘invalid’, ‘duplicate’].
            - Forbid action if resolution is ‘fixed’ and
             `time_spent` is not set.
            - Update subscriber for ticket.
            - Send email to subscriber  to notify new changes.
        """
        ctx = self._context and self._context.copy() or {}
        project_env = self.env['tms.project']
        ticket_reopening_env = self.env['forge.ticket.reopening']
        support_env = self.env['tms.support.ticket']

        owner_id = vals.get('owner_id', False)
        milestone_id = vals.get('milestone_id', False)
        project_tag_ids = vals.get('tms_project_tag_ids', [])
        # M2m fields
        if project_tag_ids and len(project_tag_ids[0]) == 3:
            project_tag_ids = project_tag_ids[0][2]
        reporter_id = vals.get('reporter_id', False)
        func_block_id = vals.get('tms_functional_block_id', False)
        activity_id = vals.get('tms_activity_id', False)
        comment_ids = vals.get('tms_forge_ticket_comment_ids', [])
        project_id = vals.get('project_id', False)
        new_state = vals.get('state', '')
        time_spent = vals.get('time_spent', False)
        total_time_spent = vals.get('total_time_spent', False)
        priority = vals.get('priority', False)
        parent_forge_ticket_id = vals.get('parent_forge_ticket_id', False)
        resoultion_val = vals.get('resolution', False)

        for old_ticket in self:
            new_vals = vals.copy()

            # FOR MASS EDITING
            if new_state in ('assigned', 'wip') and \
                old_ticket.state in ('code_completed', 'ready_to_deploy',
                                     'in_qa', 'closed') and \
                    not ctx.get('reopening_type', False):
                raise Warning(
                    'Forbidden action!',
                    'You are not allowed to set status of this ticket to' +
                    ' assigned or wip. Please use the button Re-open instead.')

            resolution = resoultion_val or old_ticket.resolution
            time_spent = time_spent or old_ticket.time_spent
            total_time_spent = total_time_spent or old_ticket.total_time_spent

            # Update customer info if the project is changed
            if project_id:
                project = project_env.browse(project_id)
                new_vals.update({'customer_id': project.partner_id and
                                 project.partner_id.id or False})
            else:
                project = old_ticket.project_id

            if new_state != '':
                # State: Assigned
                if new_state == 'assigned':
                    new_vals = old_ticket.check_status_assigned(
                        new_vals, priority)

                # State: WIP
                elif new_state == 'wip':
                    self.check_support_ticket_when_wip()
                    new_vals.update(
                        {'owner_id': self._uid, 'wip_start': datetime.now()})

                # State: Code Completed
                elif new_state == 'code_completed':
                    if not total_time_spent:
                        raise Warning(
                            'Forbidden action!',
                            'Please, update the time you spent on the ticket!')

                    # Update `completed information` for ticket.
                    new_vals = old_ticket._set_vals_with_completion_sprint(
                        new_vals)
                    if not owner_id:
                        new_vals.update(
                            {'owner_id':
                             project.technical_project_manager_id.id})
                    new_vals.update({'last_completer_id': self._uid})
                    # Click on state bar or button Code Complete
                    old_ticket.create_ticket_card()

                # State: QA
                elif new_state == 'in_qa':
                    if not owner_id:
                        tester_id = project.tester_id and \
                            project.tester_id.id or \
                            old_ticket.get_default_tester_id()
                        new_vals.update({'owner_id': tester_id})

                # State: Closed
                elif new_state == 'closed':
                    # Resolution must be set when a ticket is closed
                    if not resolution:
                        raise Warning(
                            'Forbidden action!',
                            'Please, update the field resolution in the tab' +
                            ' "Tracking Info" before closing the ticket!')

                    # Record closing datetime
                    new_vals['closing_datetime'] = str(datetime.now())

                    # Record closing user
                    new_vals['closed_by'] = self._uid

                    # Update Delivery Status
                    if old_ticket.delivery_status == 'in_integration':
                        new_vals['delivery_status'] = 'ready_for_staging'
                    if old_ticket.delivery_status == 'in_development':
                        new_vals['delivery_status'] = 'no_development'

            support_ticket_id = vals.get(
                "tms_support_ticket_id",
                old_ticket.tms_support_ticket_id and
                old_ticket.tms_support_ticket_id.id or False)

            # Update milestone_id, project_id, tms_activity_id
            # to related support ticket.
            if support_ticket_id:
                support_vals = {}
                support_obj = support_env.browse(support_ticket_id)
                # Update forge ticket for related support ticket
                # ony if current user is supporter of project
                # and forge ticket is not set.
                if not support_obj.tms_forge_ticket_id and \
                        old_ticket.check_supporter(
                            self._uid, support_obj.project_id):
                    support_vals.update({'tms_forge_ticket_id': old_ticket.id})
                if project_id and not ctx.get('update_project_from_support'):
                    ctx.update({'update_project_from_forge': 1})
                    support_vals.update({'project_id': project_id})

                if milestone_id and \
                        not ctx.get('update_milestone_from_support'):
                    ctx.update({'update_milestone_from_forge': 1})
                    support_vals.update({'milestone_id': milestone_id})

                if project_tag_ids and \
                        not ctx.get('update_project_tag_from_support'):
                    ctx.update({'update_project_tag_from_forge': 1})
                    support_vals.update({
                        'tms_project_tag_ids': [(6, 0, project_tag_ids)]})

                if func_block_id and \
                        not ctx.get('update_functional_block_from_support'):
                    ctx.update({'update_functional_block_from_forge': 1})
                    support_vals.update({
                        'tms_functional_block_id': func_block_id})

                if activity_id and \
                        not ctx.get('update_activity_from_support', False):
                    ctx.update({'update_activity_from_forge': 1})
                    support_vals.update({'tms_activity_id': activity_id})
                if support_vals and support_obj:
                    support_obj.with_context(ctx).write(support_vals)
            elif parent_forge_ticket_id:
                # Forge does not link to any support ticket
                # Update S# = S# of the parent forge ticket
                parent_obj = old_ticket.browse(parent_forge_ticket_id)
                parent_sup_ticket_id = parent_obj.tms_support_ticket_id and \
                    parent_obj.tms_support_ticket_id.id or False
                if parent_sup_ticket_id:
                    new_vals.update({
                        'tms_support_ticket_id': parent_sup_ticket_id})

            # Record Reopening ticket
            if 'reopening_times' in new_vals:
                ticket_reopening_env.with_context(ctx). \
                    create_forge_ticket_reopening(old_ticket)

            # if resolution is in (cancel, duplicate or invalid) automatically
            # change the field estimate to 0
            if resolution in ['canceled', 'invalid', 'duplicate']:
                new_vals.update({'development_time': 0})

            elif resolution == 'fixed' and not total_time_spent:
                raise Warning(
                    'Forbidden action!',
                    'Please update the time you spent on the ticket!')

            # Update subscriber for ticket
            old_subscriber_ids = [s.name.id for s in
                                  old_ticket.forge_ticket_subscriber_ids]
            ctx.update({'subscriber_from_forge_ticket': True})
            new_vals = old_ticket.with_context(ctx).get_vals_ticket_subcribers(
                project, owner_id or old_ticket.owner_id.id, new_vals,
                old_subscriber_ids)

            # TODO: Consider to refactor func `record_changes`
            has_tracked_changes = self.record_changes(
                self, [old_ticket.id], new_vals, old_ticket,
                self.tracked_fields, 'tms_forge_ticket_id')

            if owner_id:
                # update last_assigned_date
                new_vals.update({'last_assigned_date': datetime.now()})

            # update urgent date
            if priority == 'very_high' and old_ticket.priority != 'very_high':
                new_vals.update({'urgent_changed_date': datetime.now()})
            elif old_ticket.priority == 'very_high' and \
                    owner_id != old_ticket.owner_id.id:
                new_vals.update({'urgent_changed_date': datetime.now()})

            old_support = old_ticket.tms_support_ticket_id or None

            # Write changes
            super(TmsForgeTicket, old_ticket.with_context(ctx)).write(new_vals)

            # Record Changes
            has_new_comment = False
            has_invalid_comment = False
            for comment in comment_ids:
                # Indicate a new comment is added
                if comment[0] == 0:
                    has_new_comment = True
                    break
                elif comment[2] and comment[2]['is_invalid']:
                    has_invalid_comment = True
                    break

            email_to = old_ticket.get_subscriber_email_list(new_vals.keys())
            if email_to and (has_tracked_changes or has_new_comment or
                             has_invalid_comment):
                # add email-to into context to avoid run this function 2 times
                # get_subscriber_email_list, only read the 'email_to'
                # in context if it's run already in create/write forge ticket.

                ctx.update({'email_to': email_to})
                email_template = self.env.ref(
                    'tms_modules.tms_forge_notification_'
                    'email_html_div_template')
                # Send mail to subscribers to notify new changes
                email_template.with_context(ctx).\
                    _send_mail_asynchronous(old_ticket.id, asynchronous=False)
                del ctx['email_to']

            # ==== [Check if support ticket is changed] ====
            if 'tms_support_ticket_id' not in vals:
                continue
            support_id = vals.get('tms_support_ticket_id', False)
            new_support = support_env.search([('id', '=', support_id)])
            if old_support and old_support.tms_forge_ticket_id.id == \
                    old_ticket.id:
                # Remove forge from old ticket
                old_support.tms_forge_ticket_id = None
            if new_support:
                # Set forge for new support ticket
                forge_ticket = old_ticket.parent_forge_ticket_id or old_ticket
                if not new_support.tms_forge_ticket_id:
                    new_support.tms_forge_ticket_id = forge_ticket.id
                elif new_support.tms_forge_ticket_id.id == forge_ticket.id:
                    for forge in forge_ticket.child_forge_ticket_ids:
                        if not forge.tms_support_ticket_id:
                            forge.tms_support_ticket_id = new_support
                    continue
                elif new_support.tms_forge_ticket_id.id != forge_ticket.id:
                    raise Warning(
                        'This Support ticket already link'
                        ' to other Forge Ticket!')
        self.check_sent_comment('tms_forge_ticket_comment_ids')
        return True

    @api.multi
    def button_accept(self):
        """
            if the support ticket is marked as 'Evolution'
            and the quotation is not approved by customer
        """
        self.write({'state': 'wip', 'owner_id': self._uid,
                    'wip_start': datetime.now()})

    @api.model
    def check_support_ticket_when_wip(self):
        support_env = self.env['tms.support.ticket']
        support_objs = support_env.search([
            ('tms_forge_ticket_id', 'in', self._ids)])
        for support in support_objs:
            if support.ticket_type == 'evolution' and \
                    not support.quotation_approved and \
                    not support.is_offered and \
                    not support.project_id.trobz_partner_id:
                raise Warning(
                    'Forbidden action!',
                    'You cannot accept this Forge Ticket because it is '
                    'related to a support ticket with an Invoiceable Workload '
                    'but you are NOT in one of these situations:\n'
                    '- The Invoiceable Workload has been approved by the '
                    'customer.\n- The Support Ticket is Offered.\n- The '
                    'Support Ticket is related to a Dedicated Team Project.')
        return True

    @api.multi
    def button_code_completed(self):
        self.write({'state': 'code_completed'})

    @api.multi
    def button_ready_to_deploy(self):
        self.write({'state': 'ready_to_deploy'})

    @api.multi
    def button_in_qa(self):
        self.write({'state': 'in_qa'})

    @api.multi
    def button_poke(self):
        """
            Function for poking assignee of ticket
        """
        user_obj = self.env['res.users'].browse(self._uid)
        ticket_comment_env = self.env['tms.ticket.comment']
        is_production_instance = tools.config.get(
            'is_production_instance', False)

        for ticket in self:
            if not ticket.owner_id:
                raise Warning(
                    'Forbidden action!',
                    'You must define an assignee for each ticket!')
            poker = user_obj.slack_user_id
            if is_production_instance:
                ticket.slack_notification(poker)
            poke = 'POKE: %s poked %s' % (
                user_obj.name, ticket.owner_id.name)
            vals = {
                'type': 'poke',
                'name': str(datetime.now()),
                'tms_forge_ticket_id': ticket.id,
                'comment': poke
            }
            ticket_comment_env.create(vals)
        return True

    @api.multi
    def button_previous_sprint(self):
        for ticket in self:
            if ticket.sprint:
                previous_sprint = datetime.strptime(
                    ticket.sprint, '%Y-%m-%d') - timedelta(days=7)
                ticket.write({'sprint': previous_sprint})
            else:
                previous_sprint = datetime.today() \
                    + timedelta(days=(5 - datetime.today().weekday())) \
                    - timedelta(days=7)
                ticket.write({'sprint': previous_sprint})

    @api.multi
    def button_remove_sprint(self):
        for ticket in self:
            ticket.write({'sprint': False})

    @api.multi
    def button_next_sprint(self):
        for ticket in self:
            if ticket.sprint:
                next_sprint = datetime.strptime(ticket.sprint, '%Y-%m-%d') \
                    + timedelta(days=7)
                ticket.write({'sprint': next_sprint})
            else:
                next_sprint = datetime.today() \
                    + timedelta(days=(5 - datetime.today().weekday())) \
                    + timedelta(days=7)
                ticket.write({'sprint': next_sprint})

    @api.multi
    def button_previous_milestone(self):
        ctx = self._context and self._context.copy() or {}
        ctx["next_milestone"] = False
        return self.with_context(ctx).move_milestone()

    @api.multi
    def button_next_milestone(self):
        ctx = self._context and self._context.copy() or {}
        ctx["next_milestone"] = True
        return self.with_context(ctx).move_milestone()

    @api.multi
    def button_remove_milestone(self):
        self.write({"milestone_id": False})

    @api.multi
    def move_milestone(self, rcs_ids=None, module=None):
        ctx = self._context and self._context.copy() or {}
        milestone_env = self.env['tms.milestone']
        if rcs_ids is None and module is None:
            rcs = self
        else:
            rcs = self.env[module].browse(rcs_ids)
        for ticket in rcs:
            # Get current milestone and project of the ticket
            project_id = ticket.project_id and ticket.project_id.id or False
            milestones = milestone_env.search(
                [('project_id', '=', project_id),
                 ('state', '=', 'development')])
            milestone = ticket.milestone_id or False
            if not milestone and not milestones:
                raise Warning(
                    'Warning!', 'Please input a milestone!')

            # Get next or previous milestone based on the passed context
            if ctx.get("next_milestone", False):
                target_id = milestone.get_next_milestone(project_id) \
                    if milestone else milestones[0].id
            else:
                target_id = milestone.get_previous_milestone(project_id)\
                    if milestone else milestones[0].id
            # Update current milestone
            if target_id:
                vals = {'milestone_id': target_id}
                ticket.write(vals)
        return True

    @api.multi
    def button_higher_priority(self):
        for ticket in self:
            vals = {}
            if ticket.priority == 'low':
                vals = {'priority': 'normal'}
            elif ticket.priority == 'normal':
                vals = {'priority': 'high'}
            elif ticket.priority == 'high':
                vals = {'priority': 'very_high'}
            if vals:
                ticket.write(vals)
        return True

    @api.multi
    def button_lower_priority(self):
        for ticket in self:
            vals = {}
            if ticket.priority == 'very_high':
                vals = {'priority': 'high'}
            elif ticket.priority == 'high':
                vals = {'priority': 'normal'}
            elif ticket.priority == 'normal':
                vals = {'priority': 'low'}
            if vals:
                ticket.write(vals)
        return True

    @api.multi
    def button_create_support_ticket(self):
        context = self._context and self._context.copy() or {}
        support_env = self.env['tms.support.ticket']
        user = context.get('uid', self._uid)
        current_user = self.env['res.users'].browse(user)
        priority_mapping = {
            'very_high': 'urgent',
            'high': 'major',
            'normal': 'normal',
            'low': 'minor'
        }

        for ticket in self:
            vals = {}
            project = ticket.project_id
            if not project.default_supporter_id:
                raise Warning(
                    'Forbidden action!',
                    'Please set Support Project Manager for project %s.' %
                    project.name
                )
            vals['summary'] = ticket.summary or False
            vals['project_id'] = project.id
            vals['tms_functional_block_id'] = ticket.tms_functional_block_id \
                and ticket.tms_functional_block_id.id or False
            vals['milestone_id'] = ticket.milestone_id and \
                ticket.milestone_id.id or False
            vals['priority'] = priority_mapping[ticket.priority]
            vals['tms_activity_id'] = ticket.tms_activity_id and \
                ticket.tms_activity_id.id or False
            vals['state'] = 'new'
            vals['tms_forge_ticket_id'] = ticket.id
            vals['owner_id'] = project.default_supporter_id.id
            vals['reporter_id'] = current_user.id
            vals['customer_id'] = project.partner_id and \
                project.partner_id.id or False

            support = support_env.create(vals)
            ticket.write({'tms_support_ticket_id': support.id})

        return True

    @api.model
    def get_forge_indicators(self, domain_filter):

        ticket_objs = self.search(domain_filter)
        planned = remaining = spent = 0

        for ticket in ticket_objs:
            planned += ticket.development_time
            remaining += ticket.remaining_time
            spent += ticket.time_spent
        progress = 0
        if planned > 0:
            progress = float(100 * (planned - remaining)) / planned
        return {'planned': planned, 'spent': spent,
                'remaining': remaining, 'progress': progress}

    @api.multi
    def copy(self, default=None):
        if not isinstance(default, dict):
            default = {}
        sprint_env = self.env['daily.mail.notification']
        current_sprint = sprint_env.get_current_sprint()
        next_sprint = sprint_env.get_next_sprint(current_sprint)
        default.update({
            'tms_forge_ticket_comment_ids': [],
            'development_time': 0.01,
            'tms_working_hour_ids': False,
            'tms_activity_id': False,
            'resolution': False,
            'milestone_id': False,
            'forge_ticket_subscriber_ids': [],
            'reporter_id': self._uid,
            'sprint': next_sprint,
            'completion_time_spent': False,
            'completion_sprint_date': False,
            'completion_date': False,
            'developer_id': False,
            'last_completer_id': False,
            'reopening_times': False,
            'delivery_status': 'in_development',
            'delivery_id': [(5,)],
            'owner_id': False,
            'tms_support_ticket_id': False,
            'std_development_time': 0.01,
            'closing_datetime': False,
            'closed_by': False,
            'last_assigned_date': False,
        })
        return super(TmsForgeTicket, self).copy(default)

    @api.model
    def search(self, args, offset=0, limit=None,
               order=None, count=False):
        args = self.search_subscriber_on_ticket('forge_id', args)
        if 'tms_latest_modified' in self._context and not order:
            order = 'write_date desc'
        return super(TmsForgeTicket, self).search(
            args, offset=offset, limit=limit, order=order, count=count)

    @api.multi
    def get_last_changes(self):
        return super(TmsForgeTicket, self).get_last_changes(
            self.ids,
            'tms.forge.ticket', 'tms_forge_ticket_comment_ids')

    @api.multi
    def get_html_description(self):
        return super(TmsForgeTicket, self).get_html_description(
            self.ids, 'tms.forge.ticket')

    @api.multi
    def get_ticket_url(self):
        """
            Helper method used to generate anchor link to forge ticket(s)
        """
        # Get env references
        config_env = self.env["ir.config_parameter"]
        action_env = self.env['ir.actions.act_window']

        # Get system address
        config_value = config_env.get_param(
            "web.base.url", "https://tms.trobz.com")
        if not config_value:
            config_value = "https://tms.trobz.com"
        base_url = config_value + '/web?db=%s' % self._cr.dbname
        # Find the default action of menu Forge Tickets (Dev > Tickets > Forge
        # Tickets)
        act_window = action_env.for_xml_id(
            'tms_modules', 'action_view_tms_forge_ticket_open')

        urls = []
        for ticket_id in self._ids:
            urls.append(
                u"{0}#id={1}&view_type=form&".format(base_url, ticket_id) +
                u"model=tms.forge.ticket&action={0}".
                format(act_window.get("id"))
            )

        if urls and len(urls) == 1:
            urls = urls[0]

        return urls or False

    @api.model
    def check_urgent_tickets(self):
        """
            Check if there are any urgent tickets.
        """
        # Get list of urgent ticket (priority == very_high)
        tickets = self.search(
            [('state', '!=', 'closed'), ('priority', '=', 'very_high')],
            limit=1)
        if tickets and len(tickets) > 0:
            return True
        return False

    @api.model
    def get_urgent_tickets(self):
        """
            Get list of urgent tickets to send a reminder.
        """
        # Get list of urgent ticket (priority == very_high)
        forge_ticket_objs = self.search(
            [('state', '!=', 'closed'), ('priority', '=', 'very_high')],
            order='project_id')
        # TO DO: NEED TO CHECK groupby and itemgetter,
        # WRITE OUT THE OF RESULT
        grouped_lines = dict(
            (pro, [ticket for ticket in tickets])
            for pro, tickets in groupby(
                forge_ticket_objs, itemgetter('project_id')))

        # Build a list of urgent tickets to send mail
        result = ''
        for line in grouped_lines:
            result += '<div><b>' + line.name + '</b></div>'
            ticket_list = '<ul>'
            for ticket in grouped_lines[line]:
                time_stop = datetime.now()
                time_start = ticket.urgent_changed_date or \
                    ticket.get_last_date_change_to_urgent()
                time_start = datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S')
                time = time_stop - time_start
                hours = time.days * 24 + time.seconds / 3600

                ticket_link = ticket.get_ticket_url()
                ticket_list += u'<li><a href="{0}">{1}</a> ({2},'.format(
                    ticket_link, ticket.id, ticket.state) +\
                    u' {0}, opened for {1} hours): {2}</li>'.format(
                        ticket.owner_id.name or '', hours, ticket.summary
                )
            result += ticket_list + '</ul>'

        return result

    # ==============================================================================
    # SCHEDULER TO SEND TICKET MISSING WORKLOAD ESTIMATION EMAIL
    # ==============================================================================

    @api.model
    def scheduler_check_tickets_missing_workload_estimation(self):
        template = self.env.ref(
            'tms_modules.remire_ticket_email_missing_template'
        )
        forge_tickets = self.search([], limit=1)
        if forge_tickets:
            template._send_mail_asynchronous(forge_tickets[0].id)
        return True

    @api.multi
    def get_ticket_missing_workload_estimation(self):
        """
        find all tickets missing workload estimate
        """

        forge_env = self.env['tms.forge.ticket']
        forge_ticket_objs = forge_env.search(
            [('state', 'in', ('assigned', 'wip')),
             ('development_time', 'in', (None, '0', '0.00', '0.01')),
             ('project_id.check_missing_workload', '=', True)],
            order='project_id')

        grouped_lines = dict((
            pro, [ticket for ticket in tickets])
            for pro, tickets in groupby(
            forge_ticket_objs, itemgetter('project_id'))
        )

        message_content = ''
        if not grouped_lines:
            message_content += 'Well done guys! No tickets missing workload ' \
                               'estimation found.'
        else:
            message_content += '<h4>Please, add your estimation to those ' \
                               'tickets of your projects:</h4>'
            for line in grouped_lines:
                tpm_name = line.technical_project_manager_id and\
                    line.technical_project_manager_id.name.encode(
                        'utf-8') or ''
                project_content = '<b>{0} - {1}</b><br/>'.format(
                    line.name or '',
                    tpm_name)
                ticket_ids = []
                for ticket in grouped_lines[line]:
                    ticket_ids.append(ticket.id)
                list_ticket_content = self.browse(ticket_ids).\
                    get_tickets_missing_workload_contents()
                message_content += project_content + \
                    list_ticket_content + '<br/>'
        message_content += "<p><h4>Some guidelines if you are stuck</h4>"\
            "<ul><li>When nothing was done in the forge ticket, "\
            "and you are waiting for information from the "\
            "support ticket, it might be better to close the "\
            "forge ticket as invalid since anyway the "\
            "requirement is still not good. (remember to remove "\
            "the 2 relations from Forge to Support and from "\
            "Support to Forge)</li>"\
            "<li>In other cases, when it is not possible "\
            "to estimate, you can use the workload: 0.02</li>"\
            "</ul></p>"
        return message_content.decode('utf-8')

    @api.multi
    def get_tickets_missing_workload_contents(self):
        """
            Get list of urgent tickets to send a reminder
        """
        ticket_list = ''
        # Build a list of urgent tickets to send mail
        now = datetime.now()
        ir_config_env = self.env['ir.config_parameter']
        max_overdue_date = ir_config_env.get_param(
            'maximum_assigned_overdue_date', default=3)
        max_overdue_date = eval(max_overdue_date)
        for ticket in self:
            last_assigned_date = ticket.last_assigned_date
            if not last_assigned_date:
                logging.info('====Ticket %s missing data of last_assigned_date'
                             '===', ticket.id)
                color = 'black'
            else:
                last_assigned_date_obj = datetime.strptime(
                    ticket.last_assigned_date, "%Y-%m-%d %H:%M:%S")
                nb_of_assigned_date = self.get_working_days(
                    last_assigned_date_obj, now)
                color = nb_of_assigned_date >= max_overdue_date and\
                    'red' or 'black'
            ticket_link = ticket.get_ticket_url()
            ticket_list += '''<div style="color:{0}; margin: 0px; padding:0px">
            <a href="{1}">{2}</a> ({3}, {4}, {5}): {6}</div>\n'''.format(
                color,
                ticket_link,
                'F#' + str(ticket.id),
                ticket.project_id.name.encode('utf-8'),
                ticket.state,
                ticket.owner_id and ticket.owner_id.name.encode('utf-8') or '',
                ticket.summary.encode('utf-8'))
        return ticket_list

    @api.model
    def get_email_of_admin_tpm_profile_users(self):
        model_data_env = self.env['ir.model.data']
        dummy, profile_admin_id = model_data_env.get_object_reference(
            'tms_modules', 'group_profile_tms_admin')
        dummy, profile_tpm_id = model_data_env.get_object_reference(
            'tms_modules', 'group_profile_tms_technical_project_manager')
        res_users_env = self.env['res.users']
        user_objs = res_users_env.search(
            [('group_profile_id', 'in', (profile_admin_id, profile_tpm_id))])
        emails_arr = [user_obj.email for user_obj in user_objs]
        emails_str = ', '.join(emails_arr)
        return emails_str

    @api.model
    def function_remove_sequence_tms_forge_ticket(self):
        logging.info('====START Remove sequence for tms forge ticket ====')
        ir_sequence_env = self.env['ir.sequence']
        ir_sequence_type_env = self.env['ir.sequence.type']
        tms_forge_ticket_sequence_objs = ir_sequence_env.search(
            [('code', '=', 'tms.forge.ticket.code')])
        tms_forge_ticket_sequence_type_objs = ir_sequence_type_env.search(
            [('code', '=', 'tms.forge.ticket.code')])
        if tms_forge_ticket_sequence_objs:
            tms_forge_ticket_sequence_objs.unlink()
        if tms_forge_ticket_sequence_objs:
            tms_forge_ticket_sequence_type_objs.unlink()
        logging.info('====START Remove sequence for tms forge ticket ====')
        return True

    @api.multi
    def get_ticket_missing_workload_email_to_be_send(self):
        forge_env = self.env['tms.forge.ticket']
        res_users_env = self.env['res.users']
        res_groups_env = self.env['res.groups']
        ticket_ids = []
        list_email_to_send = []
        list_tpm_email = []
        owner_email_list = []

        forge_ticket_objs = forge_env.search([
            ('state', 'in', ('assigned', 'wip')),
            ('development_time', 'in', (None, '0', '0.00', '0.01'))
        ], order='project_id')

        grouped_lines = dict(
            (pro, [ticket for ticket in tickets]) for pro, tickets in groupby(
                forge_ticket_objs, itemgetter('project_id')
            )
        )

        admin_profile_objs = res_groups_env.search(
            [('name', '=', 'Admin Profile'),
             ('is_profile', '=', True)])

        res_user_objs = res_users_env.search(
            [('group_profile_id', '=', admin_profile_objs.ids[0])])

        admin_mail_list = [x.email for x in res_user_objs if x.email]

        if admin_mail_list:
            list_email_to_send.extend(admin_mail_list)
        for line in grouped_lines:
            technical_project_manager_email = \
                line.technical_project_manager_id and \
                line.technical_project_manager_id.email or ''
            if technical_project_manager_email:
                list_tpm_email.append(technical_project_manager_email)

            for ticket in grouped_lines[line]:
                ticket_ids.append(ticket.id)
            ticket_objs = forge_env.browse(ticket_ids)

            owner_objs = [x.owner_id for x in ticket_objs
                          if x.owner_id]
            for user_obj in owner_objs:
                if user_obj.email:
                    owner_email_list.append(user_obj.email)
        if owner_email_list:
            list_email_to_send.extend(owner_email_list)
        if list_tpm_email:
            list_email_to_send.extend(list_tpm_email)

        list_email_to_send = list(set(list_email_to_send))

        if list_email_to_send:
            email_to_send = ",".join(list_email_to_send)
        else:
            email_to_send = "jcdrubay@trobz.com"
        return email_to_send

    @api.multi
    def button_subscribe(self):
        """
        Button Subscribe Me on forge ticket
        Add current user into the ticket subscribers
        """
        ticket_env = self.env['tms.ticket']
        return ticket_env.button_subscribe(
            self, 'forge_ticket_subscriber_ids')

    @api.multi
    def button_unsubscribe(self):
        """
        Button Unsubscribe Me on forge ticket
        Remove current user from the ticket subscribers
        """
        real_update_ids = []
        linked_exist = []
        for forge_ticket in self:
            subscribers = forge_ticket.forge_ticket_subscriber_ids
            linked_exist = [s for s in subscribers if s.name.id == self._uid]
            # only remove the reference if user is already linked
            if linked_exist:
                real_update_ids.append(forge_ticket.id)
        if real_update_ids:
            real_update_objs = self.browse(real_update_ids)
            real_update_objs.sudo().write({
                "forge_ticket_subscriber_ids": [(2, linked_exist[0].id)]
            })

    @api.multi
    def slack_notification(self, poker):
        ir_config_env = self.env['ir.config_parameter']
        slack_url = ir_config_env.get_param(
            'webhook_slack_access', default=False)
        if not slack_url:
            logging.warn(
                'Slack is not correctly configured on TMS, \
                    please set "webhook_slack_access" config parameter')
        slack_token = tools.config.get('slack_token', '')
        if not slack_token:
            logging.warn(
                'Slack is not correctly configured on TMS, '
                'please set "slack_token"in dev config')
        slack_url += slack_token

        slack = SlackClient(slack_url)

        for ticket in self:
            project = ticket.project_id and ticket.project_id.name or ''
            owner = ticket.owner_id and ticket.owner_id.slack_user_id or ''
            ticket_id = ticket.name
            ticket_url = ticket.get_ticket_url()
            ticket_summary = ticket.summary

            channel = '#%s' % project

            title = ':point_right: <@%s> : <@%s> poked you on the below ' \
                'forge ticket, please check the ticket.' \
                % (owner, poker)
            message = '<%s|%s>: %s' \
                % (ticket_url, 'F#' + str(ticket_id), ticket_summary)

            res = slack.success(channel, title, message, (':speaker:',))

            if res and not isinstance(res, dict) and res.status_code == 500:
                default_channel = ir_config_env.get_param(
                    'default_ft_slack_channel')
                if default_channel:
                    slack.success(default_channel, title,
                                  message, (':speaker:',))
                else:
                    logging.warn(
                        'No default forge ticket slack channel defined.')

    @api.onchange('type_quotation')
    def on_change_type_quotation(self):
        self.formula_parameter = self.type_quotation and \
            self.type_quotation.formula_parameter or ''

    @api.model
    def read_group(self, domain, fields, groupby, offset=0,
                   limit=None, orderby=False, lazy=False):
        domain = self.search_subscriber_on_ticket('forge_id', domain)
        if 'name' in fields:
            del fields[fields.index('name')]
        return super(TmsForgeTicket, self).read_group(
            domain=domain, fields=fields, groupby=groupby,
            offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    # ================================================
    # ======TODO EMAIL FORTMS FORGE TICKET============
    # ================================================
    KEY_FIGURE_MESSAGE = '<div style="font-size:11px;font-style:italic;' +\
        'margin-left:30px" title="%s">%s</div>'
    KEY_FIGURE_TARGET = '<span style="font-size:14px;' +\
        'color:black;"><b>%s<b></span></div>'

    @api.model
    def get_urgent_forge_tickets(self):
        # get very high forge tickets
        if self.check_urgent_tickets():
            return self.get_urgent_tickets()
        return 'No ticket'
    # get forge tickets need to be estimated and does not have associated
    # sprint

    @api.model
    def get_target_tickets_missing_estimations(self):
        return self.env['email.template'].\
            get_target_value('Missing estimations')

    @api.model
    def get_quantity_forge_ticket_sprint_not_estimate(self):
        tickets = self.search(
            [('state', '!=', 'closed'),
             ('development_time', '=', 0.01),
             ('sprint', '!=', False),
             ('project_id.state', '=', 'active')])
        numb = len(tickets)
        target_number = self.get_target_tickets_missing_estimations()
        email_env = self.env['email.template']
        target_description = email_env.\
            get_target_description('Missing estimations')
        target_number_string = ''
        if target_number > 0:
            result = email_env.\
                render_colored_key_figure(numb < target_number, numb)
        else:
            target_number_string = 'Missing or misconfigured target'
            result = email_env.\
                render_default_colored_key_figure(numb)

        result += self.KEY_FIGURE_TARGET % ' missing estimation'
        result += self.KEY_FIGURE_MESSAGE % (
            '', 'forge tickets without estimate and associated to a sprint')

        if target_number > 0:
            result += self.KEY_FIGURE_MESSAGE % \
                (target_description, 'target: less than %s' %
                 str(int(math.floor(target_number))))
        else:
            result += self.KEY_FIGURE_MESSAGE %\
                (target_description, target_number_string)

        return result

    @api.model
    def get_long_time_spent_forge_tickets(self):
        # Get object pool references
        config_env = self.env["ir.config_parameter"]
        long_time_spent = config_env.get_param(
            "forge_ticket_long_time_spent"
        )
        # Get a list of forget tickets
        sql_query = '''
            SELECT id
            FROM tms_forge_ticket
            WHERE time_spent > %s
            AND time_spent > (development_time + additional_budget_time)
            AND state IN ('assigned', 'wip')
            ORDER BY time_spent DESC;
        '''
        self._cr.execute(sql_query, (long_time_spent, ))
        res = self._cr.fetchall()
        forge_ticket_ids = [x[0] for x in res]

        # Return text to indicates no forget tickets found
        if not forge_ticket_ids:
            return 'No forge tickets with long time spent found.'

        forge_tickets = self.browse(forge_ticket_ids)

        # prepare table template for milestone display
        table_template = u"""
            <table border="1" style="border-collapse: collapse;">
                <tr style="background: #DDD;">
                    <th style="padding:5px 10px;">Project</th>
                    <th style="padding:5px 10px;">Ticket ID</th>
                    <th style="padding:5px 10px;">Total time spent</th>
                    <th style="padding:5px 10px;">Workload Estimate</th>
                    <th style="padding:5px 10px;">Developer</th>
                    <th style="padding:5px 10px;">Summary</th>
                </tr>
                {0}
            </table>
        """
        table_row_template = u"""
            <tr>
                <td style="padding:5px 10px; text-align: center;">{0}</td>
                <td style="padding:5px 10px; text-align: left;">
                    <a href="{1}">{2}</a>
                </td>
                <td style="padding:5px 10px; text-align: right;">{3}</td>
                <td style="padding:5px 10px; text-align: right;">{4}</td>
                <td style="padding:5px 10px; text-align: left;">{5}</td>
                <td style="padding:5px 10px; text-align: left;">{6}</td>
            </tr>
        """

        # Prepare the link to access forge ticket on TMS
        link_template = u"{0}#id={1}&view_type=form&model=tms.forge.ticket"
        conf_val = config_env.get_param(
            key="web.base.url",
            default="https://tms.trobz.com")
        base_url = conf_val + '/web?db=%s' % self._cr.dbname

        # List to store each composed row data
        row_results = []
        for ticket in forge_tickets:
            # Get the link and ticket name of forge ticket
            link, ticket_name = link_template.\
                format(base_url, str(ticket.id)), str(ticket.name)
            project = ticket.project_id.name
            time_spent, estimate = ticket.time_spent, ticket.development_time
            developer, summary = ticket.owner_id.name, ticket.summary

            # Compose arguments
            func_arguments = project, link, ticket_name,\
                time_spent, estimate, developer, summary

            # Compose row rendered data
            composed_row = table_row_template.format(*func_arguments)

            # Add composed row data to list
            row_results.append(composed_row)

        return table_template.format("".join(row_results))

    @api.model
    def get_working_days(self, date_start_obj, date_end_obj):
        weekdays = rrule.rrule(rrule.DAILY, byweekday=range(0, 5),
                               dtstart=date_start_obj, until=date_end_obj)
        now = datetime.now()
        public_holidays = self.env['hr.public.holiday'].search(
            [('is_template', '=', False), ('year', '=', now.year)])
        public_holidays = [hol.date for hol in public_holidays]
        list_weekdays = [day.strftime('%Y-%m-%d') for day in list(weekdays)]

        nb_working_days = len(list(set(list_weekdays) - set(public_holidays)))
        # Do not count start date
        return nb_working_days - 1

    @api.model
    def get_last_date_change_to_urgent(self):
        """
        @Function: get last date of interested changes for urgent ticket,
        which could be :
            - Date of priority change to `Very High`
            - Date of last changes for Assignee
        """
        tms_ticket_comment_env = self.env['tms.ticket.comment']
        last_date = self.create_date
        assignee = self.owner_id.name

        if self.tms_forge_ticket_comment_ids:
            comments = tms_ticket_comment_env.search(
                [('tms_forge_ticket_id', '=', self.id)],
                order='name desc')
            if comments:
                for comment in comments:
                    if u"=> Very High" in comment.comment:
                        last_date = comment.name
                        break
                    elif u"=> %s" % assignee in comment.comment:
                        last_date = comment.name
                        break
        return last_date

    @api.model
    def is_remove_qc_estimation(self, forge_id):
        # init value of is_remove_qc
        is_remove_qc = False

        # check forge ticket from js
        try:
            if type(int(forge_id[0])) != int:
                return is_remove_qc
        except ValueError:
            # in case new create forge ticket, and forge id is temp string
            return is_remove_qc

        # search forge ticket with forge_id
        forge = self.env['tms.forge.ticket'].search([('id', 'in', forge_id)])

        # init user param
        user = self.env.user

        # get group
        pm_group = 'tms_modules.group_profile_tms_delivery_team_manager'
        fc_group = 'tms_modules.group_profile_tms_functional_consultant'

        # get allow status form project
        allow_all_pm_fc = forge.project_id.is_all_pm_fc_view_qc_est
        # check conditon for 'is remove QC Value'
        if user.id == SUPERUSER_ID or user.has_group(pm_group):
            is_remove_qc = False
        elif user.has_group(fc_group):
            # block when:
            # - not allow all pm and fb
            # - and fc not in project support
            if not allow_all_pm_fc and user.id not in\
                    forge.project_id.project_supporter_rel_ids.ids:
                is_remove_qc = True
        else:
            # block for other members
            is_remove_qc = True

        return is_remove_qc

    @api.model
    def is_remove_std_dev_estimation(self, forge_id):
        if type(forge_id[0]) != int:
            return {
                'is_remove': False,
                'std_development_time': False,
            }
        forge = self.env['tms.forge.ticket'].search([('id', 'in', forge_id)])
        is_remove = True
        user = self.env.user
        profile_conf = self.env.ref(
            'tms_modules.profile_std_dev_time',
            raise_if_not_found=False)
        values = profile_conf.value
        values = values.split(",")
        tpm = 'tms_modules.group_profile_tms_technical_project_manager'
        if user.id == SUPERUSER_ID:
            is_remove = False
        elif user.has_group(tpm):
            allow_all_tpm = forge.project_id.is_all_tpm_view_std_est
            if allow_all_tpm:
                is_remove = False
            else:
                if forge.project_id.technical_project_manager_id.id == user.id:
                    is_remove = False
        else:
            for value in values:
                if user.has_group(value):
                    is_remove = False
        re = {
            'is_remove': is_remove,
            'std_development_time': forge.std_development_time,
        }
        return re

    @api.multi
    def download_support_attachments(self):
        self.ensure_one()
        reports_tmp_directory = tempfile.mkdtemp()
        date_time = datetime.now().strftime("%Y-%m-%d")
        zipfile_name = 'zip_all_file_attachments' + '_' + date_time + '.zip'
        zipfile_path = reports_tmp_directory + '/' + zipfile_name
        zf = zipfile.ZipFile(zipfile_path, mode='w')
        zf.close()
        ir_attachment_objs = self.get_attachments()
        dct_file_binary = self.create_dict_file_binary(ir_attachment_objs)
        for key, value in dct_file_binary.iteritems():
            self.add_file_to_directory(
                reports_tmp_directory, value, key)
        zip_files_name = [f for f in os.listdir(
            reports_tmp_directory) if os.path.isfile(
                os.path.join(
                    reports_tmp_directory, f)) and f != zipfile_name]
        if zip_files_name:
            zf = zipfile.ZipFile(zipfile_path, mode='a')
            for file_name in zip_files_name:
                zf.write(reports_tmp_directory +
                         '/' + file_name, file_name)
            zf.close()
        # Download zip file
        rp_file = '/download/support_attachment?path=%s&id=' % (
            zipfile_path)
        return {
            'type': 'ir.actions.report.xml',
            'report_type': 'controller',
            'report_file': rp_file,
        }

    @api.multi
    def get_attachments(self):
        ir_attachment_obj = self.env['ir.attachment']
        active_model = 'tms.support.ticket'
        support_ticket_id = self.tms_support_ticket_id.id
        ir_attachment_objs = ir_attachment_obj.search(
            [('res_model', '=', active_model),
             ('res_id', '=', support_ticket_id)])
        if ir_attachment_objs:
            return ir_attachment_objs
        else:
            raise Warning(
                'Error!',
                'This forge ticket has no support attachment'
            )

    @api.multi
    def create_dict_file_binary(self, ir_attachment_objs):
        dct_file_binary = {}
        lst_file_name = []
        for ir_attachment in ir_attachment_objs:
            # b64decode argument 1 must be string or buffer
            data = base64.b64decode(ir_attachment.datas or "")
            file_name = '%s_%s' % (
                ir_attachment.res_id, ir_attachment.name)
            if file_name in lst_file_name:
                file_name = self.get_filename_duplicate(
                    file_name, lst_file_name)
            lst_file_name.append(file_name)
            dct_file_binary.update({file_name: data})
        return dct_file_binary

    @api.model
    def get_filename_duplicate(self, file_name, lst_file_name):
        # Change name when name duplicate
        temp = file_name.split('.')
        count = 1
        if len(temp) == 2:
            name = file_name.replace('.', ' (%s).' % count)
            while (name in lst_file_name):
                count += 1
                name = file_name.replace('.', ' (%s).' % count)
        else:
            name = file_name + ' (%s)' % count
            while (name in lst_file_name):
                count += 1
                name = file_name + ' (%s)' % count
        return name

    @api.multi
    def add_file_to_directory(self, reports_tmp_directory, result, name):
        try:
            report_file = ''
            if name:
                report_file = '%s/%s' % (reports_tmp_directory, name)
                fp = open(report_file, 'wb+')
                fp.write(result)
                fp.close()
        except Exception:
            return False
        return True

    @api.multi
    @api.constrains('state')
    def constrains_state_to_closed(self):
        """
        Forge ticket only closed when there is no related test case in Fail
        """
        for forge in self:
            if forge.state != 'closed' or not forge.qc_testcase_ids:
                continue
            domain = [
                ('forge_ticket_id', '=', forge.id),
                ('test_result', 'in', ['fail', '', False])
            ]
            n_fail = forge.qc_testcase_ids.search_count(domain)
            if n_fail > 0:
                raise Warning(
                    'Forge ticket %s still have %s failed test cases!' % (
                        forge.id, n_fail))

    @api.multi
    @api.constrains('owner_id')
    def constrains_track_assignee(self):
        """
        Tracking info when change assignee
        """
        forge_assign_env = self.env['forge.ticket.assign']
        for forge in self:
            owner_id = forge.owner_id and forge.owner_id.id or None
            if not owner_id:
                continue
            vals = {
                'forge_id': forge.id,
                'date': datetime.now(),
                'assignee_id': owner_id,
                'forge_state': forge.state
            }
            forge_assign_env.create(vals)

    @api.multi
    def create_ticket_card(self):
        '''
         Create Card when user have group TMS Dev User
        '''
        user = self.env.user
        if not user.has_group('tms_modules.group_tms_dev_user'):
            return False
        user_id = user.id
        working_date = self.env['daily.mail.notification'].\
            get_current_sprint().strftime('%Y-%m-%d')
        for ticket in self:
            cards = ticket.card_ids
            card = cards.filtered(
                lambda c: c.assignee_id.id == user_id and
                c.working_date == working_date
            )
            if card:
                continue
            remain_pct_complete = 100 - sum(
                ticket.card_ids.mapped('pct_complete'))
            remain_pct_complete = remain_pct_complete > 0 and\
                remain_pct_complete or 0
            cards.create({
                'forge_ticket_id': ticket.id,
                'assignee_id': user_id,
                'pct_complete': remain_pct_complete,
                'working_date': working_date
            })
        return True

    @api.multi
    def get_parent_ticket_id(self):
        self.ensure_one()
        return self.parent_forge_ticket_id and\
            self.parent_forge_ticket_id.get_parent_ticket_id() or\
            self.id
