# -*- encoding: UTF-8 -*-
from openerp import fields, models, api


class HrTeam(models.Model):
    _inherit = ['mail.thread']
    _name = "hr.team"

    name = fields.Char(
        "Name",
        required=True)
    team_manager = fields.Many2one(
        "hr.employee",
        "Manager",
        required=True)
    members_ids = fields.Many2many(
        comodel_name='hr.employee',
        relation='team_member_rel',
        string='Members'
    )
    number_members = fields.Integer(
        string='Number Members',
        compute='_compute_number_members')
    dtm_workload = fields.Float(
        string='Total DTM Workload (for next month)',
        compute='_compute_dtm_workload')
    daily_capacity = fields.Float(
        string='Daily Capacity',
        compute='_compute_team_capacity')
    three_month_capacity = fields.Float(
        string='Capacity (for 3 months)',
        compute='_compute_team_capacity')
    total_workload = fields.Float(
        string='Total Workload (for next 3 months)',
        compute='_compute_total_workload')
    load = fields.Float(
        string='Load (%)',
        compute='_compute_load')
    number_activities = fields.Integer(
        string='Number of Assigned Activities',
        readonly=True,
        compute='_compute_number_activities',
        help='''Activities that are not "Done"''')
    number_project = fields.Integer(
        string='Projects',
        compute='_compute_number_project')
    number_forge = fields.Integer(
        string='Forge Tickets',
        compute='_compute_number_forge')
    number_support = fields.Integer(
        string='Support Tickets',
        compute='_compute_number_support')

    @api.multi
    def _compute_number_members(self):
        for team in self:
            team.number_members = len(team.members_ids)

    @api.multi
    def _compute_team_capacity(self):
        for team in self:
            team_capacity = 0
            for member in team.members_ids:
                team_capacity += member.current_employee_capacity
            team.daily_capacity = team_capacity / 100
            team.three_month_capacity = team_capacity * 60 / 100

    @api.multi
    def _compute_dtm_workload(self):
        activity_obj = self.env['tms.activity']
        for team in self:
            dtm_activities = activity_obj.search([
                ('owner_id', '=', team.team_manager.user_id.id)
            ])
            dtm_workload = 0
            for activity in dtm_activities:
                dtm_workload += activity.dtm_workload
            team.dtm_workload = dtm_workload

    @api.multi
    def _compute_load(self):
        for team in self:
            team.load = team.three_month_capacity and \
                team.total_workload * 100 / team.three_month_capacity or 0

    @api.multi
    def _compute_number_activities(self):
        activity_obj = self.env['tms.activity']
        for team in self:
            assigned_activities = activity_obj.search_count([
                ('team_id', '=', team.id),
                ('state', 'in', ('planned', 'in_progress'))
            ])
            team.number_activities = assigned_activities

    @api.multi
    def _compute_number_project(self):
        project_obj = self.env['tms.project']
        for team in self:
            num_project = project_obj.search_count([
                ('team_id', '=', team.id),
                ('state', 'in', ('potential', 'active'))
            ])
            team.number_project = num_project

    @api.multi
    def _compute_number_support(self):
        support_obj = self.env['tms.support.ticket']
        for team in self:
            num_support = support_obj.search_count([
                ('team_id', '=', team.id),
                ('state', '!=', 'closed')
            ])
            team.number_support = num_support

    @api.multi
    def _compute_number_forge(self):
        forge_obj = self.env['tms.forge.ticket']
        for team in self:
            num_forge = forge_obj.search_count([
                ('team_id', '=', team.id),
                ('state', '!=', 'closed')
            ])
            team.number_forge = num_forge

    @api.multi
    def _compute_total_workload(self):
        activity_obj = self.env['tms.activity']
        for team in self:
            dev_activities = activity_obj.search([
                ('team_id', '=', team.id)
            ])
            dev_workload = 0
            for activity in dev_activities:
                dev_workload += activity.total_workload
            team.total_workload = dev_workload
