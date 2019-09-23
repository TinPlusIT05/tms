# -*- encoding: utf-8 -*-
from openerp import api, models, fields
import datetime


class tms_milestone(models.Model):

    _name = "tms.milestone"
    _inherit = ['mail.thread']
    _description = "Milestone"
    _order = "name"

    milestone_open_status = ['planned', 'development', 'deployment']

    @api.depends('forge_ticket_ids.development_time',
                 'forge_ticket_ids.remaining_time',
                 'forge_ticket_ids.time_spent')
    def _compute_forge_indicators(self):
        forge_ticket_env = self.env['tms.forge.ticket']
        for milestone in self:
            indicators = forge_ticket_env.get_forge_indicators(
                [('milestone_id', '=', milestone.id)])
            milestone.remaining_time = indicators['remaining']
            milestone.progress = indicators['progress']

    @api.depends('forge_ticket_ids.development_time',
                 'support_ticket_ids.workload_char')
    def _compute_workload_estimate(self):
        for milestone in self:
            sum_workload_support = sum(
                map(float, milestone.support_ticket_ids.mapped(
                    'workload_char')))
            forge_tikets = milestone.forge_ticket_ids.filtered(
                lambda f: not f.tms_support_ticket_id)
            sum_estimate_forge = sum(
                forge_tikets.mapped('development_time')) / 8
            milestone.workload = sum_workload_support + sum_estimate_forge

    @api.depends('forge_ticket_ids.time_spent',
                 'support_ticket_ids.time_spent_day')
    def _compute_time_spent(self):
        for milestone in self:
            sum_time_spent_support = sum(
                milestone.support_ticket_ids.mapped('time_spent_day'))
            forge_tikets = milestone.forge_ticket_ids.filtered(
                lambda f: not f.tms_support_ticket_id)
            sum_time_spent_forge = sum(
                forge_tikets.mapped('time_spent')) / 8
            milestone.time_spent = sum_time_spent_forge +\
                sum_time_spent_support

    # Columns
    is_main_milestone = fields.Boolean(
        string="Main Development Milestone")
    project_id = fields.Many2one(
        'tms.project', 'Project name',
        required=True,
        track_visibility='onchange',
        default=lambda self: self._context.get('project_id', False)
    )
    name = fields.Char('Name', size=256, readonly=True)
    number = fields.Char(
        'Milestone Number', size=30, required=True,
        help='ex: 4.2', track_visibility='onchange')
    description = fields.Char(
        'Short Description', size=256,
        track_visibility='onchange')
    # TODO:LOW The display with the widget = text_html does not work
    note = fields.Text(
        'Delivery Note',
        help='To be sent to the customer when the delivery becomes "official".'
    )
    deliveries = fields.One2many(
        comodel_name='tms.delivery',
        inverse_name='milestone_id',
        string='Deliveries', groups='base.group_user'
    )
    state = fields.Selection(
        [('planned', 'Planned'),
         ('development', 'Development'),
         ('deployment', 'Deployment'),
         ('production', 'Production'),
         ('done', 'Done')],
        'Status', required=True,
        track_visibility='onchange'
    )
    remaining_time = fields.Float(
        compute='_compute_forge_indicators',
        string='Remaining time', store=True)
    progress = fields.Float(
        compute='_compute_forge_indicators',
        string='Progress', store=True)

    date = fields.Date(
        'Date',
        help='Only set this date if there is a ' +
        'strong commitment with the customer.',
        track_visibility='onchange')
    forge_ticket_ids = fields.One2many(
        comodel_name='tms.forge.ticket',
        inverse_name='milestone_id',
        string='Forge Tickets',
    )
    support_ticket_ids = fields.One2many(
        comodel_name='tms.support.ticket',
        inverse_name='milestone_id',
        string='Support Tickets'
    )
    active = fields.Boolean(
        'Active', track_visibility='onchange', default=True,
        help='This field is set automatically based' +
        ' on the status of the milestone.')
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
    release_dates = fields.Char(
        'Release Dates',
        help='Dates when this milestone has been delivered in Production. '
        'In case of hotfix deliveries, we can have multiple dates')
    workload = fields.Float(
        'Workload estimate', digits=(16, 3),
        compute='_compute_workload_estimate', store=True
    )
    time_spent = fields.Float(
        compute='_compute_time_spent', store=True,
        string='Time Spent', help='In days'
    )

    show_release_notes = fields.Boolean(
        string="Show in Release Notes", default=True)

    _sql_constraints = [('milestone_unique', 'unique (name)',
                         'This milestone already exists!')]

    @api.model
    def _get_neighbour_milestone(self, is_get_next, project_id):
        """
        Get previous or next milestone
        based on a specific milestone of a project
        """
        domain = [("project_id", "=", project_id)]
        order = "number ASC"
        milestones = False
        if self:
            milestone_number = self.number
            if is_get_next:
                domain.append(("number", ">", milestone_number))
            else:
                # override the order
                order = "number DESC"
                domain.append(("number", "<", milestone_number))
            milestones = self.search(domain, limit=1, order=order)
        return milestones and milestones[0].id or False

    @api.model
    def get_next_milestone(self, project_id):
        return self._get_neighbour_milestone(True, project_id)

    @api.model
    def get_previous_milestone(self, project_id):
        return self._get_neighbour_milestone(False, project_id)

    @api.multi
    def count_close_forge_ticket(self):
        forge_env = self.env['tms.forge.ticket']
        args = [('state', '=', 'closed'), ('milestone_id', 'in', self.ids)]
        res = forge_env.search(args)
        return res and len(res) or 0

    @api.multi
    def count_all_forge_ticket(self):
        forge_env = self.env['tms.forge.ticket']
        args = [('milestone_id', 'in', self.ids)]
        res = forge_env.search(args)
        return res and len(res) or 0

    @api.multi
    def name_get(self):
        if not self:
            return []
        result = []
        # This is to avoid the case that this function is called with sudo.
        uid = self._context.get('uid', self._uid)
        current_user = self.env['res.users'].browse(uid)

        for milestone in self:
            # Deadline of this milestone
            suffix = milestone.date and ' - %s' % milestone.date or ''
            # The status of this milestone: planned, development, deployment...
            suffix += ' - %s' % milestone.state
            if current_user.is_trobz_member:  # If current user is of Trobz
                # Display the statistics of forge tickets
                num_close_ticket = milestone.count_close_forge_ticket()
                num_all_ticket = milestone.count_all_forge_ticket()
                suffix += ' (%s/%s)' % (num_close_ticket, num_all_ticket)
            result.append((
                milestone.id,
                '%s %s %s' % (milestone.project_id.name,
                              milestone.number,
                              suffix)))
        return result

    @api.multi
    def button_prepare_release_notes(self):
        general_content = ""
        forge_content = ""
        for f in self.forge_ticket_ids.filtered(
                lambda f: not f.tms_support_ticket_id):
            forge_content += '* [F#%s](https://tms.trobz.com/web?#id=%s' %\
                (f.name, f.id) + '&view_type=form&' +\
                'model=tms.forge.ticket&action=257): %s\n' % f.summary
        func_blocks = {}
        for sp in self.support_ticket_ids.sorted(
                key=lambda sp: sp.tms_functional_block_id.name):
            if sp.tms_functional_block_id and \
                    sp.tms_functional_block_id.name not in func_blocks.keys():
                func_blocks[sp.tms_functional_block_id.name] = \
                    '* [S#%s](https://tms.trobz.com/web?#id=%s' %\
                    (sp.name, sp.id) + '&view_type=form&' +\
                    'model=tms.support.ticket&action=284): %s\n' % sp.summary
            elif sp.tms_functional_block_id and \
                    sp.tms_functional_block_id.name in func_blocks.keys():
                func_blocks[sp.tms_functional_block_id.name] += \
                    '* [S#%s](https://tms.trobz.com/web?#id=%s' %\
                    (sp.name, sp.id) + '&view_type=form&' +\
                    'model=tms.support.ticket&action=284): %s\n' % sp.summary
            elif 'Unknown' in func_blocks.keys():
                func_blocks['Unknown'] += \
                    '* [S#%s](https://tms.trobz.com/web?#id=%s' %\
                    (sp.name, sp.id) + '&view_type=form&' +\
                    'model=tms.support.ticket&action=284): %s\n' % sp.summary
            else:
                func_blocks['Unknown'] = \
                    '* [S#%s](https://tms.trobz.com/web?#id=%s' %\
                    (sp.name, sp.id) + '&view_type=form&' +\
                    'model=tms.support.ticket&action=284): %s\n' % sp.summary

        if func_blocks:
            # sort functional blocks by alphabet
            for key in sorted(func_blocks):
                general_content += \
                    '\n### %s\n%s' % (key, func_blocks[key])

        if forge_content:
            general_content += \
                '\n### Technical Activities:\n%s' % forge_content
        self.note = general_content

    @api.model
    def create(self, vals):
        if vals.get('project_id', False) and vals.get('number', False):
            project = self.env['tms.project'].browse(vals['project_id'])
            vals['name'] = '%s %s' % (project.name, vals['number'])

        if 'state' in vals:
            vals['active'] = True
            if vals['state'] in ['development', 'deployment']:
                prev_main_milestones = self.search(
                    [('project_id', '=', project.id),
                     ('state', 'in', ['development', 'deployment']),
                     ('is_main_milestone', '=', 'True')])
                if prev_main_milestones:
                    for prev_main_milestone in prev_main_milestones:
                        if vals['number'] > prev_main_milestone.number:
                            vals['is_main_milestone'] = True
                            prev_main_milestone.is_main_milestone = False
                else:
                    vals['is_main_milestone'] = True
            elif vals['state'] == 'done':
                vals['active'] = False

        return super(tms_milestone, self).create(vals)

    @api.model
    def update_main_milestone(self, milestone, milestone_number, project_id,
                              milestone_state):
        if milestone_state in ['development', 'deployment']:
            prev_main_milestones = self.search(
                [('project_id', '=', project_id),
                 ('state', 'in', ['development', 'deployment']),
                 ('is_main_milestone', '=', 'True')])
            if prev_main_milestones:
                for prev_main_milestone in prev_main_milestones:
                    if milestone_number > prev_main_milestone.number:
                        milestone.is_main_milestone = True
                        prev_main_milestone.is_main_milestone = False
            else:
                milestone.is_main_milestone = True
        else:
            prev_main_milestone = self.search(
                [('id', '!=', milestone.id),
                 ('project_id', '=', project_id),
                 ('state', 'in', ['development', 'deployment'])],
                order="number desc", limit=1)
            milestone.is_main_milestone = False
            if prev_main_milestone:
                prev_main_milestone.is_main_milestone = True
        return True

    @api.multi
    def write(self, vals):
        project_env = self.env['tms.project']
        for milestone in self:
            if 'number' in vals or 'project_id' in vals:
                project_name = milestone.project_id.name
                number = milestone.number
                if 'project_id' in vals:
                    project_name = project_env.browse(
                        vals['project_id']).name
                if 'number' in vals:
                    number = vals['number']
                vals['name'] = '%s %s' % (project_name, number)
            if 'state' in vals:
                if vals['state'] == 'done':
                    vals['active'] = False
                else:
                    vals['active'] = True
                milestone.update_main_milestone(milestone,
                                                milestone.number,
                                                milestone.project_id.id,
                                                vals['state'])
            return super(tms_milestone, milestone).write(vals)

    @api.model
    def get_commitment_milestones(self):
        # Get object pool references
        config_pool = self.env["ir.config_parameter"]

        # Get a list of milestones
        milestone_domain = [('date', '!=', False),
                            ('state', 'not in', ["done", "production"])]
        milestones = self.search(milestone_domain, order='date asc')

        # Return text to indicates no milestone found
        if not milestones:
            return 'No milestone'

        # prepare table template for milestone display
        table_template = u"""
            <table border="1" style="border-collapse: collapse;">
                <tr style="background: #DDD;">
                    <th style="padding:5px 10px;">Milestone</th>
                    <th style="padding:5px 10px;">Date</th>
                    <th style="padding:5px 10px;">Progress (%)</th>
                    <th style="padding:5px 10px;">Remaining (h)</th>
                    <th style="padding:5px 10px;">Short Description</th>
                </tr>
                {0}
            </table>
        """
        table_row_template = u"""
            <tr style='color:{0};'>
                <td style="padding:5px 10px; text-align: left;">
                    <a href="{1}">{2}</a>
                </td>
                <td style="padding:5px 10px; text-align: center;">{3}</td>
                <td style="padding:5px 10px; text-align: center;">{4}%</td>
                <td style="padding:5px 10px; text-align: center;">{5}</td>
                <td style="padding:5px 10px; text-align: center;">{6}</td>
            </tr>
        """

        # Prepare the link to access milestone on TMS
        link_template = u"{0}#id={1}&view_type=form&model=tms.milestone"
        conf_val = config_pool.get_param(
            key="web.base.url",
            default="https://tms.trobz.com")
        if not conf_val:
            conf_val = "https://tms.trobz.com"
        base_url = conf_val + '/web?db=%s' % self._cr.dbname
        # List to store each composed row data
        row_results = []

        for mile in milestones:
            # Get the link and title of milestone to polulate on the table as
            # link
            link, title = link_template.\
                format(base_url, str(mile.id)), str(mile.name)

            # Get milestone's Date and Progress
            date, progress = mile.date, u"{:0.02f}".format(mile.progress)

            # Get milestone's Remaining (h) and Short Description
            remaining, description = mile.remaining_time, mile.description

            # check if milestone should not reach 100%
            _not_completed = mile.progress not in (100, 100.0)

            # Indicate the text color for milestone based on the Date
            # (commitment date late)
            color = mile.date < str(datetime.date.today()) and\
                _not_completed and "#F00" or "#222"

            # Compose arguments
            func_arguments = color, link, title, date,\
                progress, remaining, description

            # Compose row rendered data
            composed_row = table_row_template.format(*func_arguments)

            # Add composed row data to list
            row_results.append(composed_row)

        return table_template.format("".join(row_results))
