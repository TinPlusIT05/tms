
from openerp import models, fields, api
from datetime import datetime
from openerp.exceptions import Warning


class HrEmployeeCapacity(models.Model):

    _name = "hr.employee.capacity"
    _description = "hr_employee_capacity"
    _order = "starting_date DESC, employee_id DESC"
    _rec_name = 'employee_id'

    @api.depends('employee_id', 'employee_id.active', 'starting_date')
    def _compute_active(self):
        for capacity in self:
            if not capacity.employee_id.active:
                # The employee is inactive or invalid employee
                capacity.active = False
            else:
                latest_employee_capacity = self.search(
                    [('employee_id', '=', capacity.employee_id.id)],
                    limit=1, order='starting_date DESC')
                if latest_employee_capacity and \
                        capacity.id != latest_employee_capacity.id:
                    """ The latest capacity in database is not the current
                        capacity. So we have to compare this 2 capacities which
                        is newer
                    """
                    date_latest_capacity = datetime.strptime(
                        latest_employee_capacity.starting_date, "%Y-%m-%d")
                    date_capacity = datetime.strptime(capacity.starting_date,
                                                      "%Y-%m-%d")
                    if date_latest_capacity < date_capacity:
                        # The current capacity is newer than the other capacity
                        # so we have to set the old latest capacity to inactive
                        # and the current to active
                        capacity.active = True
                        sql = "UPDATE hr_employee_capacity SET active=False \
                                WHERE id = %s" % latest_employee_capacity.id
                        self._cr.execute(sql)
                    else:
                        # The current capacity is older than the latest
                        capacity.active = False
                else:
                    # The first new capacity
                    capacity.active = True

    employee_id = fields.Many2one(
        "hr.employee", string="Employee", required=True)
    starting_date = fields.Date(
        string="Starting Date", required=True,
        default=lambda self: fields.date.today())
    production_rate = fields.Float(
        string="Production Rate (%)", digits=(2, 0),
        help="""Input 50 for 50%. This represent the % of time during which
        the employee should be working on forge tickets.""")
    team_id = fields.Many2many(string="Team", related='employee_id.team_id')
    manager_id = fields.Many2one(string="Manager", store=True,
                                 related='employee_id.parent_id')
    active = fields.Boolean(string="Active", store=True,
                            compute='_compute_active')
    team_leader_id = fields.Many2one(
        string='Team Leader',
        comodel_name='hr.employee',
        related="employee_id.parent_id"
    )
    team_manager_id = fields.Many2one(
        string='Team Manager',
        related='employee_id.team_manager',
        store=True,
    )

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self._context.get('my_subordinates', False):
            logged_user = self.env['res.users'].browse(self._uid)
            args.append(['employee_id', 'child_of',
                         logged_user.employee_id.id])
        return super(HrEmployeeCapacity, self).search(
            args, offset=offset, limit=limit, order=order, count=count)

    job_id = fields.Many2one(string='Job', related='employee_id.job_id',
                             store=True)
    job_type_id = fields.Many2one(string='User Job Type',
                                  related='employee_id.job_id.job_type_id',
                                  store=True)

    @api.multi
    def write(self, values):
        res = super(HrEmployeeCapacity, self).write(values)
        for rec in self:
            if values.get('production_rate', False):
                profile_user = self.env.user.group_profile_id
                profile_admin = self.env.ref(
                    'tms_modules.group_profile_tms_admin')
                team_leader_id = rec.team_leader_id.user_id.id
                team_manager_id = rec.team_manager_id.user_id.id
                if self._uid not in [team_leader_id, team_manager_id] \
                        and profile_user != profile_admin \
                        and not self._context.get('by_pass_sec', False):
                    raise Warning('Just only team leader or team manager or '
                                  'admin can change capacity for this employee'
                                  )
        return res
