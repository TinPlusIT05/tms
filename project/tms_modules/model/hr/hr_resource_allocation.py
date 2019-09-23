# -*- encoding: UTF-8 -*-
from datetime import datetime, timedelta

from openerp import api, fields
from openerp.modules.registry import RegistryManager
from openerp.addons.booking_chart.mixin import mixin  # @UnresolvedImport
from openerp.exceptions import Warning


class hr_resource_allocation(mixin.resource):

    @api.multi
    @api.depends('employee_id.user_id', 'sprint', 'activity_id')
    def _compute_actual_occupancy(self):
        """
        Actual Occupancy % =
        (time spent in working hours in this sprint
        for this employee and this activity) /
        (40 - 8 * Leave Request Days during this sprint)
        """
        def _get_total_duration_hour(user_id, activity_id, sprint):
            wh_env = self.env['tms.working.hour']
            # Search tms_working_hour_ids
            tms_working_hour_objs = wh_env.search(
                [('user_id', '=', user_id),
                 ('tms_activity_id', '=', activity_id),
                 ('sprint', '=', sprint)]
            )
            # Calculate total hours spent
            total_duration = sum(
                l.duration_hour for l in tms_working_hour_objs)
            return total_duration

        # Search activity `Days off`
        activity_env = self.env['tms.activity']
        days_off_activities = activity_env.search(
            [('name', 'ilike', 'Days Off')])

        for record in self:
            user_id = record.employee_id and \
                record.employee_id.user_id and \
                record.employee_id.user_id.id or False
            sprint_date = record.sprint and record.sprint or False

            # Calculate total working time in this sprint
            total_time_spent = _get_total_duration_hour(
                user_id, record.activity_id.id, sprint_date)

            # Calculate total time of leave requests in this sprint
            if days_off_activities:
                total_time_of_leave_request = _get_total_duration_hour(
                    user_id, days_off_activities[0].id, sprint_date)
            else:
                total_time_of_leave_request = 0

            # Calculate (time spent in working hours in this sprint for this
            # employee and this activity) / (40 - 8 * Leave Request Days during
            # this sprint)
            record.actual_occupancy = float(total_time_spent * 100.0) / \
                (total_time_of_leave_request != 40 and
                 (40 - total_time_of_leave_request) or total_time_spent)

    _name = "hr.resource.allocation"
    _inherit = "mail.thread"
    _order = 'date_from'

    # Columns
    name = fields.Integer(string='Allocation ID', readonly=True)

    employee_id = fields.Many2one(
        comodel_name="hr.employee", string='Employee', required=True,
        track_visibility="onchange"
    )
    activity_id = fields.Many2one(
        comodel_name="tms.activity", string="Activity", required=True,
        track_visibility="onchange"
    )
    date_from = fields.Date(
        string='Date from'
    )
    date_to = fields.Date(
        string='Date to'
    )
    occupancy = fields.Float(
        'Budget Occupancy %', required=True,
        help="The Resource Allocation Budget Occupancy % should be " +
        "calculated as {number of day off during that sprint} * 20%",
        track_visibility="onchange",
        default=100
    )

    # Tab activity
    analytic_second_axis_id = fields.Many2one(
        related='activity_id.analytic_secondaxis_id',
        comodel_name='analytic.secondaxis',
        string="Analytic Second Axis", readonly=True
    )
    project_id = fields.Many2one(
        related='activity_id.project_id',
        comodel_name='tms.project',
        string="Project", readonly=True,
        store=True
    )
    priority = fields.Selection(
        related='activity_id.priority',
        string="Priority",
        readonly=True,
        selection=[('high', 'High'), ('normal', 'Normal'), ('low', 'Low')],
        store=True
    )

    day_remaining = fields.Float(
        related='activity_id.day_remaining',
        string="Remaining time(in days)",
        readonly=True
    )
    delivery_deadline = fields.Date(
        related='activity_id.planned_date',
        string="Delivery Deadline", readonly=True
    )
    completion_forecast = fields.Date(
        related='activity_id.completion_forecast',
        string="Completion Forecast", readonly=True
    )
    description = fields.Text(
        related='activity_id.description',
        string="Description", readonly=True
    )

    is_billable = fields.Boolean(
        related='activity_id.is_billable',
        string="Billable", readonly=True
    )
    employee_department_id = fields.Many2one(
        related='employee_id.department_id',
        comodel_name='hr.department',
        string="Department",
        readonly=True, store=True
    )

    sprint = fields.Date(
        string='Sprint',
        default=lambda self: datetime.today() + timedelta(
            days=(5 - datetime.today().weekday())
        )
    )

    actual_occupancy = fields.Float(
        compute='_compute_actual_occupancy',
        string='Actual Occupancy %',
        help="(Time spent in working hours in this sprint for this" +
        "employee and this activity)100 /" +
        " (40 - 8 * Leave Request Days during this sprint)"
    )
    employee_parent_id = fields.Many2one(
        related='employee_id.parent_id',
        comodel_name='hr.employee',
        string='Manager',
        readonly=True, store=True
    )
    # F#13566
    holiday_id = fields.Many2one(
        comodel_name='hr.holidays.line',
        string='Holidays line',
        readonly=True
    )

    @api.model
    def update_date_from_date_to(self, vals):
        sprint = vals.get('sprint', False)
        if sprint:
            if not isinstance(sprint, str):
                sprint = datetime.strftime(sprint, '%Y-%m-%d')
            date_from = datetime.strptime(sprint, '%Y-%m-%d') + timedelta(
                days=-6)
            vals.update({
                'date_from': date_from,
                'date_to': sprint
            })
        return vals

    @api.multi
    def write(self, vals):
        vals = self.update_date_from_date_to(vals)
        result = super(hr_resource_allocation, self).write(vals)
        return result

    @api.model
    def create(self, vals):
        vals = self.update_date_from_date_to(vals)
        result = super(hr_resource_allocation, self).create(vals)
        # Take the id of the ticket as its name
        update_sql = """
            UPDATE hr_resource_allocation
            SET name = %d
            WHERE id = %d;
        """ % (result, result)
        self._cr.execute(update_sql)
        return result

    @api.model
    def get_sprint(self, sprint, number_iteration):
        lastest_sprint = []
        for n in range(number_iteration):  # @UnusedVariable
            next_sprint = datetime.strptime(sprint, '%Y-%m-%d') + timedelta(
                days=7)
            lastest_sprint.append(next_sprint)
            sprint = next_sprint.strftime('%Y-%m-%d')
        return lastest_sprint

    @api.multi
    def button_extend1week(self):
        vals = {}
        for record in self:
            if not record.sprint:
                raise Warning(
                    "There is no sprint linked to the current resource"
                    " allocation. Please select a sprint before extending.")
            list_sprint = self.get_sprint(record.sprint, 1)
            for sprint in list_sprint:
                vals = {'employee_id': record.employee_id.id,
                        'activity_id': record.activity_id and
                        record.activity_id.id or False,
                        'sprint': sprint,
                        'occupancy': record.occupancy or False}
                self.create(vals)
        return True

    @api.multi
    def button_extend1month(self):
        vals = {}
        for record in self:
            if not record.sprint:
                raise Warning(
                    "There is no sprint linked to the current resource"
                    " allocation. Please select a sprint before extending.")
            list_sprint = self.get_sprint(record.sprint, 4)
            for sprint in list_sprint:
                vals = {'employee_id': record.employee_id and
                        record.employee_id.id,
                        'activity_id': record.activity_id and
                        record.activity_id.id or False,
                        'sprint': sprint,
                        'occupancy': record.occupancy or False}
                self.create(vals)
        return True

    @api.multi
    def copy(self, defaults=None):
        defaults = defaults or {}
        defaults.update({
            'date_from': datetime.strptime(self.sprint, '%Y-%m-%d') - timedelta(days=6),
            'date_to': datetime.strptime(self.sprint, '%Y-%m-%d')
        })
        return super(hr_resource_allocation, self).copy(defaults)

    def _get_name(self, resource_allocation):
        """
        resource_allocation.occupancy_pct
        resource_allocation.activity_id.name
        (use the display name including the project name)
        """
        label = ''
        activity = resource_allocation.activity_id or False
        name = activity and activity.name or False
        project = activity and activity.project_id and \
            activity.project_id.name or False
        occupancy = resource_allocation.occupancy or 0.0

        if name == 'Days Off':
            if resource_allocation.holiday_id:
                date_from = resource_allocation.holiday_id.first_date
                date_to = resource_allocation.holiday_id.last_date
            else:
                date_from = resource_allocation.date_from
                date_to = resource_allocation.date_to
            label = "[%0.2f%%] trobz - %s (%s to %s)" % (
                occupancy, name, date_from, date_to)

        else:
            label = '[%0.2f%%] %s - %s' % (occupancy, project, name)
        return label

    def _get_hr_employee_id(self, resource_allocation):
        return 'hr.employee,%s' %\
            (resource_allocation.employee_id and
             resource_allocation.employee_id.id or False)

    def _get_description(self, resource_allocation):
        """
        Time Sold for dev: resource_allocation.day_sold_dev
        resource_allocation.description
        Get these from tms.activity
        """
        activity = resource_allocation.activity_id or False
        return '%s %s ' % (activity and activity.description or False,
                           activity and activity.day_sold_dev or 0.0)

    def _get_color(self, resource_allocation):
        priority = resource_allocation.activity_id and \
            resource_allocation.activity_id.priority or False
        color_map = {
            'high': 'light-red',
            'normal': 'light-green',
            'low': 'light-blue'
        }
        return color_map[priority]

    def _get_tags_ids(self, resource_allocation):
        """
             'Initial Project Iterations': 'fa fa-play',
             'Evolution': 'fa fa-fast-forward',
             'Support': 'fa fa-wrench',
             'Guaranty': 'fa fa-bug',
             'Other': 'fa fa-question',
             'Prospection & Demo': 'fa fa-users',
             'R&D': 'fa fa-flask',
             'Supervision': 'fa fa-eye',
        """
        analytic_second_axis = resource_allocation.activity_id and \
            resource_allocation.activity_id.analytic_secondaxis_id or False
        analytic_second_axis_name = analytic_second_axis and \
            analytic_second_axis.name or False
        cr = RegistryManager.get(self.pool.db_name).cursor()
        # Search tag_ids depends on name of analytic_second_axis_name
        booking_research_tag_ids = self.pool['booking.resource.tag'].\
            search(cr, 1, [('name', '=', analytic_second_axis_name)])
        return [(6, 0, booking_research_tag_ids)]

    _booking_chart_mapping = {
        'tms_modules.resource_allocation_booking_chart': {
            'name': _get_name,
            'resource_ref': _get_hr_employee_id,
            'origin_ref': 'id',
            'message': _get_description,
            'date_start': 'date_from',
            'date_end': 'date_to',
            'css_class': _get_color,
            'tag_ids': _get_tags_ids,
        }
    }


hr_resource_allocation()
