# -*- encoding: UTF-8 -*-
from datetime import datetime, timedelta
import re

from openerp import fields, api, models
import time
from openerp.tools import float_utils
from copy import deepcopy
from openerp.exceptions import Warning

SUPPORT_TYPE = [
    ('unclassified', 'Support Unclassified'),
    ('initial_project', 'Support Initial Project'),
    ('functional_support', 'Support Functional Support'),
    ('evolution', 'Support Evolution'),
    ('adjustment', 'Support Adjustment'),
    ('defect', 'Support Defect'),
    ('other', 'Support Other'),
    ('no_support', 'Not Support'),
    ('support_functional_consultant', 'Support Functional Consultant')
]
SUPPORT_TYPE_HELP = """
- Support Unclassified:for the time spent before the ticket is classified
- Support Evolution
- Support Adjustment
- Support Defect
- Support Functional Support
- Support Other
- Not Support: the time is not spent on support
- Support Functional Consultant: For the time spend by Functional Consultant
  when not assigned to ticket
"""

DEV_TYPE = [
    ('new_feature', 'New Feature'),
    ('qa', 'QA'),
    ('fixing', 'Fixing'),
    ('other', 'Other')
]
DEV_TYPE_HELP = """
- New Feature: Time spent on a forge ticket by dev before the ticket is set to
  code_complete for the first time
- QA: Time spent on the testing of the ticket
- Fixing: Time spent on a forge ticket by dev after the ticket is set to
  code_complete for the first time
- Other: Time spent not associated to a forge ticket"
"""


class tms_working_hour(models.Model):

    _name = "tms.working.hour"
    _description = "Working hour"
    _order = "date desc, name"

    @api.onchange('date', 'duration_hour')
    def on_change_date_duration(self):
        if not self.duration_hour:
            self.duration_hour = 0
        if self.date:
            daily_working_hour_objs = self.search(
                [('user_id', '=', self._uid), ('date', '=', self.date)])
            if self.ids:
                total = 0
            else:
                total = self.duration_hour
            for daily_wh in daily_working_hour_objs:
                if daily_wh.id in self.ids:
                    total += self.duration_hour
                else:
                    total += daily_wh.duration_hour

            total = float_utils.float_round(total, precision_rounding=.001)
            self.daily_total = total

    @api.onchange('tms_activity_id')
    def onchange_job_type_on_activity(self):
        """
        Return domain to show allowed job types base on activity
        """
        domain = []
        activity = self.tms_activity_id
        allowed_job_types = activity.job_type_ids
        if allowed_job_types:
            domain = [('id', 'in', allowed_job_types.ids)]
            if self.tms_job_type_id not in allowed_job_types:
                self.tms_job_type_id = False
        return {
            'domain': {'tms_job_type_id': domain},
        }

    @api.model
    def get_daily_total_working_hour(self, date):
        total = 0.0
        if date:
            daily_working_hour_objs = self.search(
                [('user_id', '=', self._uid), ('date', '=', date)])
            for daily_wh in daily_working_hour_objs:
                if daily_wh.id in self.ids:
                    total += self.duration_hour
                else:
                    total += daily_wh.duration_hour
            total = float_utils.float_round(total, precision_rounding=.001)
        return total

    @api.multi
    @api.depends('date')
    def _get_weekday_day(self):
        for line in self:
            if line.date:
                date = datetime.strptime(line.date, '%Y-%m-%d').date()
                line.weekday = date.strftime("%A")
                line.day = date.strftime("%d")

    @api.multi
    @api.depends('project_id', 'project_id.trobz_partner_id')
    def _get_partner_project_id(self):
        for record in self:
            record.partner_project_id = record.project_id and \
                record.project_id.trobz_partner_id and \
                record.project_id.trobz_partner_id.id or False

    @api.multi
    @api.depends('date', 'user_id', 'user_id.employee_id')
    def _get_partner_resource_id(self):
        dedicated_contract_env = self.env['hr.dedicated.resource.contract']
        for wh in self:
            employee = wh.user_id.employee_id or False
            if employee and wh.date:
                dedicated_contracts = dedicated_contract_env.search(
                    [('employee_id', '=', employee.id),
                        ('start_date', '<=', wh.date),
                        "|", ('end_date', '>=',
                              wh.date), ('end_date', '=', False)
                     ])
                for dedicated_contract in dedicated_contracts:
                    wh.partner_resource_id = dedicated_contract.name and \
                        dedicated_contract.name.id or False

    @api.multi
    @api.depends('tms_forge_ticket_id', 'user_id', 'duration_hour')
    def _get_fixing_time_working_hour(self):
        config_env = self.env['ir.config_parameter']
        fc_profile_name = config_env.get_param(
            'fc_profile_name', "('test1', 'test2')")
        for record in self:
            if record.tms_forge_ticket_id and \
                record.tms_forge_ticket_id.completion_sprint_date and \
                record.user_id.group_profile_id and \
                (record.user_id.group_profile_id.name in (
                    'Technical '
                    'Consultant',
                    'Technical Project Manager') or
                 (record.user_id.group_profile_id.name in eval(
                     fc_profile_name) and
                  record.tms_forge_ticket_id.reopening_times > 0)
                 ):
                record.is_fixing_time_ticket = True

    @api.model
    def _get_default_name(self):
        result = False
        context = self._context and self._context.copy() or {}
        if context.get('tms_forge_ticket_id', False):
            ticket = self.env['tms.forge.ticket'].browse(
                context['tms_forge_ticket_id'])
            return 'Forge ' + \
                str(context['tms_forge_ticket_id']) + \
                ': ' + (ticket.summary or '')
        if context.get('tms_support_ticket_id', False):
            ticket = self.env['tms.support.ticket'].browse(
                context['tms_support_ticket_id'])
            return 'Support ' + \
                str(context['tms_support_ticket_id']) + \
                ': ' + (ticket.summary or '')
        return result

    @api.multi
    @api.depends('user_id', 'date',
                 'partner_resource_id', 'project_id',
                 'project_id.trobz_partner_id')
    def _get_partner_computed(self):
        """
         IF
             there is an on-going Dedicated Resource Contract for
             the user of the working hours THEN the Partner of
             the Dedicated Resource Contract
         ELSE
             Partner of the Project of the Working Hours
        """
        # Use this field for the security rule
        # must call clear_cache to make the rule worked correctly
        self.env['ir.rule'].sudo().clear_cache()

        contract_obj = self.env['hr.dedicated.resource.contract']
        for wh in self:
            contract = contract_obj.search(
                [('employee_id.user_id', '=', wh.user_id.id),
                 ('start_date', '<=', wh.date),
                 '|', ('end_date', '=', False),
                 ('end_date', '>=', wh.date)], order='start_date DESC'
            )
            if contract:
                wh.partner_computed_id = contract[0].name and \
                    contract[0].name.id or False
            else:
                wh.partner_computed_id = wh.project_id and \
                    wh.project_id.trobz_partner_id and \
                    wh.project_id.trobz_partner_id.id or False

    @api.multi
    @api.depends('date')
    def _compute_sprint(self):
        sprint_env = self.env['daily.mail.notification']
        for working in self:
            working.sprint = sprint_env.get_sprint_by_date(working.date)

    # Columns
    wip_start = fields.Datetime(
        string="WIP Start",
        related='tms_forge_ticket_id.wip_start')
    date = fields.Date('Date', required=True,
                       default=lambda self: time.strftime('%Y-%m-%d'))
    user_id = fields.Many2one(
        comodel_name='res.users', string='User',
        default=lambda self: self._uid,
        domain=[('share', '=', False)],
        )
    tms_support_ticket_id = fields.Many2one(
        comodel_name='tms.support.ticket', string='Support Ticket',
        default=lambda self: self._context.get(
            'tms_support_ticket_id', False)
    )
    tms_forge_ticket_id = fields.Many2one(
        comodel_name='tms.forge.ticket', string='Forge Ticket',
        default=lambda self: self._context.get(
            'tms_forge_ticket_id', False)
    )
    sprint = fields.Date(
        string='Sprint',
        compute='_compute_sprint',
        store=True,
    )
    name = fields.Char(
        'Description', size=256, required=True,
        default=_get_default_name,
    )
    tms_activity_id = fields.Many2one(
        comodel_name='tms.activity', string='Activity', required=True,
        default=lambda self: self._context.get('tms_activity_id', False)
    )
    duration_hour = fields.Float('Duration (hours)', required=True)
    daily_total = fields.Float(
        'Daily total', help='Total working hours already input', readonly=True)

    # For the group by analysis
    project_id = fields.Many2one('tms.project', 'Project')
    account_id = fields.Many2one(
        'account.analytic.account', 'Analytic Account')
    analytic_secondaxis_id = fields.Many2one(
        'analytic.secondaxis', 'Analytic Second Axis')
    is_billable = fields.Boolean('Billable')

    weekday = fields.Char(
        compute='_get_weekday_day', string='Weekday', store=True
    )

    day = fields.Char(
        compute='_get_weekday_day', string='Day', store=True
    )

    # F#25802
    # This is temporatory fix for this ticket.
    # I put readonly for this field to make sure that this field won't be set
    # value.
    # the root cause isn't found.
    department_id = fields.Many2one(
        comodel_name='hr.department',
        related='user_id.employee_id.department_id',
        string='Department',
        store=True,
        readonly=True
    )

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        related='user_id.employee_id',
        string='Employee', store=True)

    manager_id = fields.Many2one(
        comodel_name='hr.employee',
        related='user_id.employee_id.parent_id',
        string='Manager',
        store=True)

    partner_project_id = fields.Many2one(
        comodel_name='res.partner',
        compute='_get_partner_project_id',
        string='Partner Project', store=True
    )

    support_type = fields.Selection(
        selection=SUPPORT_TYPE, help=SUPPORT_TYPE_HELP,
        string='Support Type', required=True
    )

    dev_type = fields.Selection(
        selection=DEV_TYPE, help=DEV_TYPE_HELP,
        string="Dev Type", required=True
    )

    partner_resource_id = fields.Many2one(
        compute='_get_partner_resource_id',
        comodel_name="res.partner",
        string="Partner Resource",
        store=True
    )

    # This field is to know the duration hour is to fix a ticket
    is_fixing_time_ticket = fields.Boolean(
        compute='_get_fixing_time_working_hour',
        string="The time spent to fix ticket", store=True
    )
    activity_owner_id = fields.Many2one(
        comodel_name='res.users',
        related='tms_activity_id.owner_id',
        string="Activity's Owner", store=True
    )

    partner_computed_id = fields.Many2one(
        'res.partner', 'Partner Computed',
        compute="_get_partner_computed", store=True)

    proj_owner_id = fields.Many2one(
        related='project_id.owner_id',
        string="Project's Owner",
        store=True
    )
    team_id = fields.Many2one(string='Team', related='project_id.team_id',
                              store=True)
    team_manager_id = fields.Many2one(
        string="Team Manager", related='project_id.team_id.team_manager',
        store=True)
    job_id = fields.Many2one(string='Job', related='employee_id.job_id',
                             store=True)
    job_type_id = fields.Many2one(string='User Job Type',
                                  related='employee_id.job_id.job_type_id',
                                  store=True)
    tms_job_type_id = fields.Many2one(
        comodel_name="tms.job.type",
        string="Job Type",
        default=lambda self: self.env.user and
        self.env.user.default_job_type_id or
        self.env['tms.job.type']
    )
    hr_holiday_line_id = fields.Many2one(
        comodel_name="hr.holidays.line",
        string="Holiday Line",
    )

    @api.multi
    def _check_support_type(self):
        """
        NOT allow to create a Working Hours on an Activity
        with the Analytic Second Axis
        `Support (Defect, Functional Support and Evolution Analysis)`
        if the working hour related to a forge ticket.
        """
        for wh in self:
            support = wh.tms_forge_ticket_id \
                and wh.tms_forge_ticket_id.tms_support_ticket_id or False
            if support and (support.ticket_type == "evolution") \
                    and wh.tms_activity_id.analytic_secondaxis_id \
                    and wh.tms_activity_id.analytic_secondaxis_id.code \
                    == 'support':
                return False
        return True

    _constraints = [
        (_check_support_type,
         'You cannot input working hours the implementation of a forge ticket'
         'related directly or indirectly to a support ticket of'
         'type Evolutions on an Activity with the Analytic Second Axis'
         '"Support (Defect, Functional Support and Evolution Analysis)".'
         '"Related Indirectly" means through the Parent Forge Ticket of'
         'the current Forge Ticket. You should create your Working Hours'
         'on an Activity with the Analytic Second Axis "Evolutions"'
         'or "Dedicated Resource Contract"',
         ['tms_support_ticket_id']),
    ]

    @api.model
    def _add_activity_info(self, vals):
        if 'tms_activity_id' in vals:
            activity = self.env['tms.activity'].browse(
                vals['tms_activity_id'])
            vals['project_id'] = activity.project_id and \
                activity.project_id.id or False
            vals['account_id'] = activity.account_id and \
                activity.account_id.id or False
            vals['analytic_secondaxis_id'] = activity.analytic_secondaxis_id \
                and activity.analytic_secondaxis_id.id or False
            vals['is_billable'] = activity.is_billable
        return vals

    @api.multi
    def calculate_support_type(self, vals):
        # get object pool references
        context = self._context.copy()
        users_env = self.env['res.users']
        user_id = vals.get('user_id', self._uid)
        user_obj = users_env.browse(user_id)
        wh_tickets_required = \
            user_obj and user_obj.group_profile_id \
            and user_obj.group_profile_id.wh_tickets_required or False

        # only force activity_id exist in create or write method
        if not vals.get('tms_activity_id', False)\
                and not context.get('on_change_working_hour', False):
            raise Warning('Warning!', 'You must input an activity')

        # 5956, Measure the time spent per support type
        activity_env = self.env['tms.activity']
        activity_obj = activity_env.browse(vals['tms_activity_id'])
        if len(self) < 1:
            if not (vals.get('tms_support_ticket_id', False) or
                    vals.get('tms_forge_ticket_id', False)):
                if activity_obj\
                        and activity_obj.working_hours_requires_ticket \
                        and not context.get('on_change_working_hour', False) \
                        and wh_tickets_required:
                    raise Warning(
                        'Warning!',
                        'You must input a ticket (support or forge)'
                        ' for the time spent on this activity'
                    )
                else:
                    vals.update(
                        {'support_type': 'support_functional_consultant'})

            if vals.get('tms_forge_ticket_id', False):
                # Auto get support ticket, support type based on selected
                # forge ticket on working hour
                forge_env = self.env['tms.forge.ticket']
                forge_ticket = forge_env.browse(vals['tms_forge_ticket_id'])
                support_ticket = forge_ticket \
                    and forge_ticket.tms_support_ticket_id \
                    and forge_ticket.tms_support_ticket_id or False
                parent_support_ticket = False
                if forge_ticket.parent_forge_ticket_id:
                    parent_forge = forge_ticket.parent_forge_ticket_id
                    parent_support_ticket = parent_forge.tms_support_ticket_id \
                        or False
                if support_ticket:
                    vals.update({
                        'tms_support_ticket_id': support_ticket.id,
                        'support_type': support_ticket.ticket_type})
                elif not support_ticket and parent_support_ticket:
                    # F#11306 Support type on working hours needs to take into
                    # account the case of working hours on a child ticket for
                    # which the parent is associated to a support ticket.
                    # If the child ticket is not associated to a support
                    # ticket, it must get the support ticket of the parent
                    # forge ticket.
                    vals.update({
                        'tms_support_ticket_id': parent_support_ticket.id,
                        'support_type': parent_support_ticket.ticket_type or
                        'no_support'})
                else:
                    # no support ticket and no parent support ticket
                    vals.update(support_type='no_support')

            if vals.get('tms_support_ticket_id', False):
                # Auto get forge ticket, support type based on
                # selected support ticket on working hour
                support_env = self.env['tms.support.ticket']
                support_ticket = support_env.browse(
                    vals['tms_support_ticket_id'])
                vals.update({
                    'support_type': support_ticket and
                    support_ticket.ticket_type or False
                })
                if not vals.get('tms_forge_ticket_id', False):
                    vals['tms_forge_ticket_id'] = support_ticket \
                        and support_ticket.tms_forge_ticket_id \
                        and support_ticket.tms_forge_ticket_id.id or False

            return vals
        else:
            for wh in self:
                # Check new value in vals instead vals.get() to make sure if
                # field is not updated, final value will keep previous value
                support_final_id = wh.tms_support_ticket_id.id
                forge_final_id = wh.tms_forge_ticket_id.id
                if 'tms_support_ticket_id 'in vals and \
                        vals['tms_support_ticket_id']:
                    support_final_id = vals['tms_support_ticket_id']
                if 'tms_forge_ticket_id 'in vals and \
                        vals['tms_forge_ticket_id']:
                    forge_final_id = vals['tms_forge_ticket_id']
                if not support_final_id and not forge_final_id:
                    if activity_obj\
                            and activity_obj.working_hours_requires_ticket \
                            and not context.get('on_change_working_hour') \
                            and wh_tickets_required:
                        raise Warning(
                            'Warning!',
                            'You must input a ticket (support or forge)'
                            ' for the time spent on this activity'
                        )
                    else:
                        vals.update(
                            {'support_type': 'support_functional_consultant'})

                if forge_final_id and 'tms_forge_ticket_id' in vals:
                    # Auto get support ticket, support type based on selected
                    # forge ticket on working hour
                    forge_env = self.env['tms.forge.ticket']
                    forge_ticket = forge_env.browse(
                        vals['tms_forge_ticket_id'])
                    support_ticket = forge_ticket \
                        and forge_ticket.tms_support_ticket_id \
                        and forge_ticket.tms_support_ticket_id or False
                    parent_support_ticket = False
                    if forge_ticket.parent_forge_ticket_id:
                        parent_forge = forge_ticket.parent_forge_ticket_id
                        parent_support_ticket = \
                            parent_forge.tms_support_ticket_id or False
                    if support_ticket:
                        vals.update({
                            'tms_support_ticket_id': support_ticket.id,
                            'support_type': support_ticket.ticket_type})
                    elif not support_ticket and parent_support_ticket:
                        # F#11306 Support type on working hours needs to take
                        # into account the case of working hours on a
                        # child ticket for which the parent is associated to
                        # a support ticket.
                        # If the child ticket is not associated to a
                        # support ticket,
                        # it must get the support ticket of the
                        # parent forge ticket.
                        vals.update({
                            'tms_support_ticket_id': parent_support_ticket.id,
                            'support_type': parent_support_ticket.ticket_type or
                            'no_support'})
                    else:
                        # no support ticket and no parent support ticket
                        vals.update(support_type='no_support')

                elif support_final_id and 'tms_support_ticket_id' in vals:
                    # Auto get forge ticket, support type based on
                    # selected support ticket on working hour
                    support_env = self.env['tms.support.ticket']
                    support_ticket = support_env.browse(support_final_id)
                    vals.update({
                        'support_type': support_ticket and
                        support_ticket.ticket_type or False
                    })
                    if not vals.get('tms_forge_ticket_id', False):
                        vals['tms_forge_ticket_id'] = support_ticket \
                            and support_ticket.tms_forge_ticket_id \
                            and support_ticket.tms_forge_ticket_id.id or False
            return vals

    @api.onchange('tms_activity_id', 'user_id',
                  'tms_forge_ticket_id', 'tms_support_ticket_id')
    def onchange_to_calculate_support_dev_type(self):
        ctx = self._context and self._context.copy() or {}
        vals = {
            'tms_activity_id': self.tms_activity_id and
            self.tms_activity_id.id or False,
            'user_id': self.user_id and self.user_id.id or False}
        if self.tms_forge_ticket_id:
            vals.update({'tms_forge_ticket_id': self.tms_forge_ticket_id.id})
        elif self.tms_support_ticket_id:
            vals.update(
                {'tms_support_ticket_id': self.tms_support_ticket_id.id})
        ctx.update({'on_change_working_hour': 1})
        # get dev_type
        vals = self.with_context(ctx).calculate_support_type(vals)
        self.dev_type = self.with_context(ctx).calculate_dev_type(vals)
        self.support_type = vals.get('support_type', False)

    @api.multi
    def get_support_forge_id(self, input_vals):
        forge_env = self.env['tms.forge.ticket']
        support_env = self.env['tms.support.ticket']
        vals = deepcopy(input_vals)
        if 'tms_forge_ticket_id' in vals and \
                vals.get('tms_forge_ticket_id', False):
            forge_ticket = forge_env.browse(vals['tms_forge_ticket_id'])
            support_ticket = forge_ticket and \
                forge_ticket.tms_support_ticket_id or False
            vals.update(
                {'support_type': support_ticket and
                 support_ticket.ticket_type or 'no_support'})
            if not vals.get('tms_support_ticket_id', False):
                vals.update(
                    {'tms_support_ticket_id': support_ticket and
                     support_ticket.id or False})

        elif 'tms_support_ticket_id' in vals and \
                vals.get('tms_support_ticket_id', False):
            support_ticket = support_env.browse(vals['tms_support_ticket_id'])
            vals.update(
                {'support_type': support_ticket and
                 support_ticket.ticket_type or False})
            if not vals.get('tms_forge_ticket_id', False):
                vals['tms_forge_ticket_id'] = support_ticket and \
                    support_ticket.tms_forge_ticket_id\
                    and support_ticket.tms_forge_ticket_id.id or False

        elif 'tms_support_ticket_id' not in vals and \
                'tms_forge_ticket_id' not in vals:
            vals.update({
                'tms_support_ticket_id': self.tms_support_ticket_id and
                self.tms_support_ticket_id.id or False,
                'tms_forge_ticket_id': self.tms_forge_ticket_id and
                self.tms_forge_ticket_id.id or False,
            })
        return vals

    @api.model
    def calculate_dev_type(self, vals):
        # openerp & dev department
        dev_deparment_recs = self.env['hr.department'].search(
            [('name', 'in', ('Production', 'Web'))])
        forge_env = self.env['tms.forge.ticket']
        hr_employee_env = self.env['hr.employee']
        user_id = vals.get('user_id', False)

        employees = hr_employee_env.search(
            [('user_id', '=', user_id)])
        department_id = employees and employees[0].department_id and \
            employees[0].department_id.id or False
        forge_id = vals.get('tms_forge_ticket_id', False)
        dev_type = 'other'
        if forge_id and department_id:
            forge_obj = forge_env.browse(forge_id)
            if department_id in dev_deparment_recs.ids:
                if forge_obj.reopening_times == 0:
                    dev_type = 'new_feature'
                else:
                    dev_type = 'fixing'
            else:
                if forge_obj.state == 'in_qa':
                    dev_type = 'qa'
                else:
                    dev_type = 'other'

        return dev_type

    @api.model
    def _check_access_rights(self, wh_user_id=None):
        sudo_permission = self._context.get('sudo', False)
        if sudo_permission:
            return True
        current_user = self.env['res.users'].browse(self._uid)

        wh_user_id = wh_user_id or self.user_id.id

        return current_user.id == wh_user_id \
            or current_user.has_group('base.group_hr_manager') \
            or current_user.has_group(
                'tms_modules.group_profile_tms_delivery_team_manager')

    # TODO: Only some users can add working hours to support tickets
    @api.model
    def create(self, vals):
        if 'duration_hour' in vals and vals['duration_hour'] == 0.00:
            raise Warning(
                'Forbidden action!',
                'You must set a duration for the time spent.')

        vals = self._add_activity_info(vals)
        # If We create working hour for leave request, it'll ignore check
        # calculate_dev_type and calculate_dev_type

        vals = self.calculate_support_type(vals)
        vals['dev_type'] = self.calculate_dev_type(vals)
        if not self._check_access_rights(vals['user_id']):
            raise Warning(
                'Warning!',
                "You aren't allowed to create working hour for this user.")

        if 'name' in vals:
            field_val = re.sub(r'[\x00-\x1F]', '', vals['name'])
            vals['name'] = field_val

        return super(tms_working_hour, self).create(vals)

    @api.multi
    def write(self, vals):
        vals = self._add_activity_info(vals)

        for wh_obj in self:
            if not wh_obj._check_access_rights():
                raise Warning(
                    'Warning!',
                    "You aren't allowed to edit this user's working hour.")

        if 'name' in vals:
            field_val = re.sub(r'[\x00-\x1F]', '', vals['name'])
            vals['name'] = field_val

        if 'tms_support_ticket_id' in vals or \
            'tms_forge_ticket_id' in vals or \
                'tms_activity_id' in vals or 'user_id' in vals:
            for wh_obj in self:
                write_vals = deepcopy(vals)
                new_vals = {
                    'tms_activity_id': vals.get(
                        'tms_activity_id',
                        wh_obj.tms_activity_id and
                        wh_obj.tms_activity_id.id or False),

                    'user_id': vals.get('user_id', wh_obj.user_id and
                                        wh_obj.user_id.id or False),
                }
                new_vals.update(
                    wh_obj.get_support_forge_id(vals))

                new_vals = self.calculate_support_type(new_vals)

                if 'support_type' in vals:
                    write_vals[
                        'support_type'] = new_vals.get('support_type', False)
                if 'tms_support_ticket_id' in vals:
                    write_vals[
                        'tms_support_ticket_id'] = new_vals.get(
                            'tms_support_ticket_id', False)
                if 'tms_forge_ticket_id' in vals:
                    write_vals[
                        'tms_forge_ticket_id'] = new_vals.get(
                            'tms_forge_ticket_id', False)
                if 'dev_type' in vals:
                    write_vals['dev_type'] = self.calculate_dev_type(new_vals)
                super(tms_working_hour, wh_obj).write(write_vals)
        else:
            super(tms_working_hour, self).write(vals)
        return True

    @api.multi
    def unlink(self):
        for wh_obj in self:
            if not wh_obj._check_access_rights():
                raise Warning(
                    'Warning!',
                    "You aren't allowed to delete this user's working hour")
            super(tms_working_hour, wh_obj).unlink()
        return True

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):

        # call default sort on super
        result = super(tms_working_hour, self).read_group(
            domain=domain, fields=fields, groupby=groupby, lazy=lazy,
            offset=offset, limit=limit, orderby=orderby
        )

        # sort reversely by Sprint (sprint)
        if result and result[0].get("sprint"):
            result = sorted(
                result,
                key=lambda k: k["sprint"][0],
                reverse=True)

        # sort reversely by Month-year (date)
        if result and result[0].get("date"):
            month_mapping = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12,
            }

            def month_year_sort(_item):
                opearand = _item.get("date").split(' ')
                year_item = opearand[1]
                month_item = opearand[0].lower().strip()
                return year_item, month_mapping.get(month_item)

            result = sorted(result, key=month_year_sort, reverse=True)

        # sort reversely by Date (day)
        if result and result[0].get("day"):
            result = sorted(result, key=lambda k: k["day"], reverse=True)

        # sort reversely by Weekday (Friday, Thursday, Wednesday, Tuesday,
        # Monday, Sunday, Saturday)
        if result and result[0].get("weekday"):
            weekday_mapping = {
                "saturday": 1, 'sunday': 2, 'monday': 3, 'tuesday': 4,
                'wednesday': 5, 'thursday': 6, 'friday': 7,
            }

            def week_day_sort(_item):
                weekday = _item.get("weekday")
                if weekday:
                    weekday = weekday.lower()
                return weekday_mapping.get(weekday)
            result = sorted(result, key=week_day_sort, reverse=True)

        return result
