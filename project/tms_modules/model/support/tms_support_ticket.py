# -*- encoding: utf-8 -*-
from datetime import datetime, timedelta
from itertools import groupby
import logging
import math
from operator import itemgetter

from openerp import SUPERUSER_ID
from openerp import api, models, fields
from openerp.exceptions import Warning
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DF
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class TmsSupportTicket(models.Model):
    _inherit = "tms.ticket"
    _name = "tms.support.ticket"
    _description = "Support Ticket"

    FORGE_STATES = [
        ('child_open', 'Child Open'),
        ('assigned', 'Assigned'),
        ('wip', 'WIP'),
        ('code_completed', 'Code completed'),
        ('ready_to_deploy', 'Ready To Deploy'),
        ('in_qa', 'QA'),
        ('closed', 'Closed')
    ]

    dict_priority_mapping = {
        'urgent': 'very_high',
        'major': 'high',
        'normal': 'normal',
        'minor': 'low'
    }

    @api.onchange('missing_reactivity')
    def on_change_missing_reactivity(self):
        if not self.missing_reactivity:
            self.missing_reactivity_reason = False

    @api.onchange('ticket_type', 'manage_documentation')
    def on_change_ticket_type(self):
        """
        - `Documentation Required is checked if ticket type is not Defect.
        """
        if self.manage_documentation and self.ticket_type != 'defect':
            self.documentation_required = True
        else:
            self.documentation_required = False

    @api.onchange('documentation_required')
    def on_change_documentation_required(self):
        """
        Documentation Status is set by default to To do / Not Required
            when changing the value of the checkbox Documentation Required
        """
        if not self.documentation_required:
            self.documentation_status = 'not_required'
        elif self.documentation_required \
                and self.documentation_status == "not_required":
            self.documentation_status = 'to_do'

    @api.onchange('is_offered')
    def on_change_is_offered(self):
        if self.is_offered:
            self.invc_by_trobz_vn = False
            self.quotation_approved = False

    @api.onchange('invc_by_trobz_vn')
    def on_change_invc_by_trobz_vn(self):
        if self.invc_by_trobz_vn:
            self.is_offered = False

    @api.model
    def _get_default_project(self):
        result = None
        current_user = self.env.user
        if not current_user.is_trobz_member and self._uid > 1:
            result = current_user.default_project_id and \
                current_user.default_project_id.id or False
        return result

    @api.model
    def _get_default_customer(self):
        result = None
        model_access_env = self.env['ir.model.access']
        current_user = self.env.user
        if not current_user.is_trobz_member \
                and self._uid != SUPERUSER_ID \
                and not model_access_env.check_groups(
                    'tms_modules.group_trobz_partner'):
            assert current_user.employer_id, 'A non trobz member must have a \
                partner contact with a partner associated.'
            project = current_user.default_project_id
            if project and project.partner_id:
                assert current_user.employer_id.id == \
                    current_user.default_project_id.partner_id.id,\
                    'The configuration of the current user is not correct, ' \
                    'the default project and the partner contact are not ' \
                    'associated to the same partner'
            result = current_user.employer_id and \
                current_user.employer_id.id or False
        return result

    @api.depends('tms_working_hour_ids', 'tms_working_hour_ids.duration_hour')
    def _get_total_time_spent(self):
        return self.env['tms.ticket'].get_total_time_spent(self)

    @api.multi
    def button_higher_priority(self):
        """
        List of support ticket priority
        ('urgent','Very High'), ('major','High'),
        ('normal','Normal'), ('minor', 'Low')
        """
        for ticket in self:
            if ticket.priority == 'minor':
                ticket.priority = 'normal'
            elif ticket.priority == 'normal':
                ticket.priority = 'major'
            elif ticket.priority == 'major':
                ticket.priority = 'urgent'
        return True

    @api.multi
    def button_lower_priority(self):
        for ticket in self:
            if ticket.priority == 'urgent':
                ticket.priority = 'major'
            elif ticket.priority == 'major':
                ticket.priority = 'normal'
            elif ticket.priority == 'normal':
                ticket.priority = 'minor'
        return True

    @api.multi
    def get_subscriber_email_list(self, fields_change=[], context=None):
        result = self.env['tms.ticket'].get_subscriber_email_list(
            self.ids, 'tms.support.ticket',
            'support_ticket_subscriber_ids',
            fields_change=self._context.get('field_change'),
        )
        if len(self.ids) == 1:
            return result[self.ids[0]]
        return result

    @api.multi
    @api.depends("ticket_type")
    def _get_nbr(self):
        for ticket in self:
            if ticket.ticket_type:
                ticket.nbr = int(1)

    @api.depends('closing_datetime')
    def _get_date_end_gantt(self):
        for ticket in self:
            ticket.date_end_gantt = ticket.closing_datetime \
                or datetime.now().strftime(DF)

    @api.multi
    def _get_help_create(self):
        for ticket in self:
            ticket.help_create = False

    @api.multi
    def name_get(self):
        return [(ticket_id, 'S#%s' % ticket_id) for ticket_id in self.ids]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if name:
            self._cr.execute(
                'select id from tms_support_ticket where name::text ' +
                operator + ' %s', ('%' + name + '%',))
            ids = [ticket_id[0] for ticket_id in self._cr.fetchall()]
            recs = self.browse(ids)
        else:
            recs = self.search(args, limit=limit)

        return recs.name_get()

    @api.depends('tms_forge_ticket_id',
                 'tms_forge_ticket_id.state',
                 'tms_forge_ticket_id.child_forge_ticket_ids',
                 'tms_forge_ticket_id.child_forge_ticket_ids.state',
                 'tms_forge_ticket_id.delivery_status')
    def _get_delivery_status(self):
        """
        Calculate the delivery statuses of given support tickets.
        """
        for ticket in self:
            forge_ticket = ticket.tms_forge_ticket_id
            if forge_ticket:
                ticket.delivery_status = \
                    forge_ticket.delivery_status
                ticket.forge_state = forge_ticket.state
                # F#14241
                if forge_ticket.child_forge_ticket_ids:
                    for child_forge in forge_ticket.child_forge_ticket_ids:
                        if child_forge.state != 'closed':
                            ticket.forge_state = 'child_open'
                            break
            else:
                ticket.forge_state = None
                ticket.delivery_status = 'no_development'

    def get_year_month_week_last_modification(self):
        """
        Calculate the year, month, week from last modification date.
            Used for search and group by ability.
        Note that, this function only works correctly
            when being called in the write function.
        """
        return {
            'year': datetime.now().year,
            'month': datetime.now().month,
            'week': datetime.now().isocalendar()[1]
        }

    @api.multi
    def _get_opening_duration(self):
        """
        Get Opening Duration (ticket #1676).
        """
        for support_ticket in self:
            if not isinstance(support_ticket.id, int):
                continue
            if support_ticket.closing_datetime:
                end_datetime = datetime.strptime(
                    support_ticket.closing_datetime[:18], DF
                )
            else:
                end_datetime = datetime.now()
            create_date = support_ticket.create_date or False
            if not create_date:
                create_date = datetime.now()
            result = (
                end_datetime -
                datetime.strptime(str(create_date)[:18], DF)
            )
            time_hour = result.days * 24 + result.seconds / 3600
            support_ticket.opening_duration = result.days
            support_ticket.opening_duration_hour = time_hour

    @api.model
    def check_urgent_tickets(self):
        # Get list of urgent ticket (priority == very_high)
        domain = [
            ('state', '!=', 'closed'), ('priority', '=', 'urgent')]
        tickets = self.search(domain, limit=1)
        if tickets and len(tickets) > 0:
            return True
        return False

    @api.model
    def get_urgent_tickets(self):

        ticket_objs = self.search(
            [('state', '!=', 'closed'),
             ('priority', '=', 'urgent'),
             ('owner_id.is_trobz_member', '!=', False)
             ], order='project_id')
        grouped_lines = dict(
            (pro, [ticket for ticket in tickets])
            for pro, tickets in groupby(ticket_objs, itemgetter('project_id'))
        )

        # Build a list of urgent tickets to send mail
        result = ''

        for line in grouped_lines:
            result += '<div><b>' + line.name + '</b></div>'
            ticket_list = '<ul>'
            for ticket in grouped_lines[line]:
                ticket_link = ticket.get_ticket_url()
                time_stop = datetime.now()
                time_start = ticket.urgent_changed_date or \
                    ticket.get_last_date_change_to_urgent()
                time_start = datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S')
                time = time_stop - time_start
                hours = time.days * 24 + time.seconds / 3600
                ticket_list += u'<li><a href="{0}">{1}</a> ({2}, {3},'.format(
                    ticket_link, ticket.id, ticket.state,
                    ticket.owner_id.name or '') + \
                    u' opened for {0} hours): {1}</li>'.format(
                    hours, ticket.summary)
            result += ticket_list + '</ul>'

        return result

    # @Override order by clause
    def _generate_order_by(self, order_spec, query):
        my_order = """
            CASE
                WHEN tms_support_ticket.priority='urgent' THEN 0
                WHEN tms_support_ticket.priority='major' THEN 1
                WHEN tms_support_ticket.priority='normal' THEN 2
                WHEN tms_support_ticket.priority='minor' THEN 3
                ELSE 4
            END,
            CAST(tms_support_ticket.ownership_duration AS INTEGER) DESC,
            CAST(
                (SELECT
                    CASE WHEN tms_support_ticket.closing_datetime IS NOT NULL
                    THEN EXTRACT(DAY FROM
                                    now() - tms_support_ticket.create_date)
                    END AS opening_duration) AS INTEGER) DESC
        """
        if order_spec:
            return super(TmsSupportTicket, self)._generate_order_by(
                order_spec, query)
        return " ORDER BY {0}".format(my_order)

    # ticket 2883
    # ticket 3207 define a list of states
    list_states = [
        ('new', 'New'),
        ('assigned', 'Assigned'),
        ('planned_for_delivery', 'Planned for delivery'),
        ('delivered', 'Delivered in Staging'),
        ('ok_for_production', 'OK for production'),
        ('ok_to_close', 'OK to close'),
        ('closed', 'Closed')
    ]

    list_priority = [
        ('urgent', 'Very High'),
        ('major', 'High'),
        ('normal', 'Normal'),
        ('minor', 'Low')
    ]

    list_ticket_type = [
        ('unclassified', 'Unclassified'),
        ('initial_project', 'Initial Project'),
        ('functional_support', 'Functional Support'),
        ('evolution', 'Evolution'),
        ('adjustment', 'Adjustment'),
        ('defect', 'Defect'), ('other', 'Other')
    ]

    # 2952 define list of Missing Reactivity Reason
    @api.model
    def _get_missing_reactivity_reason_list(self):
        target = self.get_target_tickets_ready_for_staging()
        res = [
            ('unclassified', 'Unclassified tickets must not be owned by \
            trobz for more than 1 day'),
            ('project_missing_reactivy', 'For each project, at least \
            one action by Trobz must be taken every day'),
            ('defect_wo_forge', 'For a ticket of the type Defect, \
            a forge ticket must be created'),
            ('deploy_in_staging', 'More than %s tickets are related to \
            forge tickets in the Delivery Status: Ready for Staging' % (
                target)),
            ('urgent_over_day', 'Urgent ticket owned for more than 1 day'),
            ('not_low_over_20_day', 'Support ticket owned by trobz for \
             more than 20 days (not low priority)')]
        return res

    # List of delivery status
    delivery_statuses = [
        ('no_development', 'No Development'),
        ('in_development', 'In Development'),
        ('in_integration', 'In Integration'),
        ('ready_for_staging', 'Ready for Staging'),
        ('in_staging', 'In Staging'),
        ('in_production', 'In Production')
    ]

    # List of documentation status
    list_documentation_status = [
        ('to_do', 'To do'),
        ('in_progress', 'In progress'),
        ('to_review', 'To review'),
        ('done', 'Done'),
        ('not_required', 'Not Required')
    ]

    @api.depends('project_id',
                 'project_id.trobz_partner_id')
    def _get_trobz_partner_id(self):
        for ticket in self:
            ticket.trobz_partner_id = (
                ticket.project_id.trobz_partner_id and
                ticket.project_id.trobz_partner_id.id or False)

    @api.multi
    def _is_usr_trobz_member_partner(self):
        """
        Decide if current user is a Trobz member or a Trobz partner.
        Trobz members and Trobz partners have more privileges than other users.
        """
        ticket = self and self[0]
        user_env = self.env['res.users']
        config_env = self.env['ir.config_parameter']

        partner_prof_param_objs = config_env.search(
            [('key', '=', 'trobz_partner_profiles')],
            order='id', limit=1
        )
        trobz_partner_profiles = []
        if partner_prof_param_objs:
            partner_prof_param = partner_prof_param_objs.value
            if partner_prof_param:
                trobz_partner_profiles = partner_prof_param.split(',')

        is_usr_trobz_partner = user_env.has_groups(trobz_partner_profiles)
        ticket.is_usr_trobz_partner = is_usr_trobz_partner
        ticket.is_usr_trobz_member = user_env.browse(self._uid).is_trobz_member

    @api.multi
    def _is_subscribed(self):
        """
        If current user is in ticket subscribers > True
        else: False
        Use this field to show the button subscriber/unsubscribe
        """
        for ticket in self:
            is_subscribed = False
            user_ids = [x.name.id for x in
                        ticket.support_ticket_subscriber_ids]
            if self._uid in user_ids:
                is_subscribed = True
            ticket.is_subscribed = is_subscribed

    @api.multi
    @api.depends('time_spent')
    def _compute_total_time_spent_day(self):
        """
            Compute total time spent of the tickets by days
        """
        for support_ticket in self:
            support_ticket.time_spent_day = support_ticket.time_spent / 8

    # Columns
    name = fields.Integer(
        string='Ticket ID', readonly=True
    )
    ticket_type = fields.Selection(
        list_ticket_type, 'Ticket type', required=True, default='unclassified'
    )
    date_end_gantt = fields.Datetime(
        compute='_get_date_end_gantt',
        string='Date End',
        help='End of the bar in the gantt chart for \
        this ticket (closing date or today).'
    )
    tms_functional_block_id = fields.Many2one(
        comodel_name='tms.functional.block', string='Functional Block',
        help='Automatically synchronized with related Forge/Support ticket.',
        domain="['|', ('project_ids', 'ilike', "
               "project_id and [project_id] or []),"
               "('project_ids', '=', False)]")
    tms_project_tag_ids = fields.Many2many(
        string='Tags',
        comodel_name='tms.project.tag',
        relation='support_ticket_project_tag_rel',
        column1='support_ticket_id',
        column2='tag_id',
        domain="[('project_id', '=', project_id)]",
        help='Automatically synchronized with related Forge/Support ticket.'
    )
    workload = fields.Float(
        'Workload',
        help='In days, for evolutions and defects',
        digits=(16, 3)
    )
    date = fields.Date(
        'Invoicing date',
        help='Used to define on which month \
            the workload has been invoiced'
    )
    tms_forge_ticket_id = fields.Many2one(
        'tms.forge.ticket', 'Forge ticket'
    )
    forge_state = fields.Selection(
        compute='_get_delivery_status',
        selection=FORGE_STATES,
        string='Forge State',
        store=True
    )
    owner_id = fields.Many2one(
        'res.users', 'Assignee', ondelete='restrict',
        domain="[('supporter_of_project_ids', '=like', project_id)]"
    )
    state = fields.Selection(
        selection=list_states, string='Status', required=True, default='new')
    tms_support_ticket_comment_ids = fields.One2many(
        comodel_name='tms.ticket.comment',
        inverse_name='tms_support_ticket_id',
        string='Comments'
    )
    tms_working_hour_ids = fields.One2many(
        comodel_name='tms.working.hour',
        inverse_name='tms_support_ticket_id',
        string='Working hours'
    )
    time_spent = fields.Float(
        compute='_get_total_time_spent', store=True,
        string='Time Spent', help='In hours'
    )
    additional_subscribers = fields.Char(
        'Additional subscribers', size=512,
        help='For people without account.Add email addresses to '
             'notify when changes are done on this ticket. '
             'Separate email addresses by a comma.'
    )
    nbr = fields.Integer(
        compute='_get_nbr',
        string='# of tickets', store=True
    )

    priority = fields.Selection(
        selection=list_priority, string='Priority', required=True,
        default='normal',
        help='Automatically synchronized with related Forge/Support ticket.')
    help_create = fields.Text(
        compute='_get_help_create', string='Help Create'
    )
    workload_char = fields.Char(
        'Workload', size=10, default='0.0',
        help='If the ticket is invoiceable: Time Sold in days.\n'
             'If the ticket is not invoiceable: '
             'a workload which can be used for planning.'
    )
    delivery_status = fields.Selection(
        compute='_get_delivery_status',
        selection=delivery_statuses,
        string='Delivery Status',
        store=True
    )
    is_support_contract = fields.Boolean(
        'Support Contract', default=False)
    create_date = fields.Datetime(
        'Opening Date', readonly=True, default=fields.Date.today())

    opening_duration = fields.Integer(
        compute='_get_opening_duration',
        string="Opening Duration"
    )
    opening_duration_hour = fields.Integer(
        compute='_get_opening_duration',
        string="Opening Duration (Hours)"
    )
    year = fields.Char('Year', size=4)
    month = fields.Char('Month', size=2)
    week = fields.Char('Week', size=2)
    quotation_approved = fields.Boolean(
        'Quotation Approved', default=False,
        help='This field will be updated by Trobz team'
    )

    # just using for selection of quotation approved in search view
    select_quotation = fields.Selection([
        ('yes', 'Approved'),
        ('no', 'Not Approved')],
        string='Quotation ?',
        help='This field will be updated by Trobz team'
    )

    project_state = fields.Selection(
        related='project_id.state',
        selection=[
            ('potential', 'Potential'),
            ('active', 'Active'),
            ('done', 'Done'),
            ('asleep', 'Asleep')
        ],
        string="Project State",
        readonly=True
    )

    ownership_date = fields.Date('Ownership Date')
    ownership_duration = fields.Char(
        string='Ownership Duration(days)', size=10, default='0'
    )
    trobz_ownership_total_time = fields.Char(
        'Trobz Ownership Total Time', size=10, default='0'
    )
    missing_reactivity = fields.Boolean("Missing Reactivity")
    missing_reactivity_reason = fields.Selection(
        _get_missing_reactivity_reason_list, "Missing reactivity reasons"
    )
    internal_comment = fields.Text("Internal Comment")
    quotation_approved_date = fields.Datetime("Quotation Approval Date")
    staging_delivery_date = fields.Datetime("Staging Delivery Date")
    ok_production_date = fields.Datetime("Ok Production Date")
    is_offered = fields.Boolean('Offered')

    trobz_partner_id = fields.Many2one(
        compute='_get_trobz_partner_id',
        comodel_name="res.partner",
        string='Partner',
        store=True
    )
    milestone_id = fields.Many2one(
        comodel_name='tms.milestone', string='Milestone',
        help="Automatically synchronized with related Forge/Support ticket.",
        domain="[('project_id', '=', project_id)]"
    )
    milestone_number = fields.Char(
        related="milestone_id.number", size=30,
        string="Milestone", store=True
    )

    invc_by_trobz_vn = fields.Boolean(
        'Invoiceable', default=True,
        help="Set by default to True, then updated based on the activity. "
             "Use this field to manage the list of tickets in the menu "
             "Rescue Support to invoice.")
    is_usr_trobz_member = fields.Boolean(
        compute='_is_usr_trobz_member_partner',
        string='Is Trobz Member'
    )
    is_usr_trobz_partner = fields.Boolean(
        compute='_is_usr_trobz_member_partner',
        string='Is Trobz Partner',
        store=True
    )

    support_ticket_subscriber_ids = fields.One2many(
        comodel_name='tms.subscriber',
        inverse_name='support_id', string="Ticket Subscriber"
    )
    is_subscribed = fields.Boolean(
        compute='_is_subscribed',
        string='Is Subscribed'
    )
    manage_documentation = fields.Boolean('Manage Documentation')
    documentation_required = fields.Boolean('Documentation Required')
    documentation_links = fields.Text('Documentation Links')
    documentation_status = fields.Selection(
        list_documentation_status, string="Documentation Status",
        default='not_required'
    )

    analytic_secondaxis_id = fields.Many2one(
        related='tms_activity_id.analytic_secondaxis_id',
        string='Analytic Secondaxis',
        readonly=True,
        store=True
    )

    project_id = fields.Many2one(
        'tms.project', string='Project', required=True,
        default=lambda self: self._get_default_project(),
        help='Automatically synchronized with related Forge/Support ticket.')
    proj_owner_id = fields.Many2one(
        related='project_id.owner_id',
        string="Project's Owner", store=True
    )
    description = fields.Text(
        help="Customer can only change the description when the workload "
             "has not already been set. If you wish to change the "
             "description, please add a comment to request a change, "
             "then Trobz project manager will update the description and "
             "will take into your new request in the workload."
    )
    team_id = fields.Many2one(string='Team', related='project_id.team_id',
                              store=True)
    team_manager_id = fields.Many2one(
        string="Team Manager", related='project_id.team_id.team_manager',
        store=True)
    customer_id = fields.Many2one(
        comodel_name='res.partner', string='Customer', required=True,
        help='Hidden field used for access rules',
        default=lambda self: self._get_default_customer())
    milestone_date = fields.Date(
        'Milestone Date', related='milestone_id.date',
        store=True, readonly=True)
    workload_achieved = fields.Float(
        'Workload Achieved', digits=(16, 3),
        store=True, compute="_compute_workload_achieved"
    )
    time_spent_day = fields.Float(
        'Time Spent', digits=(16, 2),
        store=True, compute="_compute_total_time_spent_day")
    deadline = fields.Date('Deadline', store=True)
    sp_check_manage_dealine_on_sp_tickets = fields.Boolean(
        related='project_id.manage_dealine_on_sp_tickets',
        string='Manage Deadline on Support Tickets', readonly=True)

    @api.multi
    @api.depends('state', 'resolution', 'workload')
    def _compute_workload_achieved(self):
        """
        Compute the workload achieved of a support ticket based on the
        resolution and status of that ticket with the logic below
        - If the resolution is set but it is not "Fixed", the workload achieved
          is 0.
        - Otherwise
          - Status "Planned for Delivery": workload achieved = workload * 0.7
          - Status "Delivered in Staging": workload achieved = workload * 0.8
          - Status "OK for Production": workload achieved = workload * 0.9
          - Status "Closed" or "OK to Close": workload achieved = workload
        """
        for support_ticket in self:
            if (support_ticket.resolution and
                    support_ticket.resolution != 'fixed') or \
                    not support_ticket.workload:
                support_ticket.workload_achieved = 0
                continue
            factor = 0
            if support_ticket.state == 'delivered':
                factor = 0.8
            elif support_ticket.state == 'ok_for_production':
                factor = 0.9
            elif support_ticket.state in ('closed', 'ok_to_close'):
                factor = 1.0
            elif support_ticket.state == 'planned_for_delivery':
                factor = 0.5
            support_ticket.workload_achieved = factor * support_ticket.workload
        return

    urgent_changed_date = fields.Datetime(string="Urgent Changed Start",
                                          readonly=True)

    @api.model
    def _get_account_manager_id(self, project):
        trobz_account_manager_id = \
            project and project.default_supporter_id and\
            project.default_supporter_id.id or False
        return trobz_account_manager_id

    @api.model
    def _get_tpm_id(self, project):
        return project and project.technical_project_manager_id and \
            project.technical_project_manager_id.id or False

    @api.multi
    def get_default_project_mailing_list(self):
        """
            Get default mailing list email of a specific project,
                if no mailing list
            defined, get the default mailing list project from config parameter
        """
        config_pool = self.env["ir.config_parameter"]

        # get ticket information, we need project id
        ticket = self[0]

        # get default email
        default_mail = config_pool.get_param(
            "trobz_default_project_mailing_list_email")

        # get project information (mailing list email)
        project = ticket.project_id

        # use mailing list email from project or use default one
        # Mailing list being mandatory on the project, the " or default_mail"
        #    is here only
        # for (data) backward compatibility and to ensure that no customer
        #    would face an error due to
        # missing mailing list on the project.

        mail_list = []
        if project:
            for mailing in project.mailing_list_ids:
                if mailing.is_used_for_sup_notif:
                    mail_list.append(mailing.name + "@lists.trobz.com")
        mailling_list_txt = ', '.join(mail_list)
        return mailling_list_txt or default_mail

    @api.model
    def check_blocked_project(self, project):
        """
        Function to check blocked project:
            - Only user with Admin Profile can create / update support ticket
            of blocked project
        """
        if project.is_blocked and not self.env.user.is_admin_profile():
            raise Warning(
                'Error!', 'Sorry, it seems your Support contract is '
                          'outdated. Please contact Trobz by email for '
                          'more information.')

    @api.model
    def create(self, vals):
        """
         - Check Blocked Project.
         - Set is_support_contract based on project.
         - Update workload, Workload_char.
         - Forbid the modification of user who is not Admin or Supporter.
         - Forbid the modification on activity of user who is not Trobz member.
         - If Assignee:
           - Set ownership and ownership duration.
         - If Not Assignee:
           - Set Assignee based on default supporter of project or parameter
           `support_default_trobz_owner`
         - If related to forge ticket
           - Update milestone.
           - Update project tag.
         - Create comment `Creation of the ticket`.
         - Update subscriber.
         - Update ticket name by ticket number.
         - Send Notification Email.
        """
        ctx = self._context and self._context.copy() or {}
        project_env = self.env['tms.project']
        forge_ticket_env = self.env['tms.forge.ticket']
        res_users_env = self.env['res.users']
        project_id = vals.get('project_id', False)
        activity_id = vals.get('tms_activity_id', False)
        owner_id = vals.get('owner_id', False)
        forge_ticket_id = vals.get('tms_forge_ticket_id', False)
        ticket_comment_ids = vals.get("tms_support_ticket_comment_ids", [])
        new_state = vals.get('state', '')
        current_user = self.env.user
        is_trobz_member = current_user.is_trobz_member

        # Only user with Admin Profile can create / update support ticket
        # of blocked project.
        # Set "is_support_contract" based on project
        project = project_env.browse(project_id)
        self.check_blocked_project(project)
        vals['is_support_contract'] = project.is_support_contract

        if current_user.group_profile_id \
                and current_user.group_profile_id.name == \
                'TMS Customer Reporter Only Profile':
            if new_state != 'new':
                raise Warning(
                    'Forbidden action!',
                    'You can only create a ticket in status "New"!')
        try:
            temp = round(float(vals.get('workload_char', 0)), 3)
            vals.update({'workload_char': '%.3f' % temp})
            vals.update({'workload': temp})
        except Exception:
            raise Warning('Error!', 'Workload must be float type.')

        if is_trobz_member:
            if not self.check_supporter(self._uid, project):
                raise Warning(
                    "Forbidden action!",
                    "Only supporters of project can create support tickets.")

        elif activity_id and self._uid != SUPERUSER_ID:
            raise Warning(

                'Forbidden action!',
                'You cannot set value of the Activity field!')

        if owner_id:
            # Set the Owner Duration day
            vals['ownership_date'] = datetime.now()
            vals['ownership_duration'] = 0

            user_env = self.env(self._cr, owner_id, ctx)
            is_customer_group = res_users_env.with_env(user_env).has_group(
                'tms_modules.group_tms_customer')
            if is_customer_group:
                vals['missing_reactivity'] = False
        else:
            if is_trobz_member:
                raise Warning(
                    'Forbidden action!',
                    'You must set a assignee for this ticket!')
            owner_id = self._get_account_manager_id(project)
            vals['owner_id'] = owner_id

        # If there is a related forge ticket, get milestone_id of forge
        if forge_ticket_id:
            forge = forge_ticket_env.browse(forge_ticket_id)

            # get milestone of related forge ticket
            vals['milestone_id'] = forge.milestone_id \
                and forge.milestone_id.id or False

            # get tag of related forge ticket
            vals['tms_project_tag_ids'] = [
                (6, 0, forge.tms_project_tag_ids.ids)]

        # Ticket creation comment
        ticket_creation_vals = [[0, False, {
            'comment': 'Creation of the ticket',
            'type': 'changelog',
            'name': str(datetime.now())}]]
        vals["tms_support_ticket_comment_ids"] = ticket_creation_vals + \
            ticket_comment_ids

        # Update Subscriber
        ctx.update({'subscriber_from_support_ticket': True})
        vals = self.with_context(ctx).get_vals_ticket_subcribers(
            project, owner_id, vals, [])
        ticket = super(TmsSupportTicket, self.with_context(ctx)).create(vals)

        # Take the id of the ticket as its name
        self.update_ticket_name(ticket, 'tms_support_ticket')

        # Send Notification Email
        # Use this context in get_subscriber_email_list
        ctx.update({'create_support_ticket': True})
        # If the creation of a support ticket is from an auto test, skip
        # sending the email.
        if not project.mute_mail_noti and not ctx.get('test_support_ticket'):
            template = self.env.ref(
                'tms_modules.tms_support_notification_email_html_template')
            template.with_context(ctx)._send_mail_asynchronous(ticket.id)

        # comment check is_notification_sent always to ignore sent old comment
        # when project is mute_mail_noti or uncheck mute_mail_noti
        ticket.check_sent_comment('tms_support_ticket_comment_ids')

        if vals.get('tms_forge_ticket_id', False):
            forge_id = vals['tms_forge_ticket_id']
            forge_obj = self.env['tms.forge.ticket'].browse(forge_id)
            support_on_forge = forge_obj.tms_support_ticket_id or False
            if support_on_forge:
                raise Warning(
                    'Warning!',
                    'Cannot set the support ticket for the forge ticket\n'
                    'Because this forge ticket had another support ticket'
                )
            else:
                forge_obj.tms_support_ticket_id = ticket.id or False
                forge_obj.tms_working_hour_ids and \
                    forge_obj.tms_working_hour_ids.sudo().write(
                        {'tms_support_ticket_id': ticket.id})
        return ticket

    # TODO-LOW: It should not be possible to choose a activity
    #    that do not belong to the active project.
    #    It is currently possible when doing:
    # - Select customer A
    # - Choose activity of customer A
    # - Change to customer B

    @api.model
    def control_support_ticket(
        self, owner_id, milestone_id, activity_id, reporter_id,
            func_block_id, project_tag_ids, tms_forge_ticket_id, project):
        """
        Control support ticket to avoid setting values from the wrong project
        """
        warning_msgs = []
        user_env = self.env['res.users']
        milestone_env = self.env['tms.milestone']
        forge_env = self.env['tms.forge.ticket']
        activity_env = self.env['tms.activity']
        functional_block_env = self.env['tms.functional.block']
        project_tag_env = self.env['tms.project.tag']

        is_customer = user_env.has_group('tms_modules.group_tms_customer')
        prj_supporter_ids = [supporter.id for supporter in
                             project.project_supporter_rel_ids]

        # Check Assignee
        if owner_id:
            assignee = user_env.sudo().browse(owner_id)
            if owner_id not in prj_supporter_ids:
                warning_msgs.append(
                    "S#%d - The assignee %s is not in the "
                    "supporters of the project %s" % (
                        self.name, assignee.name, project.name))

        # Check Milestone
        if milestone_id:
            milestone_obj = milestone_env.sudo().browse(milestone_id)
            if milestone_id not in project.milestones.ids:
                warning_msgs.append(
                    "S#%d - The milestone %s is not in the "
                    "milestones of the project %s" % (
                        self.name, milestone_obj.name, project.name))
            if is_customer and milestone_obj.state not in ['planned',
                                                           'development']:
                # This control is only applied for the customer
                warning_msgs.append(
                    "You cannot assign this support ticket" +
                    " to this milestone because its development" +
                    " is complete. For this operation, the status" +
                    " of the new milestone should be Planned or" +
                    " Development. Please send an email to the project" +
                    " mailing list if it is critical to change the" +
                    " milestone (at this stage this action will" +
                    " require extra work)."
                )
            if tms_forge_ticket_id:
                related_forge_ticket = forge_env.sudo().browse(
                    tms_forge_ticket_id)
                if is_customer and \
                    (related_forge_ticket.state != 'assigned' or
                        related_forge_ticket.completion_sprint_date):
                    # This control is only applied for the customer
                    warning_msgs.append(
                        "You cannot change the milestones on this support "
                        "ticket because it is related to a Forge ticket "
                        "(development tasks) which has started already. "
                        "Please send an email to the project mailing list "
                        "if it is critical to change the milestone "
                        "(at this stage this action will require "
                        "extra work)."
                    )
        # Check activity
        if activity_id:
            activity_obj = activity_env.sudo().browse(activity_id)
            if activity_id not in project.activity_ids.ids:
                warning_msgs.append(
                    "S#%d - The activity %s is not in the "
                    "activities of the project %s" % (
                        self.name, activity_obj.name, project.name))

        # Check reporter
        if reporter_id:
            reporter = user_env.sudo().browse(reporter_id)
            if reporter_id not in prj_supporter_ids:
                warning_msgs.append(
                    "S#%d - The reporter %s is not in the "
                    "supporters of the project %s" % (
                        self.name, reporter.name, project.name))

        # Check functional Block
        if func_block_id:
            funct_block_obj = functional_block_env.sudo().browse(
                func_block_id)
            prj_funct_block_ids = project.functional_block_ids.ids
            # Global functional block
            all_func_blocks = functional_block_env.sudo().search([])
            prj_funct_block_ids += [
                func_block.id for func_block in all_func_blocks
                if not func_block.project_ids]

            if func_block_id not in prj_funct_block_ids:
                warning_msgs.append(
                    "S#%d - The functional block %s is not in the "
                    "functional blocks of the project %s or not a "
                    "global functional block" % (
                        self.name, funct_block_obj.name, project.name))

        # Check Tag
        if project_tag_ids:
            tag_objs = project_tag_env.sudo().browse(project_tag_ids)
            project_tags = project.project_tag_id
            unknow_tags = tag_objs.filtered(lambda x: x not in project_tags)
            for tag_obj in unknow_tags:
                warning_msgs.append(
                    "S#%d - The tag %s is not in the "
                    "tags of the project %s" % (
                        self.name, tag_obj.name, project.name))

        if warning_msgs:
            display_msg = '\n'.join(warning_msgs)
            raise Warning('Error!', display_msg)
        return True

    def check_workload(self, workload_char, vals):
        try:
            temp = round(float(workload_char), 3)
            vals.update({'workload_char': '%.3f' % temp,
                         'workload': temp})
        except Exception:
            raise Warning('Error!', 'Workload must be float type.')
        return vals

    def forbid_action_of_not_trobz_user(
            self, ticket_type, workload, workload_char, invoicing_date,
            new_state):
        # Forbid setting ticket type, workload, invoicing date
        # if not trobz member.
        if ticket_type or workload or workload_char or invoicing_date:
            raise Warning(
                "Forbidden action!",
                "You cannot change ticket type, workload, invoicing date "
                "on a ticket!"
            )
        # Only Trobz employees are able to close a Support Ticket
        if new_state == 'closed':
            raise Warning(
                "Access Denied!",
                "Only Trobz team can close a Support Ticket. " +
                "Use the button on the right 'OK to Close', " +
                "then Trobz team will take care of closing the ticket " +
                "after ensuring of the proper classifications " +
                "(ticket type, functional block, resolution ...)."
            )

    def check_reporter_profile(self, new_state, old_state, vals):
        if new_state:
            raise Warning(
                "Forbidden action!",
                "You are not allowed to change status of the ticket!")
        if old_state != 'new' and (
            len(vals.keys()) == 1 and vals.keys()[
                0] != 'tms_support_ticket_comment_ids') or\
                (len(vals.keys()) > 1):
            raise Warning("Forbidden action!",
                          "You can only add comments on the ticket!")

    @api.constrains('state', 'invc_by_trobz_vn', 'workload_char', 'date',
                    'resolution', 'is_offered', 'quotation_approved')
    def check_invoicing_rules_inconsistencies(self):
        if self.state == 'closed' and \
                self.invc_by_trobz_vn and \
                float(self.workload_char) > 0.0 and \
                not self.date and \
                self.resolution == 'fixed' and\
                not self.is_offered and\
                not self.quotation_approved:
            raise Warning('Forbidden action!',
                          'The ticket {%s} cannot be closed due to '
                          'invoicing rules inconsistencies. '
                          'It cannot have at the same time'
                          ' Invoiceable = True, Workload > 0, '
                          'Invoicing Date not set, '
                          'Resolution = Fixed, Offered = False and '
                          'Quotation not Approved.' % self.name)

    @api.multi
    def check_change_deadline(self):
        for record in self:
            record.deadline = False
        return True

    @api.multi
    def write(self, vals):
        """
         - Check type of workload.
         - Forbid setting ticket type, workload, invoicing date or close
         support ticket if not trobz member.
         - Check `missing_reactivity`.
         - Update `date, month, year` of last modification date.
         - Update quotation approved date for support ticket.
         - Add controls to avoid setting wrong values related to project
              in case mass editing.
         - Prevent `TMS Customer Reporter Only Profile`:
            + Change state.
            + Modifying any fields except comments.
         - Block users which profile is not Admin Profile,
              to modify blocked project.
         - Only allow supporters update the support tickets.
         - Ensure that ticket type is not set to "Unclassified"
              when state in ['planned_for_delivery', 'delivered',
              'ok_for_production']
         - Update date of production or staging delivery
              for corresponding status.
         - Ensure that resolution is set when closing ticket.
         - Ensure that Unclassified ticket can not be closed.
         - Ensure that ticket can not be closed
              if forge ticket is not closed or functional block is not set.
         - Set ownership, is_support_contract.
         - Update milestone_id, project_id, tms_activity_id, tag_id,
              priority to related forge ticket.
         - Send the Notification Support Email.
         - Updating documentation_required.
         - Update Subscriber for support ticket.
         - Prevent user change project_id if time_spent has been set.
        """
        context = self._context and self._context.copy() or {}
        project_env = self.env['tms.project']
        res_users_env = self.env['res.users']
        new_state = vals.get('state', '')
        workload_char = vals.get("workload_char", False)
        workload = vals.get("workload", False)
        project_id = vals.get('project_id', False)
        new_forge_ticket_id = vals.get("tms_forge_ticket_id", False)
        ticket_type = vals.get('ticket_type', '')
        invoicing_date = vals.get("date", False)
        resolution = vals.get('resolution', '')
        closing_datetime = vals.get('closing_datetime', False)
        func_block_id = vals.get('tms_functional_block_id', False)
        owner_id = vals.get('owner_id', False)
        owner_ship_date = vals.get('ownership_date', False)
        priority = vals.get('priority', '')
        doc_status = vals.get('documentation_status', '')
        activity_id = vals.get('tms_activity_id', False)
        # Prevent miss-understand of milestone_id is changed or not.
        if 'milestone_id' in vals:
            milestone_id = vals['milestone_id']
        else:
            milestone_id = None
        tag_ids = vals.get('tms_project_tag_ids', [])
        # M2m fields
        if tag_ids and len(tag_ids[0]) == 3:
            tag_ids = tag_ids[0][2]
        reporter_id = vals.get('reporter_id', False)

        current_user = self.env.user
        profile_name = current_user.group_profile_id.name
        is_trobz_member = current_user.is_trobz_member

        # Check fields deadline if change state
        if new_state == 'delivered':
            self.check_change_deadline()

        # Check type of workload.
        if workload_char:
            vals = self.check_workload(workload_char, vals)

        # Forbid setting ticket type, workload, invoicing date or close
        # support ticket if not trobz member.
        if not is_trobz_member:
            self.forbid_action_of_not_trobz_user(
                ticket_type, workload, workload_char, invoicing_date,
                new_state)

        if not workload_char and 'workload_char' in vals.keys():
            try:
                temp = round(float(vals.get('workload_char', 0)), 3)
                vals.update({'workload_char': '%.3f' % temp})
                vals.update({'workload': temp})
            except Exception:
                raise Warning('Error!', 'Workload must be float type.')

        # Check missing reactivity
        if 'missing_reactivity' in vals and not vals['missing_reactivity']:
            vals['missing_reactivity_reason'] = False

        # Calculate the year, month, week from last modification date.
        #    Used for search and group by.
        vals.update(self.get_year_month_week_last_modification())

        # Add quotation approved date for support ticket
        if 'quotation_approved' in vals and\
                vals.get('quotation_approved', False):
            vals.update({'quotation_approved_date': str(datetime.now())})
        elif 'quotation_approved' in vals and\
                not vals.get('quotation_approved', False):
            vals.update({'quotation_approved_date': False})
        project = None

        for old_ticket in self:
            old_forge_ticket = old_ticket.tms_forge_ticket_id
            old_state = old_ticket.state

            project = project_id and project_env.browse(project_id) or \
                old_ticket.project_id

            # block any creation on support ticket except
            # users with the profile Admin.
            self.check_blocked_project(project)

            forge_ticket_id = new_forge_ticket_id or \
                (old_forge_ticket and old_forge_ticket.id or False)

            # When using the mass update, add some controls to avoid
            # setting values from the wrong project
            old_ticket.control_support_ticket(
                owner_id, milestone_id, activity_id, reporter_id,
                func_block_id, tag_ids, forge_ticket_id, project)

            # For Group TMS Customer Reporter Only Profile
            if profile_name == 'TMS Customer Reporter Only Profile':
                old_ticket.check_reporter_profile(new_state, old_state, vals)

            elif not self.check_supporter(self._uid, project) and \
                    self._uid != SUPERUSER_ID:  # Exception for admin to update
                                                # the data occasionally
                raise Warning("Forbidden action!",
                              "Only supporters of project can update "
                              "the support tickets.")

            ticket_vals = vals.copy()

            # Ensure that Ticket type is not set to "Unclassified"
            # (only for some status)
            if is_trobz_member:
                old_ticket.check_support_ticket_type(
                    new_state or old_ticket.state,
                    ticket_type or old_ticket.ticket_type)

            # Update Date for Production or Staging when changing corresponding
            # status
            if new_state == 'closed':
                dict_val = old_ticket.check_info_when_closing_ticket(
                    closing_datetime, resolution, ticket_type, forge_ticket_id,
                    old_forge_ticket, func_block_id)
                ticket_vals.update(dict_val)
            else:
                dict_val = old_ticket.update_progress_date(new_state)
                ticket_vals.update(dict_val)
            if owner_id and not owner_ship_date:
                ticket_vals['ownership_date'] = datetime.now()
                ticket_vals['ownership_duration'] = '0'
                user_env = self.env(self._cr, owner_id, context)
                is_customer_group = res_users_env.with_env(user_env).has_group(
                    'tms_modules.group_tms_customer')
                if is_customer_group:
                    ticket_vals['missing_reactivity'] = False

            if project_id:
                ticket_vals['is_support_contract'] = project and \
                    project.is_support_contract or False
                if old_ticket.time_spent > 0.01:
                    raise Warning(
                        "Forbidden action!",
                        "Cannot change Project when Time spent has been set.")

            # Update milestone_id, project_id, tms_activity_id, tag
            # to related forge ticket.
            if forge_ticket_id:
                old_ticket.update_value_for_related_forge_ticket(
                    forge_ticket_id, activity_id, milestone_id, func_block_id,
                    tag_ids, project_id, priority)

            # Send email to notify about the changes
            if old_state == 'closed' and not new_state:
                # If a ticket is already closed,
                # we don't need to send mail notification
                has_tracked_changes = False
            else:
                has_tracked_changes = self.record_changes(
                    self, [old_ticket.id], ticket_vals, old_ticket,
                    self.tracked_fields, 'tms_support_ticket_id')

            if doc_status == 'not_required':
                ticket_vals['documentation_required'] = False
            else:
                ticket_vals['documentation_required'] = True

            # Update Subscriber for support ticket
            old_subscriber_ids = \
                [s.name.id for s in old_ticket.support_ticket_subscriber_ids]
            context.update({'subscriber_from_support_ticket': True})

            # update urgent date
            if priority == 'very_high' and old_ticket.priority != 'very_high':
                ticket_vals.update({'urgent_changed_date': datetime.now()})
            elif old_ticket.priority == 'very_high' and \
                    owner_id != old_ticket.owner_id.id:
                ticket_vals.update({'urgent_changed_date': datetime.now()})

            ticket_vals = old_ticket.with_context(
                context).get_vals_ticket_subcribers(
                project, owner_id or old_ticket.owner_id.id,
                ticket_vals, old_subscriber_ids)
            old_forge = old_ticket.tms_forge_ticket_id or None
            super(TmsSupportTicket, old_ticket.with_context(context)
                  ).write(ticket_vals)
            # F#17388
            # When setting the field `forge ticket` on a support
            # ticket, automatically set the field `support ticket`
            # of the forge ticket
            new_forge = old_ticket.tms_forge_ticket_id or None
            if 'tms_forge_ticket_id' in vals:
                # If exist old forge ticket
                if old_forge:
                    # Remove support from old forge ticket's working hour
                    old_forge.sudo().tms_working_hour_ids.write({
                        'tms_support_ticket_id': None,
                    })
                    # remove support ticket on old forge ticket
                    old_forge.tms_support_ticket_id = None
                # If new forge ticket is set
                if new_forge:
                    # Set support ticket on new forge ticket
                    support_of_new_forge = new_forge.tms_support_ticket_id
                    if not support_of_new_forge or \
                            support_of_new_forge.id == old_ticket.id:
                        new_forge.tms_support_ticket_id = old_ticket
                        # F_27306: link all working hours of new forge ticket
                        # to support ticket
                        new_forge.tms_working_hour_ids and \
                            new_forge.tms_working_hour_ids.sudo().write(
                                {'tms_support_ticket_id': old_ticket.id})

            # Send the Notification Support Email
            if has_tracked_changes or \
                    'tms_support_ticket_comment_ids' in ticket_vals:
                context.update({'field_change': ticket_vals.keys()})

                # If a ticket is already closed,
                # we don't need to send mail notification
                # or if the update of the support ticket is from an auto test.
                if not project.mute_mail_noti and \
                        not context.get('test_support_ticket'):
                    template = self.env.ref('tms_modules.tms_support_'
                                            'notification_email_html_template')
                    template.with_context(context)._send_mail_asynchronous(
                        old_ticket.id)
        self.check_sent_comment('tms_support_ticket_comment_ids')
        return True

    def update_progress_date(self, new_state):
        dict_val = {'closing_datetime': False, 'resolution': False}
        if new_state == 'delivered':
            dict_val.update({'staging_delivery_date': str(datetime.now())})
        elif new_state == 'ok_for_production':
            dict_val.update({'ok_production_date': str(datetime.now())})
        return dict_val

    def check_support_ticket_type(self, final_state, final_ticket_type):
        if final_state in ['planned_for_delivery', 'delivered',
                           'ok_for_production'] and \
                final_ticket_type == 'unclassified':
            raise Warning(
                'Forbidden action!',
                'Please set ticket type to a different type \
                    than Unclassified.')

    @api.model
    def check_info_when_closing_ticket(self, closing_datetime, resolution,
                                       ticket_type, forge_ticket_id,
                                       old_forge_ticket, func_block_id):
        # Resolution field must be set when closing a support ticket
        if not resolution and not getattr(self, 'resolution', False):
            raise Warning(
                'Forbidden action!',
                'Please, update the field resolution in the tab \
                    "Tracking Info" before closing the ticket!')
        # The ticket {ticket id} cannot be closed with the Type
        # "Unclassified"
        if ticket_type == 'unclassified' or self.ticket_type == 'unclassified':
            raise Warning(
                'Forbidden action!', 'The ticket {%s} cannot be closed with '
                'the Type "Unclassified"' % self.name)

        if forge_ticket_id:
            forge_ticket = self.env['tms.forge.ticket'].browse(forge_ticket_id)
        elif old_forge_ticket:
            forge_ticket = old_forge_ticket
        else:
            forge_ticket = False

        # The ticket cannot be closed because the related forge ticket is
        # not closed
        if forge_ticket and forge_ticket.state != 'closed':
            raise Warning(
                'Forbidden action!',
                'The ticket {%s} cannot be closed because '
                'the related forge ticket is not closed' % self.name)

        # The ticket cannot be closed because functional block is not set.
        if not func_block_id and not self.tms_functional_block_id:
            raise Warning(
                'Forbidden action!',
                'The ticket {%s} cannot be closed because '
                'functional block is not set' % self.name)

        # Update closing date when closing ticket.
        if not self.closing_datetime or not closing_datetime:
            return {'closing_datetime': str(datetime.now())}
        return {}

    @api.model
    def update_value_for_related_forge_ticket(
            self, forge_ticket_id, activity_id, milestone_id, func_block_id,
            tag_ids, project_id, priority):
        forge_env = self.env['tms.forge.ticket']
        context = self._context and self._context.copy() or {}
        forge_vals = {}
        if activity_id and \
                not context.get('update_activity_from_forge', False):
            context.update({'update_activity_from_support': 1})
            forge_vals.update({'tms_activity_id': activity_id})
        if milestone_id is not None and not context.get(
                'update_milestone_from_forge', False):
            context.update({'update_milestone_from_support': 1})
            forge_vals.update({'milestone_id': milestone_id})

        if func_block_id and not context.get(
                'update_functional_block_from_forge', False):
            context.update({'update_functional_block_from_support': 1})
            forge_vals.update({
                'tms_functional_block_id': func_block_id})

        if tag_ids and not context.get(
                'update_project_tag_from_forge', False):
            context.update({'update_project_tag_from_support': 1})
            forge_vals.update({'tms_project_tag_ids': [(6, 0, tag_ids)]})

        if project_id and not context.get(
                'update_project_from_forge', False):
            context.update({'update_project_from_support': 1})
            forge_vals.update({'project_id': project_id})

        # Update priority to related forge ticket
        if priority:
            forge_priority = self.dict_priority_mapping.get(priority)
            if forge_priority:
                forge_vals.update({'priority': forge_priority})

        if forge_vals:
            # Update support ticket => auto update forge ticket
            # PROBLEM: customer has no access on Forge ticket,
            # it will meet a error if use the customer user
            # for auto changes from support to forge ticket
            # SOLUTION: Use supperuser write the changes
            # When create a forge ticket comment,
            # change author of the comment to the user
            # who made the changes in forge ticket comment
            context.update({'support_change_uid': self._uid})
            forge_env.sudo().with_context(
                context).browse(forge_ticket_id).write(forge_vals)

    @api.multi
    def button_planned_for_delivery(self):
        self.write({'state': 'planned_for_delivery'})

    @api.multi
    def button_delivered_in_staging(self):
        self.write({'state': 'delivered'})

    @api.multi
    def button_assign_to_trobz(self):
        ticket = self[0]
        default_trobz_supporter_for_project = \
            ticket.project_id.default_supporter_id and \
            ticket.project_id.default_supporter_id.id or False
        manage_deadline_on_project = \
            ticket.project_id.manage_dealine_on_sp_tickets
        if manage_deadline_on_project:
            ctx = dict(self._context or {})
            ctx.update({
                'default_trobz_supporter_for_project':
                default_trobz_supporter_for_project})
            view_id = self.env.ref(
                'tms_modules.view_manage_deadline_sp_ticket_wizard_form').id
            return {
                'name': _('Assign To Trobz'),
                'type': 'ir.actions.act_window',
                'target': 'new',
                'view_id': view_id,
                'view_mode': 'form',
                'res_model': 'manage.deadline.sp.ticket.wizard',
                'context': ctx
            }
        if default_trobz_supporter_for_project:
            return ticket.write(
                {'owner_id': default_trobz_supporter_for_project,
                 'state': 'assigned'})
        else:
            users_pool = self.env['res.users']
            data_pool = self.env['ir.model.data']
            user_login = data_pool.get_object(
                "tms_modules", "trobz_default_project_supporter_login"
            ).value
            users = users_pool.search(
                [('login', '=', user_login)]
            )
            if users:
                return ticket.write(
                    {'owner_id': users[0].id,
                     'state': 'assigned'})
            raise Warning(
                "Warning!",
                "No default project supporter configuration found on system"
            )

    @api.multi
    def button_ok_for_production(self):
        ticket = self[0]
        trobz_account_manager_id = self._get_account_manager_id(
            ticket.project_id)
        return ticket.write(
            {'owner_id': trobz_account_manager_id,
             'state': 'ok_for_production'
             })

    @api.multi
    def button_assign_to_reporter(self):
        ticket = self[0]
        return ticket.write(
            {'state': 'assigned',
             'owner_id': ticket.reporter_id.id
             })

    @api.multi
    def button_close(self):
        return self.write({'state': 'closed'})

    @api.multi
    def button_create_forge_ticket(self):
        milestone_env = self.env['tms.milestone']
        forge_env = self.env['tms.forge.ticket']
        ticket = self[0]
        if not ticket.tms_activity_id:
            raise Warning(
                'Forbidden action!',
                'You cannot create a Forge Ticket because you did not '
                'specify the Activity (tab Tracking Info).'
            )

        if ticket.tms_forge_ticket_id:
            raise Warning(
                'Forbidden action!',
                'This support ticket is already associated to a forge ticket.'
            )

        vals = {}
        project = ticket.project_id
        if ticket.ticket_type == 'unclassified':
            prefix = '[Unclassified, need investigation to recommend Support \
            type and next action] '
            vals['summary'] = prefix + ticket.summary or False
        else:
            vals['summary'] = ticket.summary or False
        vals['description'] = ticket.description or False
        vals['project_id'] = project.id
        vals['reporter_id'] = ticket.reporter_id and \
            ticket.reporter_id.id or False
        vals['tms_activity_id'] = ticket.tms_activity_id and \
            ticket.tms_activity_id.id or False
        vals['tms_functional_block_id'] = ticket.tms_functional_block_id and \
            ticket.tms_functional_block_id.id or False
        vals['tms_project_tag_ids'] = [(6, 0, ticket.tms_project_tag_ids.ids)]
        vals['tms_support_ticket_id'] = ticket.id
        milestones = milestone_env.search(
            [('project_id', '=', project.id),
             ('state', 'in', milestone_env.milestone_open_status)]
        )
        vals['milestone_id'] = milestones and milestones[0].id or False

        priority_mapping = {'urgent': 'very_high', 'major': 'high',
                            'normal': 'normal', 'minor': 'low'}
        vals['priority'] = priority_mapping[ticket.priority]
        vals['owner_id'] = project.technical_project_manager_id.id

        # Create forge ticket, set activity from support ticket
        vals['tms_activity_id'] = ticket.tms_activity_id \
            and ticket.tms_activity_id.id or False
        forge_ticket = forge_env.create(vals)
        return ticket.write({'tms_forge_ticket_id': forge_ticket.id})

    tracked_fields = [
        'invc_by_trobz_vn',
        'tms_activity_id',
        'summary',
        'description',
        'reporter_id',
        'milestone_id',
        'state',
        'priority',
        'workload',
        'owner_id',
        'ticket_type',
        'resolution',
        'quotation_approved',
        'tms_project_tag_ids',
        'tms_functional_block_id',
        'documentation_required',
        'documentation_status',
        'documentation_links',
        'deadline',
    ]

    @api.multi
    def copy(self, default=None):
        raise Warning(
            _('Error'), _('You cannot duplicate a support ticket.')
        )

    @api.multi
    def get_ticket_url(self):
        res = ''

        # Get object pool reference
        config_env = self.env['ir.config_parameter']
        action_env = self.env['ir.actions.act_window']

        # Get the base url of current instance
        default_conf = 'https://tms.trobz.com'
        conf_val = config_env.get_param(
            'web.base.url', default=default_conf
        )
        if not conf_val:
            conf_val = default_conf

        # Check if we are on production, because we usually use `tms.trobz.com`
        # domain to access system a bit hardcoded but no way else to do
        base_url = conf_val + '/web?db=%s' % self._cr.dbname

        # Find the default action of menu Support Tickets
        # (Support > Support Tickets > Support Tickets)
        act_window = action_env.for_xml_id(
            'tms_modules', 'action_view_tms_support_ticket_open'
        )

        # Compose list of ticket access urls
        for ticket_id in self._ids:
            res += '{0}#id={1}&view_type=form&model=tms.support.ticket' \
                   '&action={2}'.format(base_url, ticket_id,
                                        act_window.get("id"))
        return res

    @api.multi
    def get_html_description(self):
        return self.env['tms.ticket'].get_html_description(
            self.ids, 'tms.support.ticket')

    @api.multi
    def get_last_changes(self):
        return self.env['tms.ticket'].get_last_changes(
            self.ids, 'tms.support.ticket', 'tms_support_ticket_comment_ids')

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
        customize search for quotation aprroved in format selection yes/no
        because it's currently boolean field
        """
        args = self.change_quotation_condition(args)
        args = self.search_subscriber_on_ticket('support_id', args)
        deliver_this_week = self._context.get('deliver_this_week', False)
        deadline_in_this_week = self._context.get(
            'deadline_in_this_week', False)
        if deliver_this_week:
            start_date, end_date = self.week_range(datetime.now())
            args.append(['milestone_date', '>=',
                         start_date.strftime('%Y-%m-%d')])
            args.append(['milestone_date', '<=',
                         end_date.strftime('%Y-%m-%d')])
        if deadline_in_this_week:
            args.append(['id', 'in', self.filter_deadline_in_this_week()])
        return super(TmsSupportTicket, self).search(
            args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def filter_deadline_in_this_week(self):
        sql_duration = """
            SELECT sp.id
            FROM tms_support_ticket sp where deadline is not null
        """
        self._cr.execute(sql_duration)
        results = self._cr.fetchall()
        sp_ids = []
        lst_sp_ids = []
        for result in results:
            sp_ids.append(result[0])
        if sp_ids:
            records = self.env['tms.support.ticket'].browse(sp_ids)
            for record in records:
                temp_deadline = datetime.strptime(record.deadline, '%Y-%m-%d')
                week_deadline = temp_deadline.isocalendar()[1]
                week_current = datetime.now().isocalendar()[1]
                if week_deadline == week_current and record.state in \
                        ['new', 'assigned', 'planned_for_delivery']:
                    lst_sp_ids.append(record.id)
        return lst_sp_ids

    # FIXME: issue with lazy argument using old API
    # def read_group(self, cr, uid, domain, fields, groupby, offset=0,
    #                limit=None, context=None, orderby=False):
    #     if context is None:
    #         context = {}
    #     domain = self.change_quotation_condition(domain)
    #
    #     result = super(tms_support_ticket, self).read_group(
    #         cr, uid, domain=domain, fields=fields, groupby=groupby,
    #         offset=offset, limit=limit, orderby=orderby, context=context
    #     )
    #
    # ======================================
    # handle sort "group by" priority (6108)
    # ======================================
    # TODO:
    # perhaps it's expensive to order the group by
    # like this way, should considered to do in better way
    #     if result and result[0].get("priority"):
    #         target_list = []
    # temporary convert dict to list and sort with
    # addition number at the beginning of the list
    #         for item in result:
    #             converted_list = list(item.iteritems())
    #
    #             if item.get("priority") == "urgent":
    #                 target_list.append([4] + converted_list)
    #
    #             elif item.get("priority") == "major":
    #                 target_list.append([3] + converted_list)
    #
    #             elif item.get("priority") == "normal":
    #                 target_list.append([2] + converted_list)
    #
    #             elif item.get("priority") == "minor":
    #                 target_list.append([1] + converted_list)
    #
    # Sort the list
    #         target_list = sorted(target_list, reverse=True)
    #
    # Switch back to list and remove the first intended sort number
    #         if target_list:
    #             result = [dict(item[1:]) for item in target_list]
    #
    #     return result

    def change_quotation_condition(self, args):
        select_quotation = [
            arg for arg in args if arg[0] == 'select_quotation'
        ]
        if select_quotation and len(select_quotation) == 1:
            args.remove(select_quotation[0])
            select_quotation[0][0] = 'quotation_approved'
            select_quotation[0][2] = select_quotation[0][2] == \
                'yes' and True or False
            args.append(select_quotation[0])
        return args

    @api.multi
    def get_state_value_from_key(self):
        info = self[0]
        for state in self.list_states:
            if info.state == state[0]:
                return state[1]

    @api.multi
    def get_priority_value_from_key(self):
        info = self[0]
        for priority in self.list_priority:
            if info.priority == priority[0]:
                return priority[1]

    @api.multi
    def get_ticket_type_value_from_key(self):
        info = self[0]
        for ticket_type in self.list_ticket_type:
            if info.ticket_type == ticket_type[0]:
                return ticket_type[1]

    @api.multi
    def button_launch_in_forge(self):
        support_ticket = self[0]
        support_project = support_ticket.project_id

        # F#11707
        # if the current user is not TPM of the project and
        # and not in supporters of project
        supporter_ids = support_project.project_supporter_rel_ids \
            and support_project.project_supporter_rel_ids.ids or []
        user = self.env.user
        if user.group_profile_id.name != 'Admin Profile' and \
                self._uid not in supporter_ids:
            raise Warning(
                _('Warning'),
                _("Only Admin users or supporters of this project"
                  " can use this button.")
            )

        # if support ticket quotation is not approved
        if not support_ticket.quotation_approved:
            raise Warning(
                _('Warning'),
                _("You cannot Launch in Forge \
                    if you don't check the box Quotation Approved.")
            )

        # if Workload is 0
        if not support_ticket.workload_char or \
                not float(support_ticket.workload_char) > 0:
            raise Warning(
                _("Warning"),
                _("You cannot Launch in Forge \
                    if the Workload is 0.")
            )

        # if ticket type of support ticket is not evolution
        if support_ticket.ticket_type != 'evolution':
            raise Warning(
                _("Warning"),
                _("You cannot use this button \
                    if the Ticket Type is not Evolution.")
            )

        # if ticket links to an activity
        if not support_ticket.tms_activity_id:
            raise Warning(
                _("Warning"),
                _("You cannot create a Forge Ticket because you did"
                  " not specify the Activity (tab Tracking Info).")
            )

        # if this evolution support ticket have no forge ticket associated
        if not support_ticket.tms_forge_ticket_id:
            support_ticket.button_create_forge_ticket()
        else:
            forge_ticket = support_ticket.tms_forge_ticket_id
            # modify write value
            summary = forge_ticket.summary \
                if not forge_ticket.summary.startswith('[Quotation sent]') \
                else forge_ticket.summary.replace('[Quotation sent]', ''
                                                  ).strip()
            forge_vals = {
                'quotation': 'no',
                'summary': summary
            }
            # update forge ticket
            forge_ticket.write(forge_vals)

    @api.model
    def is_project_missing_reactivity(self, project_id):
        """
            Indicates a project is missing reactivity
                or not based on the nearest activities,
            if no action (comment) performed
                within a day for all support tickets of the project,
                the project is identified as missing reactivity.
        """
        current_time = datetime.now().strftime(DF)
        past24hours = (datetime.now() - timedelta(days=1)).strftime(DF)
        sql_command = """
            SELECT MAX(ttc.create_date) FROM tms_support_ticket tst
            JOIN tms_ticket_comment ttc ON tst.id = ttc.tms_support_ticket_id
            JOIN res_users ru ON ru.id = ttc.author_id
            WHERE ru.is_trobz_member = True
            GROUP BY tst.project_id HAVING tst.project_id = {0};
        """.format(project_id)
        self._cr.execute(sql_command)
        result = self._cr.fetchone()
        if result:
            return not past24hours <= result[0] <= current_time
        return True

    @api.model
    def get_target_tickets_ready_for_staging(self):
        return self.env['email.template'].get_target_description(
            'Minimum tickets ready for staging')

    @api.model
    def is_project_ready_for_staging(self, project_id):

        # get total tickets that belong to the project
        # which is ready for staging
        tickets_ready_for_stagings = self.search(
            [('state', '!=', 'closed'),
             ('priority', '!=', 'minor'),
             ('owner_id.is_trobz_member', '=', True),
             ('delivery_status', '=', 'ready_for_staging'),
             ('tms_forge_ticket_id', '!=', False),
             ('project_id', '=', project_id)])
        tickets_ready_for_staging_ids = len(tickets_ready_for_stagings.ids) \
            if tickets_ready_for_stagings else []

        target = int(self.get_target_tickets_ready_for_staging())
        return tickets_ready_for_staging_ids > target

    @api.model
    def run_identify_support_tickets_missing_reactivity(self):
        """
            Scheduler method used to check support ticket scope
                and project scope for missing reactivities:
            There are six cases for missing reactivity and followed on
                order to make sure one support ticket
            is not fallen into more than one case at the same time.
                (one support ticket per case)

            order to perform check:
            (skip check for support ticket in low priority)

            1./ Unclassified support ticket owned by trobz
                => should perform ticket classification action

            2./ Defect support ticket does not have forge ticket assocciated
                => create forge ticket to handle defect

            3./ Urgent support ticket owned by trobz more than one day
                => feedback to customer within 24 hours

            4./ Five more tickets of project ready for staging
                => remind deploy tickets in staging.

            5./ Not low support ticket owned by trobz more than 20 days
                => trobz is holding these ticket too long.

            6./ Project is missing reactivity (within 24 hours)
                => require activity from trobz (comment or something)

            7./ Support ticket late response (within 24 hours)
                => If a ticket is created by a non-Trobz member (customer):
                last response should always come from a Trobz member.
                If a ticket is a created by a Trobz member (internal issue):
                last response should always come from the "assignee".

        """
        # always run scheduler with highest permission (admin)
        #         uid = SUPERUSER_ID
        logging.warn('===========BEGIN CHECK MISSING REACTIVITY ============')
        # ---------------------------------------------------------------#
        # TODO: CHECK MISSING REACTIVITY FOR SUPPORT TICKETS             #
        # IN THE ABOVE CASES LISTED                                      #
        # ---------------------------------------------------------------#
        # only take care of support tickets which have current
        # owner is trobz, project is active and not in low priority
        support_tickets_objs = self.search(
            [('owner_id.is_trobz_member', '=', True),
             ('state', '!=', 'closed'),
             ('priority', '!=', 'minor'),
             ('project_id.state', '=', 'active')])

        # contains project id and flag to check
        # whether project is ready for staging or not
        ready_for_staging_projects = {}
        # contains project id and a flag to check
        # whether project missing reactivity or not
        missing_reactivity_projects = {}
        # unclassified tickets owned by trobz member more than one day
        support_ticket_unclassified_ids = []
        # defect ticket has no forge ticket associated to handle defect
        support_ticket_defect_no_forge_ids = []
        # urgent tickets owned by trobz for more than one day
        support_ticket_urgent_more_than_one_day_ids = []
        # five more tickets 'Ready For Staging' (project scope)
        support_ticket_project_ready_for_staging_ids = []
        # not low priority tickets owned by trobz over 20 days
        support_ticket_not_low_priority_over_20_days_ids = []
        # tickets is missing activity within 24 hours (project scope)
        support_ticket_project_missing_reactivity_ids = []
        # revert tickets previously marked as missing
        # support_ticket_old_case_right_but_now_wrong_recs = False

        # check a list of support tickets for missing reactivity by order
        for support_ticket in support_tickets_objs:

            # get project id for checking with project scope
            project_id = support_ticket.project_id.id

            # get ownership duration to check
            ownership_duration = int(support_ticket.ownership_duration)

            # 1./ unclassified owned by trobz for more than 1 day
            if support_ticket.ticket_type == "unclassified" \
                    and ownership_duration > 1:
                support_ticket_unclassified_ids.append(support_ticket.id)
                continue

            # 2./ defect support have no forge ticket
            if support_ticket.ticket_type == "defect" \
                    and not support_ticket.tms_forge_ticket_id:
                support_ticket_defect_no_forge_ids.append(
                    support_ticket.id)
                continue

            # 3./ urgent tickets own more than one day
            if support_ticket.priority == "urgent" \
                    and ownership_duration > 1:
                support_ticket_urgent_more_than_one_day_ids.append(
                    support_ticket.id
                )
                continue

            # 4./ five more tickets in project ready for staging
            if support_ticket.delivery_status == "ready_for_staging" \
                    and support_ticket.tms_forge_ticket_id:

                if project_id not in ready_for_staging_projects:
                    ready_for_staging_projects[
                        project_id] = self.is_project_ready_for_staging(
                        project_id
                    )

                if ready_for_staging_projects[project_id]:
                    support_ticket_project_ready_for_staging_ids.append(
                        support_ticket.id
                    )
                    continue

            # 5./ not low ticket own more than 20 days
            # (low is filtered above in search function)
            if int(support_ticket.ownership_duration) > 20:
                support_ticket_not_low_priority_over_20_days_ids.append(
                    support_ticket.id
                )
                continue

            # 6./ missing reactivity project
            if datetime.now().strftime('%A') not in ['Sunday', 'Monday']:

                if project_id not in missing_reactivity_projects:
                    missing_reactivity_projects[
                        project_id] = self.is_project_missing_reactivity(
                        project_id
                    )

                if missing_reactivity_projects[project_id]:
                    support_ticket_project_missing_reactivity_ids.append(
                        support_ticket.id
                    )
                    continue

        # --------------------------------------------------------------------#
        # TODO: REVERT STATE OF SUPPORT TICKETS                               #
        #     INCASE OF ONE OF PROJECT'S TICKETS IS NOT MISSING REACTIVITY    #
        # --------------------------------------------------------------------#

        support_ticket_old_case_right_but_now_wrong_recs = self.search(
            [
             ('missing_reactivity', '=', True),
             ('id', 'not in', support_ticket_unclassified_ids),
             ('id', 'not in', support_ticket_defect_no_forge_ids),
             ('id', 'not in', support_ticket_urgent_more_than_one_day_ids),
             ('id', 'not in', support_ticket_project_ready_for_staging_ids),
             ('id', 'not in',
              support_ticket_not_low_priority_over_20_days_ids),
             ('id', 'not in', support_ticket_project_missing_reactivity_ids)]
        )

        # ------------------------------------------------------------------#
        # TODO:                PERFORM ONE-TIME WRITE                       #
        # ------------------------------------------------------------------#

        if support_ticket_unclassified_ids:
            tickets = self.browse(support_ticket_unclassified_ids)
            super(TmsSupportTicket, tickets).write(
                {'missing_reactivity': True,
                 'missing_reactivity_reason': 'unclassified'},
            )

        if support_ticket_defect_no_forge_ids:
            tickets = self.browse(support_ticket_defect_no_forge_ids)
            super(TmsSupportTicket, tickets).write(
                {'missing_reactivity': True,
                 'missing_reactivity_reason': 'defect_wo_forge'},
            )

        if support_ticket_urgent_more_than_one_day_ids:
            tickets = self.browse(support_ticket_urgent_more_than_one_day_ids)
            super(TmsSupportTicket, tickets).write(
                {'missing_reactivity': True,
                 'missing_reactivity_reason': 'urgent_over_day'},
            )

        if support_ticket_project_ready_for_staging_ids:
            tickets = self.browse(support_ticket_project_ready_for_staging_ids)
            super(TmsSupportTicket, tickets).write(
                {'missing_reactivity': True,
                 'missing_reactivity_reason': 'deploy_in_staging'},
            )

        if support_ticket_not_low_priority_over_20_days_ids:
            tickets = self.browse(
                support_ticket_not_low_priority_over_20_days_ids)
            super(TmsSupportTicket, tickets).write(
                {'missing_reactivity': True,
                 'missing_reactivity_reason': 'not_low_over_20_day'},
            )

        if support_ticket_project_missing_reactivity_ids:
            tickets = self.browse(
                support_ticket_project_missing_reactivity_ids)
            super(TmsSupportTicket, tickets).write(
                {'missing_reactivity': True,
                 'missing_reactivity_reason': 'project_missing_reactivy'},
            )

        if support_ticket_old_case_right_but_now_wrong_recs:
            super(TmsSupportTicket,
                  support_ticket_old_case_right_but_now_wrong_recs).write(
                {'missing_reactivity': False,
                 'missing_reactivity_reason': False})

        # 7. late response
        # hanlder support ticket which is not in these support ticket above
        # and support ticket which author is customer
        sp_ticket_to_check_late_response_ids = self._search([
            ('id', 'not in', support_ticket_unclassified_ids),
            ('id', 'not in', support_ticket_defect_no_forge_ids),
            ('id', 'not in', support_ticket_urgent_more_than_one_day_ids),
            ('id', 'not in', support_ticket_project_ready_for_staging_ids),
            ('id', 'not in', support_ticket_not_low_priority_over_20_days_ids),
            ('id', 'not in', support_ticket_project_missing_reactivity_ids)
        ])
        self.handler_support_ticket_late_response(
            sp_ticket_to_check_late_response_ids)

        logging.warn('==============END CHECK MISSING REACTIVITY ============')
        return True

    @api.model
    def run_calculate_ownership_date(self):
        """
            auto calculate ownership durration and total ownership duration
                for each support ticket
        """
        sql_duration = """
            UPDATE tms_support_ticket
            SET ownership_duration = EXTRACT(DAY FROM now() - ownership_date);
        """
        self._cr.execute(sql_duration)

        return self._cr.rowcount > 0

    @api.model
    def run_calculate_trobz_ownership_total_time(self):
        """
            auto calculate trobz ownership total time for each support ticket
        """
        sql_duration = """
            UPDATE tms_support_ticket
            SET trobz_ownership_total_time = CAST(
                (CAST(trobz_ownership_total_time AS INT) + 1) AS CHAR)
            WHERE state != 'closed'
            AND (SELECT is_trobz_member
                    FROM res_users
                    WHERE res_users.id = tms_support_ticket.owner_id) = true;
        """
        self._cr.execute(sql_duration)

        return self._cr.rowcount > 0

    @api.multi
    def button_previous_milestone(self):
        ctx = self._context and self._context.copy() or {}
        ctx["next_milestone"] = False
        return self.env['tms.forge.ticket'].with_context(ctx). \
            move_milestone(self.ids, 'tms.support.ticket')

    @api.multi
    def button_next_milestone(self):
        ctx = self._context and self._context.copy() or {}
        ctx["next_milestone"] = True
        return self.env['tms.forge.ticket']. \
            with_context(ctx).move_milestone(self.ids, 'tms.support.ticket')

    @api.multi
    def button_remove_milestone(self):
        return self.env['tms.forge.ticket']. \
            remove_milestone(self.ids, 'tms.support.ticket')

    @api.model
    def function_remove_sequence_tms_support_ticket(self):
        _logger.info('====START Remove sequence for tms support ticket ====')
        ir_sequence_env = self.env['ir.sequence']
        ir_sequence_type_env = self.env['ir.sequence.type']
        tms_support_ticket_sequences = ir_sequence_env.search(
            [('code', '=', 'tms.support.ticket.code')])
        tms_support_ticket_sequence_types = ir_sequence_type_env.search(
            [('code', '=', 'tms.support.ticket.code')])
        if tms_support_ticket_sequences:
            tms_support_ticket_sequences.unlink()
            tms_support_ticket_sequence_types.unlink()
        _logger.info('====START Remove sequence for tms support ticket ====')
        return True

    @api.multi
    def button_subscribe(self):
        """
        Button Subscribe Me on support ticket
        Add current user into the ticket subscriber
        """
        ticket_env = self.env['tms.ticket']
        return ticket_env.button_subscribe(
            self, 'support_ticket_subscriber_ids')

    @api.multi
    def button_unsubscribe(self):
        """
        Button Unsubscribe Me on support ticket
        remove current user from the ticket subscribers
        """
        for support_ticket in self:
            subscribers = support_ticket.support_ticket_subscriber_ids
            subscribed_vals = [(2, s.id) for s in subscribers
                               if s.name.id == self._uid]
            # only remove the reference if user is already linked
            if subscribed_vals:
                support_ticket.write({
                    "support_ticket_subscriber_ids": subscribed_vals
                })
        return True

    @api.onchange('tms_activity_id')
    def on_change_activity(self):
        # Technical note:
        # if the field invoiceable is set to False on the activity,
        # the default value must be False (not the value of the field
        # invc_by_trobz_vn from the project)
        if self.tms_activity_id:
            self.invc_by_trobz_vn = self.tms_activity_id.invoiceable
        else:
            self.invc_by_trobz_vn = self.project_id.invc_by_trobz_vn

    @api.onchange('project_id')
    def on_change_project(self):
        project = self.project_id
        self.manage_documentation = project.manage_documentation or False
        self.additional_subscribers = project.additional_subscribers or False
        self.customer_id = project.partner_id and \
            project.partner_id.id or False
        self.owner_id = project.default_assignee_id and \
            project.default_assignee_id.id or False
        self.tms_activity_id = project.default_activity_id and \
            project.default_activity_id.id or False
        self.milestone_id = False
        self.tms_activity_id = False

    @api.model
    def read_group(self, domain, fields, groupby, offset=0,
                   limit=None, orderby=False, lazy=False):
        domain = self.search_subscriber_on_ticket('support_id', domain)
        if 'name' in fields:
            del fields[fields.index('name')]
        domain = self.change_quotation_condition(domain)

        deliver_this_week = self._context.get('deliver_this_week', False)
        if deliver_this_week:
            start_date, end_date = self.week_range(datetime.now())
            domain.append(['milestone_date', '>=',
                           start_date.strftime('%Y-%m-%d')])
            domain.append(['milestone_date', '<=',
                           end_date.strftime('%Y-%m-%d')])

        return super(TmsSupportTicket, self).read_group(
            domain=domain, fields=fields, groupby=groupby,
            offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    @api.model
    def week_range(self, date):
        """Find the first/last day of the week for the given day.
        Assuming weeks start on Sunday and end on Saturday.

        Returns 2 dates ``start_date, end_date``.

        """
        # isocalendar calculates the year, week of the year,
        # and day of the week.
        # dow is Mon = 1, Sat = 6, Sun = 7
        _year, _week, dow = date.isocalendar()

        # Find the first day of the week.
        if dow == 7:
            # Since we want to start with Sunday,
            # let's test for that condition.
            start_date = date
        else:
            # Otherwise, subtract `dow` number days to get the first day
            start_date = date - timedelta(dow)

        # Now, add 6 for the last day of the week (i.e., count up to Saturday)
        end_date = start_date + timedelta(6)
        return start_date, end_date

    @api.multi
    def button_ok_to_close(self):

        ticket = self[0]
        default_project_supporter = \
            ticket.project_id.default_supporter_id and \
            ticket.project_id.default_supporter_id.id or False
        if not default_project_supporter:
            users_env = self.env['res.users']
            data_env = self.env['ir.model.data']

            user_login = data_env.get_object(
                "tms_modules", "trobz_default_project_supporter_login").value
            users = users_env.search([('login', '=', user_login)])
            default_project_supporter = users and users[0] and \
                users[0].id or False

            if not default_project_supporter:
                raise Warning(
                    "Warning!",
                    "This ticket will be reassigned to Default " +
                    "Project Supporter. But no Default Project Supporter " +
                    "found in system!")

        return ticket.write({'state': 'ok_to_close',
                             'owner_id': default_project_supporter})

    # =========================================================
    # EMAIL FOR TMS SUPPORT TICKET
    # =========================================================
    KEY_FIGURE_MESSAGE = '<div style="font-size:11px;font-style:italic;' + \
                         'margin-left:30px" title="%s">%s</div>'
    KEY_FIGURE_TARGET = '<span style="font-size:14px;' + \
                        'color:black;"><b>%s<b></span></div>'

    @api.model
    def get_new_support_ticket_in_past_24h(self):
        # get new support tickets in past 24 hours
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        ticket_ids = self.search_count(
            [
                ('create_date', '>=', str(yesterday)),
                ('create_date',
                 '<=', str(today)),
                ('project_id.state',
                 '=', 'active'),
                ('project_id.is_support_contract',
                 '=', True)
            ])
        return ticket_ids

    @api.model
    def get_support_ticket_closed_in_past_24h(self):
        # get support tickets closed in past 24 hours
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        ticket_ids = self.search_count(
            [
                ('state', '=', 'closed'),
                ('closing_datetime', '>=', str(yesterday)),
                ('closing_datetime', '<=', str(today)),
                ('project_id.state', '=', 'active'),
                ('project_id.is_support_contract', '=', True)
            ])
        return ticket_ids

    @api.model
    def get_urgent_support_tickets(self):
        # get very high support tickets
        if self.check_urgent_tickets():
            return self.get_urgent_tickets()
        return 'No ticket'

    @api.model
    def get_target_number_of_support_ticket_trobz(self):
        return self.env['email.template']. \
            get_target_value('Support tickets assigned to trobz')

    @api.model
    def get_number_of_support_ticket_trobz(self):
        state_list = ('ok_for_production', 'closed')
        support_domain = [
            '|', ('analytic_secondaxis_id.code', '=', 'support'),
            ('tms_activity_id', '=', False),
            ('state', 'not in', state_list),
            ('priority', '!=', 'minor'),
            ('owner_id.is_trobz_member', '=', True),
            ('project_id.state', '=', 'active'),
            ('project_id.is_support_contract', '=', True),

        ]
        number_of_support_ticket = \
            len(self.search(support_domain))
        target_number = self.get_target_number_of_support_ticket_trobz()
        target_description = self.env['email.template']. \
            get_target_description('Support tickets assigned to trobz')
        result = r''
        target_number_string = ''
        if target_number > 0:
            result += \
                self.env['email.template'].render_colored_key_figure(
                    number_of_support_ticket < target_number,
                    number_of_support_ticket)
        else:
            target_number_string = 'Missing or misconfigured target'
            result = self.env['email.template']. \
                render_default_colored_key_figure(number_of_support_ticket)
        result += self.KEY_FIGURE_TARGET % (
            ' support tickets to Trobz (not low, for support activities'
            ' or without activity, active project with support contract,'
            ' not "Ok for production")')
        if target_number > 0:
            result += self.KEY_FIGURE_MESSAGE % \
                (target_description, 'target: less than %s' %
                 str(int(math.floor(target_number))))
        else:
            result += self.KEY_FIGURE_MESSAGE % \
                (target_description, target_number_string)
        return result

    @api.model
    def get_support_indicators(self, domain_filter):

        support_tickets = self.search(domain_filter)
        total_workload = remaining = work_achive = progress = 0

        total_workload = sum(map(
            float, support_tickets.mapped('workload_char')))
        # All support tickets which
        # has related forge ticket is already implemented
        tiket_objs_done = support_tickets.filtered(
            lambda t: t.state not in ['new', 'assigned'])
        work_achive = sum(map(float, tiket_objs_done.mapped('workload_char')))
        remaining = total_workload - work_achive
        if remaining < 0:
            remaining = 0

        if total_workload > 0:
            progress = float(work_achive * 100) / total_workload
        return {'planned': total_workload, 'work_achive': work_achive,
                'remaining': remaining, 'progress': progress}

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

        if self.tms_support_ticket_comment_ids:
            comments = tms_ticket_comment_env.search(
                [('tms_support_ticket_id', '=', self.id)],
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
    def handler_support_ticket_late_response(self, sp_ticket_ids):
        """ Mark missing_reactivity = True case:
            - Creator of ticket is Assignee
            - Support ticket late response (within 24 hours)
                => If a ticket is created by a non-Trobz member (customer):
                last response should always come from a Trobz member.
                If a ticket is a created by a Trobz member (internal issue):
                last response should always come from the "assignee".
        """
        # Use sql to search owner_id = create_uid
        sql = '''
            SELECT tst.id
            FROM tms_support_ticket tst
                JOIN tms_project tp
                ON tst.project_id = tp.id
            WHERE tst.state != 'closed' AND
                tp.state = 'active' AND
                tst.owner_id = tst.create_uid AND
                tst.id in %s
        '''
        self._cr.execute(sql, (tuple(sp_ticket_ids),))
        sp_ticket_ids = [ticket_id[0] for ticket_id in self._cr.fetchall()]
        sp_ticket_late_responses = self.env['tms.support.ticket']
        sp_ticket_not_late_responses = self.env['tms.support.ticket']
        now = datetime.now()
        for sp_ticket in self.browse(sp_ticket_ids):
            if sp_ticket._check_late_response(now):
                sp_ticket_late_responses |= sp_ticket
            else:
                sp_ticket_not_late_responses |= sp_ticket

        if sp_ticket_late_responses:
            sp_ticket_late_responses.write({
                'missing_reactivity': True,
                'missing_reactivity_reason': False})
        if sp_ticket_not_late_responses:
            sp_ticket_not_late_responses.write({
                'missing_reactivity': False,
                'missing_reactivity_reason': False})
        return True

    @api.multi
    def _check_late_response(self, now):
        self.ensure_one()
        tms_ticket_cmt_env = self.env['tms.ticket.comment']
        lastest_comment = tms_ticket_cmt_env.search(
            [('tms_support_ticket_id', '=', self.id),
             ('type', '=', 'comment'),
             ('is_invalid', '=', False)],
            order='name desc', limit=1)
        if lastest_comment and lastest_comment.name:
            comment_datetime = datetime.strptime(lastest_comment.name, DF)
            if (now - comment_datetime).days >= 1:
                author_member = lastest_comment.author_id and \
                    lastest_comment.author_id.is_trobz_member or False
                creator_member = self.create_uid.is_trobz_member
                if (author_member and creator_member) or \
                        (not author_member and not author_member):
                    return True
        return False

    @api.onchange('tms_forge_ticket_id')
    def onchange_forge_ticket(self):
        """
        Onchange working hours of Support ticket by forge ticket
        """
        if self.tms_forge_ticket_id:
            wh = self.tms_forge_ticket_id.tms_working_hour_ids
            self.tms_working_hour_ids = wh
        else:
            self.tms_working_hour_ids = None

    @api.constrains('tms_forge_ticket_id')
    def check_constrains_forge_support(self):
        """
        Can not link support ticket to a forge ticket
        which already have support ticket
        """
        for support in self:
            support_of_new_forge = \
                support.tms_forge_ticket_id.tms_support_ticket_id
            if support_of_new_forge and support.id != support_of_new_forge.id:
                raise Warning(
                    'Cannot set the support ticket for the forge ticket\n'
                    'Because this forge ticket had another support ticket'
                )
