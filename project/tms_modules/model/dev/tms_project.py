# -*- encoding: utf-8 -*-
import logging
from collections import defaultdict
from openerp.exceptions import Warning
from openerp import _, api, fields, models, SUPERUSER_ID
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import ast


class TmsProject(models.Model):

    _inherit = ['mail.thread']
    _name = "tms.project"
    _description = "Project"
    _order = "name"

    HEADER_FORMAT = u"<h4>{0}</h4>"
    ITEM_FORMAT = u"<li>{0} ({1}, {2}): {3}</li>"
    ITEM_LINK_FORMAT = u"<a href='{0}' target='_blank'>{1}</a>"
    GROUP_FORMAT = u"""<p><h5>{priority}</h5>
        <ul style='list-style-type: disc;'>{items}</ul></p>"""
    KEY_FIGURE_MESSAGE = '<div style="font-size:11px;font-style:italic;' +\
        'margin-left:30px" title="%s">%s</div>'
    KEY_FIGURE_TARGET = '<span style="font-size:14px;' +\
        'color:black;"><b>%s<b></span></div>'

    @api.onchange('team_id')
    def _onchange_team_id(self):
        for project in self:
            if project.team_id:
                project.owner_id = project.team_id.team_manager.user_id

    @api.multi
    def get_support_consumption_status(self):
        data_lst = []
        active_projects = self.env['tms.project'].search(
            [('state', '=', 'active')])
        for project in active_projects:
            # The projects being displayed in this email should have
            # at least one active (in-progress) support contract.
            contracts = project.get_active_contract()
            if not contracts:
                continue
            project_name = project.name
            project_owner = project.owner_id.name

            for contract in contracts:
                # Get data
                spent = contract.spent or 0.0
                budget = contract.budget or 0.0
                pro_rata_budget = contract.prorata_budget
                pro_rata_consumption = contract.prorata_consumption
                # Get dates of support contracts
                date_start = contract.start_date or '-'
                date_end = contract.end_date or '-'
                forecasted_date_done = contract.forecasted_date_done or '-'

                data_dict = {
                    'project_name': project_name,
                    'project_owner': project_owner,
                    'spent': spent,
                    'budget': budget,
                    'pro_rata_budget': pro_rata_budget,
                    'pro_rata_consumption': pro_rata_consumption,
                    'date_start': date_start,
                    'date_end': date_end,
                    'forecasted_date_done': forecasted_date_done,
                }
                data_lst.append(data_dict)
        # ordered by Pro-rata consumption desc
        data_lst_sorted = sorted(
            data_lst, key=lambda d: d['pro_rata_consumption'], reverse=True)

        table = u""
        LINE_TEMPLATE = u"""
            <tr>
                <td style="text-align: center; padding: 8px;">
                    %(project_name)s
                </td>
                <td style="text-align: center; padding: 8px;">
                    %(project_owner)s
                </td>
                <td style="text-align: right; padding: 8px;">
                    %(spent)s
                </td>
                <td style="text-align: right; padding: 8px;">
                    %(budget)s
                </td>
                <td style="text-align: right; padding: 8px;">
                    %(pro_rata_budget)s%%
                </td>
                <td style="text-align: right; padding: 8px;">
                    %(pro_rata_consumption)s%%
                </td>
                <td style="text-align: right; padding: 8px;">
                    %(date_start)s
                </td>
                <td style="text-align: right; padding: 8px;">
                    %(date_end)s
                </td>
                <td style="text-align: right; padding: 8px;">
                    %(forecasted_date_done)s
                </td>
            </tr>
        """
        LINE_TEMPLATE_OVER = u"""
            <tr>
                <td style="text-align: center; padding: 8px; color: red">
                    %(project_name)s
                </td>
                <td style="text-align: center; padding: 8px; color: red">
                    %(project_owner)s
                </td>
                <td style="text-align: right; padding: 8px; color: red">
                    %(spent)s
                </td>
                <td style="text-align: right; padding: 8px; color: red">
                    %(budget)s
                </td>
                <td style="text-align: right; padding: 8px; color: red">
                    %(pro_rata_budget)s%%
                </td>
                <td style="text-align: right; padding: 8px; color: red">
                    %(pro_rata_consumption)s%%
                </td>
                <td style="text-align: right; padding: 8px; color: red">
                    %(date_start)s
                </td>
                <td style="text-align: right; padding: 8px; color: red">
                    %(date_end)s
                </td>
                <td style="text-align: right; padding: 8px; color: red">
                    %(forecasted_date_done)s
                </td>
            </tr>
        """
        for row in data_lst_sorted:
            if row['spent'] > row['budget']:
                table += LINE_TEMPLATE_OVER % row
            else:
                table += LINE_TEMPLATE % row
        return table

    @api.multi
    def get_project_support_time_spent(self, project_id,
                                       current_day, first_day, last_day):
        support_time_spent = 0
        monthly_support_budget = 0
        pro_rata_consumption = 0

        activities = self.env['tms.activity'].search(
            [('project_id', '=', project_id),
             '|', ('date_end', '>', first_day), ('date_end', '=', None),
             ('analytic_secondaxis_id.code', '=', 'support')])
        for activity in activities:
            working_hours = self.env['tms.working.hour'].search(
                [('tms_activity_id', '=', activity.id),
                 ('date', '>=', first_day),
                 ('date', '<=', last_day)])
            # Sum support_time_spent
            for working_hour in working_hours:
                support_time_spent += working_hour.duration_hour
            # Sum monthly_support_budget
            monthly_support_budget += activity.day_sold_dev * 8

        # pro_rata_budget
        pro_rata_budget = int(
            (float(current_day.day) / float(last_day.day)) * 100
        )
        budget_in_hour = round(
            (float(monthly_support_budget * current_day.day) /
                float(last_day.day)), 2
        )
        # pro_rata_consumption
        if budget_in_hour != 0:
            pro_rata_consumption = int(
                (float(support_time_spent) / float(budget_in_hour)) * 100
            )
        data_time_spent = {
            'support_time_spent': support_time_spent,
            'monthly_support_budget': monthly_support_budget,
            'pro_rata_budget': pro_rata_budget,
            'pro_rata_consumption': pro_rata_consumption
        }
        return data_time_spent

    @api.multi
    def get_project_key_info(self):
        if not self:
            projects = self.search([])
        else:
            projects = self

        res = {}
        for project in projects:
            res.update({project['id']: project})
        return res

    @api.multi
    def _get_project_intensity(self):
        """
        Get the project Intensity based on number of support tickets created
        in the past 2 months
        """
        res = {}
        support_ticket_pool = self.env['tms.support.ticket']
        project_intensity_pool = self.env['tms.project.intensity']
        forge_ticket_pool = self.env['tms.forge.ticket']
        for project in self:
            today_date = datetime.today().date()
            past_2_month_date = (today_date -
                                 relativedelta(months=2)).strftime('%Y-%m-%d')
            no_of_requests = support_ticket_pool.search_count(
                [('project_id', '=', project.id),
                 ('create_date', '>=', past_2_month_date)]) + \
                forge_ticket_pool.search_count(
                [('project_id', '=', project.id),
                 ('create_date', '>=', past_2_month_date),
                 ('tms_support_ticket_id', '=', False)])
            project_intensity_ids = project_intensity_pool.search(
                [('min_tk', '<=', no_of_requests),
                 ('max_tk', '>=', no_of_requests)],)
            res[project.id] = project_intensity_ids and \
                project_intensity_ids[0] and \
                project_intensity_ids[0].id or False
        return res

    @api.model
    def auto_update_project_intensity(self):
        """
        @Function called by Scheduler to update project intensity daily
        """
        projects = self.search([])
        sql = ''
        for project in projects:
            intensity = project._get_project_intensity()
            project_intensity = intensity.get(project.id, False)
            if project_intensity:
                sql += '''UPDATE tms_project
                        SET tms_project_intensity_id = %d
                        WHERE id = %d;''' % (project_intensity, project.id)
        if sql:
            self._cr.execute(sql)
        return True

    @api.model
    def _get_auto_low_day_default(self):
        ir_config_obj = self.env['ir.config_parameter']
        support_action_defaults = ir_config_obj.get_param(
            'support_ticket_auto_actions_default_days')
        if support_action_defaults:
            support_action_defaults = eval(support_action_defaults)
            result = 'auto_low_days' in support_action_defaults and\
                support_action_defaults['auto_low_days'] or -1
        else:
            result = -1
        return result

    @api.model
    def _get_auto_close_day_default(self):
        ir_config_obj = self.env['ir.config_parameter']
        support_action_defaults = ir_config_obj.get_param(
            'support_ticket_auto_actions_default_days')
        if support_action_defaults:
            support_action_defaults = eval(support_action_defaults)
            result = 'auto_close_days' in support_action_defaults and\
                support_action_defaults['auto_close_days'] or -1
        else:
            result = -1
        return result

    # Columns
    owner_id = fields.Many2one(
        'res.users', string="Owner",
        help="The person in charge of making this project successful: " +
        "Happy Customer, Happy Team and Profitable.",
        default=lambda self: self._uid)

    name = fields.Char('Project name', size=256, required=True)
    partner_id = fields.Many2one('res.partner', 'Customer', required=True,
                                 domain="[('is_company', '=', True)]",
                                 track_visibility='onchange')
    trobz_partner_id = fields.Many2one('res.partner', 'Partner',
                                       domain="[('is_company', '=', True)]",
                                       track_visibility='onchange',
                                       help="Use Trobz Co. Ltd when we work"
                                       "directly with the final customer, "
                                       "Use the Partner name when Trobz "
                                       "doesn't work directly with the final "
                                       "customer (for instance Trobz Middle "
                                       "East). Keep empty for Internal "
                                       "projects.")
    technical_project_manager_id = fields.Many2one(
        'res.users', 'Technical Project Manager',
        required=True, track_visibility='onchange',
        domain=[('is_trobz_member', '=', True)]
    )

    # Project repository url, new way to manage project with one repo + subtree
    # TODO: add required=True when all project will be migrated to the "one
    # repo / project" configuration
    repository = fields.Char(
        'Project Repository', size=256,
        help='Full qualified GIT repository. '
        'Used for project setup with on repository + subtree.',
        track_visibility='onchange')

    # TODO: should not use fixed profile name in domain
    customer_project_manager = fields.Many2one(
        'res.users', 'Customer Project Manager',
        domain="[('partner_id.customer','=', True),"
        "('partner_id.is_company','=', False)]")
    standard_workflow = fields.Text('Standard Workflow',
                                    help="Workflows to be tested.")
    activity_ids = fields.One2many('tms.activity', 'project_id', 'Activities')
    milestones = fields.One2many('tms.milestone', 'project_id', 'Milestones')
    noti_trobz_audit = fields.Boolean('Notification Trobz Audit',
                                      default=True)
    # TODO-LOW: Project launch check-list: see :
    # https://docs.google.com/a/trobz.com/spreadsheet/ccc?key=0AsZtdLAzjmdtdGtQR0MzREc4MEp0UF9XS0ZCUndZRnc#gid=0
    # https://docs.google.com/a/trobz.com/spreadsheet/ccc?key=0AsZtdLAzjmdtdEd5bkxvcjNOS2gyUTJaaFRzQXhEMXc#gid=0
    # https://sites.google.com/a/trobz.com/dev/procedures/project-launch

    instance_ids = fields.One2many('tms.instance', 'project_id', 'Instances')
    requirement = fields.Text(
        'Requirements documentation',
        help="Where can the requirements/functional analysis be found.")

    user_documentation = fields.Char('User Documentation', size=256)
    state = fields.Selection(
        [('potential', 'Potential'), ('active', 'Active'),
         ('done', 'Done'), ('asleep', 'Asleep')],
        'Status', required=True, track_visibility='onchange')
    actions = fields.Text('Specific Actions for deployment')
    tester_id = fields.Many2one('res.users', 'Tester',
                                track_visibility='onchange',
                                domain=[('is_trobz_member', '=', True)])
    # Create a new field "Calculate Delivery Status"
    cal_delivery_status = fields.Boolean('Calculate Delivery Status',
                                         track_visibility='onchange',
                                         default=True)

    # Ticket 2720, In the form Project, new tab Support, including 2 new
    # fields default subscribers
    additional_subscribers = fields.Char(
        'Additional Subscribers', size=512,
        help='List of people who will added by default as Subscribers when '
        'a support ticket is created. For people without TMS account. '
        'Add email addresses to notify when changes are done on this ticket. '
        'Separate email addresses by a comma.')
    # 10945
    tms_project_support_subscriber_ids = fields.One2many(
        'project.subscriber', 'tms_project_id',
        string='Project Support Subscribers')
    # ticket 2833
    is_support_contract = fields.Boolean('Support Contract',
                                         track_visibility='onchange')

    default_supporter_id = fields.Many2one(
        'res.users', 'Support Project Manager', ondelete='restrict',
        required=True,
        help="Used when clicking on the button assign to Trobz.",
        track_visibility='onchange'
    )
    default_assignee_id = fields.Many2one(
        'res.users', 'Default Assignee', ondelete='restrict',
        required=True,
        help="On new Support ticker creation, Assignee field will be filled by"
             " the Default Assignee value.",
        track_visibility='onchange'
    )

    project_supporter_rel_ids = fields.Many2many(
        "res.users", "tms_project_supporter_rel", "project_id", "user_id",
        string="Trobz Supporters",
        help="Only those people would be listed in the fields Assignee, "
        "Reporter and Subscriber of the support ticket for.")

    invc_by_trobz_vn = fields.Boolean(
        string='Invoiceable by Trobz '
        'Vietnam (Default)', track_visibility='onchange', default=True,
        help='Default value for the field Invoiceable of Activities / '
        'Support Tickets; Invoiceable to the direct customer, '
        'whether it is invoiced or not to the Final Customer in '
        'case of projects through Partners. It should be set to '
        'False only for the projects handled by '
        'Dedicated Resources.')
    active = fields.Boolean(
        'Active', default=True,
        help="If the active field is set to False, "
        "it will allow you to hide the project without removing it.",
        track_visibility='onchange')
    project_type_id = fields.Many2one('tms.project.type', 'Project Type')
    mailing_list_ids = fields.One2many("mailman.list", "project_id",
                                       string="Mailing Lists")
    framework_version_id = fields.Many2one('tms.framework.version',
                                           'Framework Version')
    project_tag_id = fields.One2many('tms.project.tag',
                                     'project_id',
                                     'Tags')
    functional_block_ids = fields.Many2many(
        'tms.functional.block',
        'tms_functional_block_project_rel',
        'project_id',
        'tms_functional_block_id',
        'Functional Blocks'
    )
    manage_documentation = fields.Boolean(
        'Manage Documentation',
        help='If checked, display '
        'a new tab “Doc” on the support '
        'tickets of that project')
    forge_subscriber_ids = fields.One2many(
        "tms.forge.subscriber", "project_id", "Default Forge Subscribers"
    )
    description = fields.Text('Description')
    tms_project_intensity_id = fields.Many2one(
        comodel_name='tms.project.intensity',
        string='Intensity',
        help="Estimates the intensity of the "
        "project depending on the number of "
        "requests created in the past 2 months. "
        "The requests are counted as number of support tickets "
        "+ number of forge tickets not linked to a support ticket.")
    is_blocked = fields.Boolean(
        'Blocked', help="Use this checkbox to block a customer "
        "from using TMS. TMS will stop sending notification and "
        "block the creation/update of support tickets."
    )
    # F#14618: Add a new fields.Text "Server Support Contract"
    server_support_contract = fields.Text('Server Support Contract')
    readonly_mute_mail = fields.Boolean(
        compute='_compute_readonly_mute_mail')
    mute_mail_noti = fields.Boolean(
        string='Mute Support Mail Notification',
        track_visibility='onchange',
        help="When checked, the support email will be skipped. Only users with"
        " the profile 'Admin Profile'' are allowed to change the value of this"
        " field as it should only be used in exceptional cases when the"
        " standard workflows have not been respected.")

    activity_count = fields.Integer("Activities",
                                    compute="compute_activity_count")
    milestone_count = fields.Integer("Milestones",
                                     compute="compute_milestone_count")
    forge_ticket_count = fields.Integer("Forge Tickets",
                                        compute="compute_forge_ticket_count")
    project_portal_url = fields.Char('URL',
                                     help='A google doc (or a google site) to '
                                     'reference all the key info of the '
                                     'project (key events, links do project '
                                     'documents, special organization for this'
                                     ' project...). This document is meant to '
                                     'be internal, create a second one if you '
                                     'want to share with the customer but '
                                     'very few customer will use (none so '
                                     'far). For google doc, naming convention '
                                     'is "{Project Name} - Project Portal '
                                     '[Internal]".')
    support_ticket_count = fields.Integer(
        "Support Tickets", compute="compute_support_ticket_count")
    support_contracts_count = fields.Integer(
        "Support Contracts",
        compute="compute_support_contracts")
    # F#17332
    team_id = fields.Many2one('hr.team', string='Team')
    team_manager_id = fields.Many2one(string="Team Manager",
                                      related='team_id.team_manager',
                                      store=True)
    show_project_analysis = fields.Boolean(
        string='Show Project Analysis',
        help='Use this checkbox to allow Customer/Partner access to '
             'Activities, Working Hours, Milestones.',
        default=False,
        track_visibility='onchange')
    auto_low_days = fields.Integer(
        'Set low priority after x days inactive',
        default=lambda self: self._get_auto_low_day_default())
    auto_close_days = fields.Integer(
        'Close after y days inactive',
        default=lambda self: self._get_auto_close_day_default())
    target_ticket_ready_for_integration = fields.Integer(
        'Target ticket ready for integration'
    )
    target_ticket_ready_for_staging = fields.Integer(
        'Target ticket ready for staging'
    )
    target_ticket_ready_in_qa = fields.Integer(
        'Target ticket in QA',
    )
    support_contract_hours = fields.Integer(
        'Support Contract Hours',
        track_visibility='onchange',
        help='Support hours is defined in contract that it is valuable when '
        'application support contract is TRUE.')
    manage_dealine_on_sp_tickets = fields.Boolean(
        'Manage Deadline on Support Tickets')
    external_dev_ids = fields.Many2many(
        "res.users", "tms_project_external_dev_rel", "project_id", "user_id",
        string="External Developers",
        help="List of all developer from others company or freelancers",
        domain="[('is_external_dev', '=', True)]",
    )
    default_activity_id = fields.Many2one(
        'tms.activity',
        'Default Activity'
    )

    is_all_tpm_view_std_est = fields.Boolean(
        "Allow all TPM view ticket's Std Dev Estimation?",
        default=False
    )
    is_all_pm_fc_view_qc_est = fields.Boolean(
        "Allow all PM and FC view ticket's QC Estimation?",
        default=False
    )
    allow_dockerization_of_production_db = fields.Boolean(
        string='Allow dockerization of production database',
        default=True
    )
    check_missing_workload = fields.Boolean(
        'Mail check ticket missing workload',
        default=True,
        help='Forge tickets of this project will be track in mail ticket '
             'missing workload'
    )

    _sql_constraints = [
        ('project_unique', 'unique (name)', 'This project already exists!')]

    @api.model
    def create(self, vals):
        # Ensure project name is lowercase
        if vals.get('name', ''):
            vals['name'] = vals['name'].lower()
        res = super(TmsProject, self).create(vals)
        res.check_add_mailing_tpm_pm()
        # create default activities
        if res.state == "active":
            res._auto_create_default_activities()
        return res

    @api.multi
    def _auto_create_default_activities(self):
        '''
        Automatically create the default activities following
            the "default_project_idoject_activity" lis
        '''
        for rec in self:
            # get default activities list with sys parameter
            default_activities = self.env["ir.config_parameter"].get_param(
                "default_project_activity")
            # iterate all list for create new activity
            for activity in eval(default_activities):
                # update new infomation for default activity
                # - partner information
                # - project information
                activity.update(
                    {
                        "project_id": rec.id,
                        "partner_id": rec.partner_id.id,
                    }
                )

                # convert exist information
                # convert state
                state_table = {
                    "Planned": "planned",
                    "In progress": "in_progress",
                    "Done": "closed",
                    "Canceled": "canceled",
                }
                activity['state'] = state_table[activity['state']]

                # convert activity type
                activity_type_id = self.env["analytic.secondaxis"].search(
                    [("name", "=", activity.get(
                        "analytic_secondaxis_id", "/"
                    ).strip())],
                    limit=1
                ).id
                if activity_type_id:
                    activity["analytic_secondaxis_id"] = activity_type_id
                else:
                    Warning("Do not find the 'Activity Type' with name "
                            "{0}".format(activity["analytic_secondaxis_id"]))

                # create new default activity
                self.env["tms.activity"].sudo().create(activity)

    @api.multi
    def check_add_mailing_tpm_pm(self):
        mailing_obj = self.env['mailman.list']
        for record in self:
            lst_tpm_pm = list(set(
                [record.technical_project_manager_id, record.owner_id]))
            mailing_list = mailing_obj.search(
                [('project_id', '=', record.id),
                 ('active', '=', True)])
            if mailing_list:
                for tpm_pm in lst_tpm_pm:
                    mailing_list.write(
                        {'subscriber_ids': [(4, tpm_pm.partner_id.id)]})
        return True

    @api.multi
    def write(self, vals):
        """
        Update related support tickets
        when a project is marked having a support contract
        or removing from support contract.
        """
        support_ticket_env = self.env['tms.support.ticket']
        project_subscriber_env = self.env['project.subscriber']
        tms_forge_subscriber_env = self.env['tms.forge.subscriber']
        tms_subscriber_env = self.env['tms.subscriber']

        tpm_id = vals.get('technical_project_manager_id', False)
        tester_id = vals.get('tester_id', False)
        state = vals.get('state', False)
        project_supporter_list = vals.get('project_supporter_rel_ids', [])
        groups_str = self.env[
            'ir.config_parameter'].get_param(
                'groups_allowed_change_project_supporter', [])
        groups_xmlid = ast.literal_eval(groups_str)
        groups_xmlid = [i.strip() for i in groups_xmlid]
        group_ids = []
        list_group = []
        for xmlid in groups_xmlid:
            group = self.env.ref(xmlid, raise_if_not_found=False)
            if group:
                group_ids.append(group.id)
                list_group.append(group.name)
        groups_str = ", ".join(list_group)

        if project_supporter_list:
            # Check the Profile that allowed change
            user = self.env.user
            if not user.group_profile_id or \
                (user.group_profile_id and
                 user.group_profile_id.id not in group_ids):
                raise Warning(
                    _('Warning'),
                    _('Only users with Profile %s can change the'
                      ' supporters on project' % groups_str))

        # Ensure project name is lowercase
        if vals.get('name', ''):
            vals['name'] = vals['name'].lower()
        for project_obj in self:
            # F#29929 Check support contracts related
            if state == 'done' or state == 'asleep':
                project_obj.check_support_contracts(project_obj.id)

            if state == 'active':
                project_obj._auto_create_default_activities()

            if project_supporter_list:
                new_supporter_ids = project_supporter_list[0][2]

                old_supporter_ids = [supporter.id for supporter in
                                     project_obj.project_supporter_rel_ids]
                # Get supporters are removed
                removed_supporter_ids = list(
                    set(old_supporter_ids) - set(new_supporter_ids))
                # Removing a supporter

                # Check default project of removed supporter
                result = self.check_default_project(
                    project_obj.id, removed_supporter_ids)
                if result:
                    raise Warning(
                        _('Warning'),
                        _('User "%s" must be a supporter of project "%s"'
                          ' because it is his/her default project.'
                          ' If you want to remove user from list supporters,'
                          ' please remove default project on user form'
                          ' firstly' %
                          (result, project_obj.name)))
                if removed_supporter_ids:
                    tpm_id = tpm_id or\
                        project_obj.technical_project_manager_id.id
                    tester_id = tester_id or project_obj.tester_id.id
                    if tpm_id in removed_supporter_ids or tester_id \
                            in removed_supporter_ids:
                        raise Warning(
                            _('This user is TPM or Tester of "%s" project, '
                              'can not remove this user out of supporter '
                              'of "%s" project' % (self.name,
                                                   self.name)))
                    # (1). he must be unsubcribed in the support tickets.
                    support_ticket_objs = support_ticket_env.search([(
                        'project_id', '=', project_obj.id)])
                    subscriber_objs = tms_subscriber_env.search([
                        ('support_id', 'in', support_ticket_objs.ids),
                        ('name', 'in', removed_supporter_ids)])
                    subscriber_objs.unlink()

                    # (2). he must be removed from the default forge
                    # subscribers of the project
                    tms_forge_subscriber_objs = \
                        tms_forge_subscriber_env.search(
                            [('project_id', '=', project_obj.id),
                             ('name', 'in', removed_supporter_ids)])
                    tms_forge_subscriber_objs.unlink()

                    # (3). he must be removed from the default support
                    # subscribers of the project
                    project_subscriber_objs = \
                        project_subscriber_env.search(
                            [('tms_project_id', '=', project_obj.id),
                             ('name', 'in', removed_supporter_ids)])
                    project_subscriber_objs.unlink()

            if tpm_id or tester_id:
                if project_supporter_list:
                    check_supporter_list = project_supporter_list[0][2]
                else:
                    check_supporter_list = self.project_supporter_rel_ids.ids
                if tester_id and tester_id not in check_supporter_list or \
                        tpm_id and tpm_id not in check_supporter_list:
                    raise Warning(
                        _('Tester and TPM must be supporter of the project'))

            if 'is_support_contract' in vals or vals.get('partner_id', False):
                update_vals = []
                update_forge_sql = ''
                project_ids_str = ",".join(map(str, self.ids))

                # Update is_support_contract on support tickets
                if 'is_support_contract' in vals:
                    is_support_contract = vals.get(
                        'is_support_contract', False) and 't' or 'f'
                    update_vals.append(
                        "is_support_contract = '%s'" % is_support_contract)

                # Update customer info on both support tickets and forge
                # tickets
                if vals.get('partner_id', False):
                    update_vals.append("customer_id = %s" % vals['partner_id'])
                    # Prepare to update forge tickets
                    update_forge_sql = """
                        UPDATE tms_forge_ticket
                        SET customer_id = %s
                        WHERE project_id IN (%s);
                    """ % (vals['partner_id'], project_ids_str)

                # Update related support tickets
                update_sql = """
                    UPDATE tms_support_ticket
                    SET write_uid = %s,
                        write_date = NOW() AT TIME ZONE 'UTC',
                        %s
                    WHERE project_id IN (%s);
                """ % (self._uid, ",".join(update_vals), project_ids_str)

                # Update related forge tickets
                if update_forge_sql:
                    update_sql += update_forge_sql
                self._cr.execute(update_sql)

            # Hidden 'Documentation' Tag on TMS Support ticket with
            # Documentation Required is False
            # and Documentation Status is Not Required
            if 'manage_documentation' in vals and \
                    not vals.get('manage_documentation', False):
                support_ticket_objs = support_ticket_env.search(
                    [('project_id', '=', project_obj.id)])
                if support_ticket_objs:
                    update_sql = '''
                    update tms_support_ticket
                    set documentation_required = 'f',
                    manage_documentation = 'f',
                    documentation_status = 'not_required'
                    where id in %s;
                    '''
                    self._cr.execute(
                        update_sql, (tuple(support_ticket_objs.ids),))
            super(TmsProject, project_obj).write(vals)
            if 'technical_project_manager_id' or \
                    'owner_id' or 'mailing_list_ids' in vals:
                self.check_add_mailing_tpm_pm()
        return True

    @api.multi
    def get_assigned_tickets(self):
        """
            Find all assigned tickets of current project
            and group by priority from high to low
        """
        project = self[0]
        sql = '''
            SELECT TST.name, TST.state,
            RP.name AS owner_name, TST.summary, TST.priority
            FROM tms_support_ticket TST
                JOIN res_users RU ON TST.owner_id = RU.id
                JOIN res_partner RP ON RP.id = RU.employer_id
                JOIN tms_project TP ON TST.project_id = TP.id
            WHERE TST.project_id IN (%s)
                AND TST.state != 'closed'
                AND TP.state = 'active'
                AND RU.id IN (
                    SELECT id FROM res_users WHERE employer_id IN (%s))
            ORDER BY (
                CASE
                    WHEN TST.priority = 'urgent' THEN 0
                    WHEN TST.priority = 'major' THEN 1
                    WHEN TST.priority = 'normal' THEN 2
                    WHEN TST.priority = 'minor' THEN 3
                    ELSE 4
                END
            ), TST.id DESC;
        ''' % (project.id, project.partner_id.id)
        header = 'Here is the list of support tickets assigned to you:'
        return self.compose_status_mail_contents(sql, header)

    @api.multi
    def get_tickets_ready_for_production(self):
        """
            Find all ready tickets of current project
            and group by priority from high to low
        """
        sql = '''
            SELECT TST.name, TST.state,
            RP.name AS owner_name, TST.summary, TST.priority
            FROM tms_support_ticket TST
                JOIN res_users RU
                    ON TST.owner_id = RU.id
                JOIN res_partner RP
                    ON RP.id = RU.employer_id
                JOIN tms_project TP
                    ON TST.project_id = TP.id
            WHERE TST.project_id IN (%s)
                AND TST.state = 'ok_for_production'
                AND TP.state = 'active'
            ORDER BY (
                CASE
                    WHEN TST.priority = 'urgent' THEN 0
                    WHEN TST.priority = 'major' THEN 1
                    WHEN TST.priority = 'normal' THEN 2
                    WHEN TST.priority = 'minor' THEN 3
                    ELSE 4
                END
            ), TST.id DESC;
        ''' % (self.ids[0])

        header = 'Here is the list of support tickets '
        'in the status "Ok for production":'
        return self.compose_status_mail_contents(sql, header)

    @api.multi
    def compose_status_mail_contents(self, sql, header):
        """
            @param {str} sql: the raw sql query to be executed
            @param {str} header: the header text to be displayed
                                 if sql query execution has result
        """

        # Get object pool reference
        config_pool = self.env['ir.config_parameter']
        action_pool = self.env['ir.actions.act_window']

        # Get the base url of current instance
        default_conf = 'https://tms.trobz.com'
        conf_val = config_pool.get_param(
            'web.base.url', default=default_conf)

        # Check if we are on production, because we usually use `tms.trobz.com`
        # domain to access system a bit hardcoded but no way else to do
        temp_url = default_conf if "tms.trobz.com" in conf_val else conf_val
        base_url = temp_url + '/web?db=%s' % self._cr.dbname
        # Find the default action of menu Support Tickets (Support > Support
        # Tickets > Support Tickets)
        act_window = action_pool.for_xml_id(
            'tms_modules', 'action_view_tms_support_ticket_open'
        )

        # Get related data for customer support tickets
        compose_contents = ""
        self._cr.execute(sql)
        query_result = self._cr.fetchall() or []
        groups = defaultdict(list)

        URL_TEMPLATE = \
            u"{0}#id={1}&view_type=form&model=tms.support.ticket&action={2}"

        for _id, state, owner_name, summary, priority in query_result:
            # Compose format for ticket status notification
            url = URL_TEMPLATE.format(
                base_url, _id, act_window["id"])

            link = self.ITEM_LINK_FORMAT.format(url, _id)
            format_msg = self.ITEM_FORMAT.format(
                link, state, owner_name, summary)

            # Append to classified group of Support tickets
            groups[priority].append(format_msg)

        if groups:
            # Always put header at the top
            compose_contents = self.HEADER_FORMAT.format(header)

            if groups.get("urgent", ""):  # Very High Priority
                urgent_dict = {
                    "priority": "Very High Priority",
                    "items": "".join(groups["urgent"])}
                compose_contents += self.GROUP_FORMAT.format(**urgent_dict)

            if groups.get("major", ""):  # High Priority
                major_dict = {
                    "priority": "High Priority",
                    "items": "".join(groups["major"])}
                compose_contents += self.GROUP_FORMAT.format(**major_dict)

            if groups.get("normal", ""):  # Normal Priority
                normal_dict = {
                    "priority": "Normal Priority",
                    "items": "".join(groups["normal"])}
                compose_contents += self.GROUP_FORMAT.format(**normal_dict)

            if groups.get("minor", ""):  # Low Priority
                minor_dict = {
                    "priority": "Low Priority",
                    "items": "".join(groups["minor"])}
                compose_contents += self.GROUP_FORMAT.format(**minor_dict)
        return compose_contents

    @api.multi
    def get_mail_list(self):
        """
            Get email list from supporters of project
            If not Trobz member, only consider if
            send_support_status_mail = True (setup in users form)
        """
        mail_list = ''
        project = self[0]
        if project.default_supporter_id and project.default_supporter_id.email:
            mail_list += project.default_supporter_id.email + ','
        for supporter in project.project_supporter_rel_ids:
            if supporter.email:
                if supporter.is_trobz_member:
                    mail_list += supporter.email + ','
                else:
                    if supporter.send_support_status_mail:
                        mail_list += supporter.email + ','
        return mail_list

    @api.multi
    def get_partner_project_mailing_list(self):
        """
            Return Project mailing list or Trobz default project mailing list
        """

        # Get default support sender email
        config_pool = self.env["ir.config_parameter"]

        PARAM_DEFAULT_MAIL = "trobz_default_project_mailing_list_email"

        default_config_email = config_pool.get_param(
            PARAM_DEFAULT_MAIL)

        assert default_config_email, ('Config param ' +
                                      PARAM_DEFAULT_MAIL +
                                      ' must be set.')

        if self and len(self) == 1:
            project = self[0]
            project_emails_list = []
            for mailing in project.mailing_list_ids:
                if mailing.is_used_for_sup_notif:
                    project_emails_list.append(
                        mailing.name + '@lists.trobz.com')
            project_emails = ', '.join(project_emails_list)

            if project_emails:
                return_mail = project_emails
            else:
                logging.warning("Project %s is missing support mailing list."
                                % project.name)
                return_mail = default_config_email

        else:
            logging.error("The function get_partner_project_mailing_list " +
                          "should be called with a list of exactly 1 project.")
            return_mail = default_config_email

        return return_mail

    @api.model
    def automatic_send_email_to_customers(self):
        """
            Automatic weekly send email to customers about current tickets
            of the Project
            If project is blocked or have not email list:
                - not send email
                - continue check next project
            else:
                - check assigned tickets and tickets ready for production
                - send email
        """
        # context = self._context and self._context.copy() or {}
        project_pool = self.env['tms.project']
        projects = project_pool.search([])
        email_template = self.env.ref(
            'tms_modules.email_template_to_customers_with_support_status'
        )
        for project in projects:
            # F#12936: Do not send email from blocked project
            if project.is_blocked or not project.get_mail_list():
                logging.info(
                    '=== Support Weekly Notification email: missing'
                    ' sender or blocked for project with id: %s' % project.id)
                continue
            elif not project.get_mail_list():
                logging.error('Support Weekly Notification email: missing'
                              ' sender for project with id: %s' % project.id)
                continue
            elif project.get_assigned_tickets() or \
                    project.get_tickets_ready_for_production():
                # Send email for each project
                email_template._send_mail_asynchronous(project.id)
        return True

    @api.model
    def _get_project_supporters(self, project_id):
        """
        Get users in supporters of given project
        """
        if not project_id:
            return []
        project = self.browse(project_id)
        return project.project_supporter_rel_ids and \
            project.project_supporter_rel_ids.ids or []

    # ====================================================
    # =============== EMAILS TMS PROJECT ===================
    # ====================================================
    @api.model
    def get_target_ready_for_intergragion(self):
        return self.env['email.template'].get_target_value(
            'Ready for integration')
    # get target type description

    @api.model
    def get_target_tickets_ready_for_staging(self):
        return self.env['email.template'].get_target_value(
            'Tickets ready for staging')

    @api.model
    def get_target_number_tickets_in_qa(self):
        return self.env['email.template'].get_target_value('QA tickets')

    @api.multi
    def compute_activity_count(self):
        activity_pool = self.env["tms.activity"]
        for record in self:
            record.activity_count = activity_pool.search_count(
                [('project_id', '=', record.id)])

    @api.multi
    def compute_milestone_count(self):
        milestone_pool = self.env["tms.milestone"]
        for record in self:
            record.milestone_count = milestone_pool.search_count(
                [('project_id', '=', record.id)])

    @api.multi
    def compute_forge_ticket_count(self):
        forge_ticket_pool = self.env["tms.forge.ticket"]
        for record in self:
            record.forge_ticket_count = forge_ticket_pool.search_count(
                [('project_id', '=', record.id),
                 ('state', '!=', 'closed')])

    @api.multi
    def compute_support_ticket_count(self):
        support_ticket_pool = self.env["tms.support.ticket"]
        for record in self:
            record.support_ticket_count = support_ticket_pool.search_count(
                [('project_id', '=', record.id),
                 ('state', '!=', 'closed')])

    @api.multi
    def compute_support_contracts(self):
        for record in self:
            sql = """
                SELECT COUNT(*) FROM ref_project_contract WHERE project_id = %s
            """ % (record.id)
            record._cr.execute(sql)
            datas = record.env.cr.fetchone()
            record.support_contracts_count = datas[0]

    @api.multi
    def _compute_readonly_mute_mail(self):
        user = self.env.user
        is_admin = user.is_admin_profile() or user.id == SUPERUSER_ID
        for project in self:
            if project.owner_id.id == user.id or is_admin:
                project.readonly_mute_mail = False
            else:
                project.readonly_mute_mail = True

    @api.model
    def get_support_ticket_by_user(self, date_from, date_to, activity_ids):
        """Get support ticket by user"""
        result = {}
        project_ids = self.ids or [-1]
        activity_ids = activity_ids and activity_ids or [-1]

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
                        AND tst.tms_activity_id =
                        ANY ( array[%(activity_ids)s]))
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
                    END AS assignee
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
                    assignee
             FROM   total_ticket
             GROUP  BY assignee,
                       assignee_id),
         support_ticket_by_user
         AS (SELECT tt.assignee as name,
                    tt.assignee_id as id,
                    pt.priority,
                    SUM(pt.total_priority_ticket) AS total_priority_ticket,
                    tt.total_ticket
             FROM   group_total_ticket AS tt
                    left join priority_ticket AS pt
                           ON pt.assignee = tt.assignee
             GROUP  BY tt.assignee,
                       tt.assignee_id,
                       pt.priority,
                       tt.total_ticket)
         SELECT row_to_json(support_ticket_by_user)
         FROM   support_ticket_by_user """ % {
            'date_from': date_from,
            'date_to': date_to,
            'activity_ids': activity_ids,
            'project_id': project_ids}

        self._cr.execute(sql)
        result['total'] = {'data': {'name': 'Global',
                                    'total': 0,
                                    '%': 0.00,
                                    'Very High': 0,
                                    'Normal': 0,
                                    'High': 0,
                                    'Low': 0,
                                    'Open': 0, }, }
        for line in self._cr.fetchall():
            line_id = line[0]['id']
            if line_id not in result:
                result[line_id] = {}
                result[line_id]['data'] = {
                    'name': line[0]['name'],
                    'total': line[0]['total_ticket'] or 0,
                    'Open': 0,
                    '%': 0.00,
                    'Very High': 0,
                    'Normal': 0,
                    'High': 0,
                    'Low': 0, }
                result['total']['data']['total'] += \
                    result[line_id]['data']['total']
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
        res.append(result['total'])
        if not float(result['total']['data']['Open']):
            return res
        for key in result:
            result[key]['data']['%'] = \
                round(float(result[key]['data']['Open']) /
                      float(result[key]['data']['total']) * 100, 2)
            if key == 'total':
                continue
            res.append(result[key])
        return res

    @api.model
    def get_forge_ticket_by_user(self, date_from, date_to, activity_ids):
        """Get forge ticket by user"""
        result = {}
        project_ids = self.ids
        activity_ids = activity_ids if activity_ids \
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
                        AND tft.tms_activity_id =
                        ANY ( array[%(activity_ids)s]))
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
                    END AS assignee
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
                    assignee
             FROM   total_ticket
             GROUP  BY assignee,
                       assignee_id),
         forge_ticket_by_user
         AS (SELECT tt.assignee as name,
                    tt.assignee_id as id,
                    pt.priority,
                    SUM(pt.total_priority_ticket) AS total_priority_ticket,
                    tt.total_ticket
             FROM   group_total_ticket AS tt
                    left join priority_ticket AS pt
                           ON pt.assignee = tt.assignee
             GROUP  BY tt.assignee,
                       tt.assignee_id,
                       pt.priority,
                       tt.total_ticket)
         SELECT row_to_json(forge_ticket_by_user)
         FROM   forge_ticket_by_user """ % {
            'date_from': date_from,
            'date_to': date_to,
            'activity_ids': activity_ids,
            'project_id': project_ids,
        }
        self._cr.execute(sql)
        result['total'] = {'data': {'name': 'Global',
                                    'total': 0,
                                    '%': 0.00,
                                    'Very High': 0,
                                    'Normal': 0,
                                    'High': 0,
                                    'Low': 0,
                                    'Open': 0, }, }
        for line in self._cr.fetchall():
            line_id = line[0]['id']
            if line_id not in result:
                result[line_id] = {}
                result[line_id]['data'] = {
                    'name': line[0]['name'],
                    'total': line[0]['total_ticket'] or 0,
                    'Open': 0,
                    '%': 0.00,
                    'Very High': 0,
                    'Normal': 0,
                    'High': 0,
                    'Low': 0, }
                result['total']['data']['total'] += \
                    result[line[0]['id']]['data']['total']
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
        res.append(result['total'])
        if float(result['total']['data']['Open']) != 0:
            for key in result:
                result[key]['data']['%'] = \
                    round(float(result[key]['data']['Open']) /
                          float(result[key]['data']['total']) * 100, 2)
                if key != 'total':
                    res.append(result[key])
        return res

    @api.model
    def run_scheduler_clean_support_ticket(self):
        """run scheduler check support ticket on project"""
        logging.info("=== START to clean the support tickets automatically: "
                     "set to low / close after x days")

        projects = self.search(["|", ('auto_low_days', '>', 0),
                                ('auto_close_days', '>', 0)])
        for project in projects:
            support_tickets = self.env['tms.support.ticket']
            today = date.today()
            # set low the tickets which are without action over auto_low_days
            if project.auto_low_days > 0:
                set_low_tickets = support_tickets.search([
                    ('project_id', '=', project.id),
                    ('priority', '!=', 'low'),
                    ('state', '!=', 'closed'),
                    ('write_date', '<', str(
                        today - timedelta(days=project.auto_low_days)))])
                if set_low_tickets:
                    set_low_tickets.write({'priority': 'minor'})
            # close the tickets which are without action over auto_close_days
            if project.auto_close_days > 0:
                tickets_close = support_tickets.search([
                    ('project_id', '=', project.id),
                    ('priority', '=', 'low'),
                    ('state', '!=', 'closed'),
                    ('write_date', '<',
                     str(today -
                         timedelta(days=project.auto_close_days)))])
                if tickets_close:
                    tickets_close.write({'state': 'closed'})
            project.auto_send_email_supporters()
            logging.info("=== END to clean the support tickets automatically: "
                         "set to low / close after x days")
        return True

    @api.multi
    def get_tickets_set_low(self, days_to_notification):
        """get ticket will set low on days_to_notification days"""
        end_date = date.today() - \
            timedelta(days=self.auto_low_days - days_to_notification)
        start_date = end_date - timedelta(days=7)
        domain = [('project_id', '=', self.id),
                  ('priority', '!=', 'low'),
                  ('state', '!=', 'closed'),
                  ('write_date', '>', str(start_date)),
                  ('write_date', '<', str(end_date))]
        return self.env['tms.support.ticket'].search(domain)

    @api.multi
    def get_tickets_close(self, days_to_notification):
        """get ticket will be closed on days_to_notification days"""
        return self.env['tms.support.ticket'].search([
            ('project_id', '=', self.id),
            ('priority', '=', 'low'),
            ('state', '!=', 'closed'),
            ('write_date', '<',
             str(date.today() -
                 timedelta(
                     days=self.auto_close_days - days_to_notification)))])

    @api.multi
    def auto_send_email_supporters(self):
        """
            Automatic Notification for automatic actions
            scheduled on Support Tickets.
        """
        email_template = self.env.ref(
            'tms_modules.email_inactive_ticket_to_supporter_template'
        )
        if self.get_mail_list() and \
            (self.get_tickets_set_low(7) or
             self.get_tickets_set_low(14) or
             self.get_tickets_close(7) or
             self.get_tickets_close(14)):
            email_template._send_mail_asynchronous(self.id)
        return True

    @api.model
    def get_forge_key_figures_per_project(self):
        res = self.sql_get_forge_key_figures_per_project()

        table_template = u"""
            <table border="1" style="border-collapse: collapse;">
                <tr style="background: #DDD;">
                    <th style="padding:5px 10px;" rowspan="2">Project</th>
                    <th style="padding:5px 10px;" colspan="2">
                        Ticket ready for integration
                    </th>
                    <th style="padding:5px 10px;" colspan="2">
                        Ticket ready for staging
                    </th>
                    <th style="padding:5px 10px;" colspan="2">Ticket in QA</th>
                </tr>
                <tr style="background: #DDD;">
                    <th style="padding:5px 10px;" >Current</th>
                    <th style="padding:5px 10px;" >Target</th>
                    <th style="padding:5px 10px;" >Current</th>
                    <th style="padding:5px 10px;" >Target</th>
                    <th style="padding:5px 10px;" >Current</th>
                    <th style="padding:5px 10px;" >Target</th>
                </tr>
                {0}
            </table>
        """
        table_row_template = u"""
            <tr>
                <td style="padding:5px 10px; text-align: center;">{0}</td>
                <td style="padding:5px 10px; text-align: center; color:{1};">
                    {2}
                </td>
                <td style="padding:5px 10px; text-align: center">{3}</td>
                <td style="padding:5px 10px; text-align: center; color:{4};">
                    {5}
                </td>
                <td style="padding:5px 10px; text-align: center;">{6}</td>
                <td style="padding:5px 10px; text-align: center; color:{7};">
                    {8}
                </td>
                <td style="padding:5px 10px; text-align: center;">{9}</td>
            </tr>
        """
        row_results = []
        if len(res) == 0:
            row_results = self.get_empty_row_result(table_row_template)
            return table_template.format("".join(row_results))
        default_target_integration = self.get_target_ready_for_intergragion()
        default_target_staging = self.get_target_tickets_ready_for_staging()
        default_target_in_qa = self.get_target_number_tickets_in_qa()
        for rec in res:
            project = rec[0] and rec[0] or ''

            # Ticket ready for integration
            tickets_integration_current = rec[1] and rec[1] or 0
            tickets_integration_target = rec[2] and rec[2] > 0 and rec[2] or\
                default_target_integration

            # Ticket ready for staging
            tickets_staging_current = rec[3] and rec[3] or 0
            tickets_staging_target = rec[4] and rec[4] > 0 and rec[4] or \
                default_target_staging

            # Ticket in QA
            tickets_qa_current = rec[5] and rec[5] or 0
            tickets_qa_target = rec[6] and rec[6] > 0 and rec[6] or \
                default_target_in_qa

            if tickets_integration_current > tickets_integration_target or \
                    tickets_staging_current > tickets_staging_current or \
                    tickets_qa_current > tickets_qa_target:
                # Get color for each type
                integration_color = self.get_color_compare_current_and_target(
                    tickets_integration_current, tickets_integration_target)
                staging_color = self.get_color_compare_current_and_target(
                    tickets_staging_current, tickets_staging_target)
                qa_color = self.get_color_compare_current_and_target(
                    tickets_qa_current, tickets_qa_target)

                # Composed new row
                composed_row = table_row_template.format(
                    project,
                    integration_color,
                    tickets_integration_current,
                    tickets_integration_target,
                    staging_color,
                    tickets_staging_current,
                    tickets_staging_target,
                    qa_color,
                    tickets_qa_current,
                    tickets_qa_target
                )
                row_results.append(composed_row)
        if len(row_results) == 0:
            row_results = self.get_empty_row_result(table_row_template)
        return table_template.format("".join(row_results))

    @api.model
    def get_color_compare_current_and_target(self, current, target):
        return current > target and "red" or "black"

    @api.model
    def get_empty_row_result(self, table_row_template):
        row_results = []
        composed_row = table_row_template.format(
            "No Data", "black", "", "", "black", "", "", "black", "", "")
        row_results.append(composed_row)
        return row_results

    @api.model
    def sql_get_forge_key_figures_per_project(self):
        sql = '''
        SELECT tp.name, integration.nb, tp.target_ticket_ready_for_integration,
            staging.nb, tp.target_ticket_ready_for_staging,
            qa.nb, tp.target_ticket_ready_in_qa
        FROM tms_project tp FULL JOIN (
                    SELECT count(tft.id) as nb, tft.project_id as project_id
                    FROM tms_forge_ticket tft
                    JOIN tms_project tp on tft.project_id = tp.id
                    WHERE tft.state in ('code_completed','ready_to_deploy')
                    and tp.state = 'active' and tp.active = true
                    GROUP BY tft.project_id ) as integration
                on tp.id = integration.project_id
                FULL JOIN (
                    SELECT count(tft.id) as nb, tft.project_id as project_id
                    FROM tms_forge_ticket tft
                    JOIN tms_project tp on tp.id = tft.project_id
                    WHERE tft.delivery_status = 'ready_for_staging'
                    and tp.state = 'active' and tp.active = true
                    GROUP BY tft.project_id
                ) as staging
                on tp.id = staging.project_id
                FULL JOIN (
                    SELECT count(tft.id) as nb, tft.project_id as project_id
                    FROM tms_forge_ticket tft
                    JOIN tms_project tp on tp.id = tft.project_id
                    WHERE tft.state= 'in_qa'
                    and tp.state = 'active' and tp.active = true
                    GROUP BY tft.project_id
                ) as qa
                on tp.id = qa.project_id
        ORDER BY tp.name ASC
        '''
        self._cr.execute(sql)
        res = self._cr.fetchall()
        return res

    @api.multi
    def view_contracts_related(self):
        self.ensure_one()
        action_contract = self.env.ref(
            'tms_modules.action_project_support_contracts').read()[0]
        sql = """
            SELECT contract_id FROM ref_project_contract WHERE
            project_id = %s
        """ % (self.id)
        self._cr.execute(sql)
        datas = self.env.cr.fetchall()
        contract_ids = [data[0] for data in datas]
        action_contract.update({'domain': [('id', 'in', contract_ids)]})
        return action_contract

    @api.multi
    def get_active_contract(self):
        """
        Return contract in planned or in progress
        """
        self.ensure_one()
        sql = """
            SELECT contract_id FROM ref_project_contract WHERE
            project_id = %s
        """ % (self.id)
        self._cr.execute(sql)
        datas = self.env.cr.fetchall()
        contract_ids = [data[0] for data in datas]
        contracts = self.env[
            'project.support.contracts'].search(
                [('id', 'in', contract_ids),
                 ('state', '=', 'in_progress')])
        return contracts

    @api.model
    def check_default_project(self, pro_id, supporter_ids):
        supporters = self.env['res.users'].search(
            [('id', 'in', supporter_ids)])
        for supporter in supporters:
            if supporter.default_project_id and\
                    pro_id == supporter.default_project_id.id:
                return supporter and supporter.partner_id and \
                    supporter.partner_id.name
        return False

    @api.model
    def check_support_contracts(self, pro_id):
        sql = """
            SELECT contract_id FROM ref_project_contract WHERE
            project_id = %s
        """ % (pro_id)
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
                'Some Support Contracts of this project are still '
                '"Planned" or "In Process". Please handle its support '
                'contract firstly if you expect to perform this action.'
            )

    @api.multi
    def support_contract_by_project(self):
        ctx = self.env.context.copy()
        ctx.update(
            {
                'default_project_ids': [self.id]
            }
        )
        sql = '''
        SELECT contract_id FROM ref_project_contract WHERE project_id = %s
        '''
        self._cr.execute(sql % self.id)
        contract_ids = [i[0] for i in self._cr.fetchall()]
        return {
            'name': 'Support Contracts',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'project.support.contracts',
            'type': 'ir.actions.act_window',
            'context': ctx,
            'search_view_id': self.env.ref(
                'tms_modules.view_project_support_contracts_tree').id,
            'domain': "[('id', 'in', %s)]" % contract_ids,
            'target': 'current',
        }

    @api.multi
    def button_remove_subscribe(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tms.remove.subscribe.wizard',
            'target': 'new',
            'context': dict(self.env.context, default_project_id=self.id),
            'view_type': 'form',
            'view_mode': 'form',
        }

    wkhtmltopdf_version_id = fields.Many2one(
        'tms.wkhtmltopdf.version',
        string='Wkhtmltopdf Version',
    )
