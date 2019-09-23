# -*- encoding: UTF-8 -*-
from datetime import date, datetime, timedelta
from openerp import fields, api, models
import logging
from openerp.exceptions import Warning
from dateutil.relativedelta import relativedelta

DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class hr_employee(models.Model):

    _inherit = "hr.employee"
    _order = 'login'

    asset_ids = fields.One2many(
        string="Assets",
        comodel_name="tms.asset",
        inverse_name="owner_id",
        track_visibility="onchange",
        help="Asset which owned by employee")
    depreciate_line_ids = fields.One2many(
        string="Trobz Assets",
        comodel_name="depreciation.lines",
        inverse_name="employee_id",
        track_visibility="onchange",
        domain=[('is_depreciated', '=', True)])
    benefit_months = fields.Integer(
        'Months of benefit',
        compute='compute_benefit_months',
        help='The months from benefit started to the current date')
    debit_benefit = fields.Float(
        string='Debited Benefit',
        compute='get_debit_benefit',
        store=True,
        help='Total amount that this employee has used to purchase equipments')
    balance_benefit = fields.Float(
        string='Balance Benefit', readonly=True,
        compute='compute_balance_benefit',
        store=True,
        help='Remaining amount that employee can use to purchase equipment')
    employee_code = fields.Char(
        string='Employee Code',
        size=32)

    @api.multi
    @api.depends('birthday')
    def compute_employee_birthday_month(self):
        for employee in self:
            employee.birthday_month = ""
            if employee.birthday:
                brth = map(int, employee.birthday.split("-"))
                employee.birthday_month = "{:02d}".format(date(*brth).month)

    @api.multi
    def _is_dedicated_resource(self):
        for employee in self:
            today = fields.Date.today()
            domain = [('employee_id', '=', employee.id),
                      ('start_date', '<=', today), '|',
                      ('end_date', '>=', today),
                      ('end_date', '=', False)]
            resource_env = self.env['hr.dedicated.resource.contract']
            resource_rec = resource_env.search(domain)
            is_dedicated_resource = False
            if resource_rec:
                is_dedicated_resource = True
            employee.is_dedicated_resource = is_dedicated_resource

    @api.multi
    def get_credit_benefit_on_date(self, compute_date=None):
        """
        (date) -> int
        Return credit benefit of employee on date. If not date, compute to
        current date.
        Incase employee has no hire_date, return 0
        """
        self.ensure_one()
        cred_benefit = 0
        if not self.hire_date or not self.benefit_start:
            return cred_benefit
        today = datetime.now().date()
        start_date = datetime.strptime(self.benefit_start, DATE_FORMAT).date()
        end_date = compute_date or today
        gap = relativedelta(end_date, start_date)
        gap_year = gap.years
        gap_month = gap.months
        diff = gap_year * 12 + gap_month
        cred_benefit = diff * self.amt_benefit
        return cred_benefit

    issued_place = fields.Char(string='Issued Place')
    issued_date = fields.Date(string="Issued Date")
    skype_id = fields.Char(string='Skype ID', required=False)
    employee_capacity_ids = fields.One2many(
        comodel_name='hr.employee.capacity',
        inverse_name='employee_id',
        string='Employee Capacity'
    )
    employee_capacity_weekly_ids = fields.One2many(
        comodel_name='hr.employee.capacity.weekly',
        inverse_name='employee_id',
        string='Employee Capacity Weekly',
        readonly=True,
    )
    login = fields.Char(
        related='resource_id.user_id.login',
        string='Login',
        readonly=True,
        store=True
    )
    birthday_month = fields.Char(
        compute='compute_employee_birthday_month',
        string="Birthday Month",
        store=True
    )
    team_id = fields.Many2many(
        comodel_name='hr.team',
        relation='team_member_rel',
        string='Team'
    )
    job_type_id = fields.Many2one(
        comodel_name='hr.job.type',
        string='User Job Type',
        related='job_id.job_type_id',
        store=True
    )
    team_manager = fields.Many2one(
        comodel_name="hr.employee",
        string="Team Manager",
    )
    is_dedicated_resource = fields.Boolean(
        compute='_is_dedicated_resource',
        string='Is Dedicated Resource',
        help='This employee is a dedicated resource?'
    )
    current_employee_capacity = fields.Float(
        string='Current Capacity',
        compute='_get_current_capacity',
        store=True
    )
    employee_capacity_three_months = fields.Float(
        string='Capacity (for 3 months)',
        compute='_compute_capacity_three_months'
    )
    parent_id = fields.Many2one(string='Team Leader')
    leave_manager_id = fields.Many2one(
        'hr.employee',
        string='Leave Manager',
    )
    approval_employee_ids = fields.One2many('hr.employee', 'leave_manager_id')

    tax_code = fields.Char('Tax Code', groups="base.group_hr_manager")
    current_country_id = fields.Many2one('res.country', 'Current Country')
    current_state_id = fields.Many2one('res.country.state', 'Current State')
    current_district_id = fields.Many2one(
        'res.country.state.district', 'Current District')
    current_ward_id = fields.Many2one(
        'res.country.state.district.ward',
        'Current Ward'
    )
    current_street = fields.Char('Current Street')

    @api.onchange('current_country_id')
    def onchange_current_country_id(self):
        self.current_state_id = None
        self.current_district_id = None
        self.current_ward_id = None
        self.current_street = None

    @api.onchange('current_state_id')
    def onchange_current_state_id(self):
        self.current_district_id = None
        self.current_ward_id = None
        self.current_street = None

    @api.onchange('current_district_id')
    def onchange_current_district_id(self):
        self.current_ward_id = None
        self.current_street = None

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        if self.parent_id:
            self.leave_manager_id = self.parent_id

    @api.model
    def create(self, vals):
        # F#13269
        ctx = self._context and self._context.copy() or {}
        param_obj = self.env['ir.config_parameter']
        default_manager_name = param_obj.get_param(
            'default_trobz_manager_name')
        if self.name != default_manager_name and \
                not vals.get('parent_id', False) and \
                not ctx.get('create_from_application'):
            raise Warning("You must set a manager!")
        res = super(hr_employee, self).create(vals)
        if 'user_id' in vals and vals.get('user_id', False) and res:
            res.user_id.sudo().write({'employee_id': res.id})
        return res

    @api.multi
    def write(self, vals):
        # F#13269
        ctx = self._context and self._context.copy() or {}
        param_obj = self.env['ir.config_parameter']
        default_manager_name = param_obj.get_param(
            'default_trobz_manager_name')
        for user in self:
            name = vals.get('name', user.name)
            parent_id = vals.get(
                'parent_id', user.parent_id and user.parent_id.id or False)
            if name != default_manager_name and \
                    not parent_id and not ctx.get('create_from_application'):
                raise Warning("You must set a manager!")
        res = super(hr_employee, self).write(vals)
        if 'user_id' in vals and vals.get('user_id', False) and res:
            [hr.user_id.sudo().write({'employee_id': hr.id}) for hr in self]
        return res

    # ====================================================
    # ============ HR EMAILS ===================
    # ====================================================
    KEY_FIGURE_ORANGE = '<h4><div style="font-size:18px;' +\
        'color:orange;font-family:Arial" >%s</div></h4>'

    @api.model
    def get_string_from_job_type(self, item):
        rs = ''
        wip_ticket = str(item[6] and int(item[6]) or 0) + ' WIP'
        assigned_ticket = str(item[7] and int(item[7]) or 0) + ' Assigned'
        qa_ticket = str(item[8] and int(item[8]) or 0) + ' QA'
        if item[3] < 8:
            if item[2]:
                rs += '<li><font color="#f00">' + \
                    item[1] + ': ' + str(item[2] and int(item[2]) or 0) +\
                    ' assigned ticket(s) with ' +\
                    str(item[3] or 0) + \
                    ' hour(s) for workload.  ('
                if item[6]:
                    rs += wip_ticket
                if item[7] and item[6]:
                    rs += ', ' + assigned_ticket
                elif item[7]:
                    rs += assigned_ticket
                if item[8]:
                    if item[6] or item[7]:
                        rs += ', ' + qa_ticket
                    else:
                        rs += qa_ticket
                rs += ')</font></li>\n'
            else:
                rs += '<li><font color="#f00">' + \
                    item[1] + ': ' + str(item[2] and int(item[2]) or 0) +\
                    ' assigned ticket(s) with ' +\
                    str(item[3] or 0) + \
                    ' hour(s) for workload.</font></li>\n'
        else:
            if item[2]:
                rs += '<li>' + item[1] + ': ' + str(
                    item[2] and int(item[2]) or 0
                ) + ' assigned ticket(s) with ' + str(
                    item[3] or 0
                ) + ' hour(s) for workload. ('

                if item[6]:
                    rs += wip_ticket
                if item[7] and item[6]:
                    rs += ', ' + assigned_ticket
                elif item[7]:
                    rs += assigned_ticket
                if item[8]:
                    if item[7] or item[6]:
                        rs += ', ' + qa_ticket
                    else:
                        rs += qa_ticket
                rs += ')</li>\n'
            else:
                rs += '<li>' + item[1] + ': ' + str(
                    item[2] and int(item[2]) or 0
                ) + ' assigned ticket(s) with ' + str(
                    item[3] or 0
                ) + ' hour(s) for workload.</li>\n'

        return rs

    @api.model
    def get_trobz_member_detail(self):
        """
        Ticket F24451:
            - Because of changing field team_id from m2o to m2m, we will show
            all member, whose job in job_val_param_lst, in each team.
        """
        team_env = self.env['hr.team']
        job_env = self.env['hr.job']
        user_env = self.env['res.users']
        config_pool = self.env["ir.config_parameter"]
        # Read configuration for trobz_member_workload mapping
        # then parse configuration string
        trobz_member_workload_string = config_pool.get_param(
            "trobz_member_workload_param", "{}")
        trobz_member_workload_dict = eval(trobz_member_workload_string)
        job_val_param_lst = trobz_member_workload_dict.get(
            'group_jobs', [])
        all_teams = team_env.search([])
        team_val_param_lst = [team.name for team in all_teams]
        team_val_param_tuple = tuple(team_val_param_lst)

        """
        Get workload of member who have assigned tickets  in team
        """
        assigned_ticket_query = '''
            SELECT
                ru.id,
                rp.name,
                sum(tbl1_1.total_ticket) total_ticket,
                sum(tbl1_1.total_time) total_time,
                ht.id as team_id,
                he.job_id,
                sum(tbl1_1.total_ticket_wip) total_ticket_wip,
                sum(tbl1_1.total_ticket_assigned) total_ticket_assigned,
                sum(tbl1_1.total_ticket_in_qa) total_ticket_in_qa
            FROM res_users ru
                JOIN res_partner rp
                    ON rp.id = ru.partner_id
                JOIN hr_employee he
                    on he.id = ru.employee_id
                JOIN hr_job hj
                    ON he.job_id = hj.id
                JOIN team_member_rel tmr
                    ON he.id = tmr.hr_employee_id
                JOIN hr_team ht
                    ON ht.id = tmr.hr_team_id
                JOIN (
                    SELECT id, team_id
                    FROM tms_project
                    WHERE state = 'active') tprj ON tprj.team_id = ht.id
                LEFT JOIN (
                    SELECT
                        tbl1.user_id,
                        tbl1.project_id project_id,
                        sum(tbl1.total_time)::INTEGER total_time,
                        sum(tbl1.total_ticket) total_ticket,
                        sum(tbl1.total_ticket_assigned) total_ticket_assigned,
                        sum(tbl1.total_ticket_wip) total_ticket_wip,
                        sum(tbl1.total_ticket_in_qa) total_ticket_in_qa
                    FROM
                        (
                            SELECT
                                tft.project_id project_id,
                                tft.owner_id user_id,
                                sum(tft.remaining_time) total_time,
                                count(tft.id) total_ticket,
                                CASE
                                    WHEN tft.state = 'assigned'
                                    THEN count(tft.id)
                                END total_ticket_assigned,
                                CASE
                                    WHEN tft.state = 'wip'
                                    THEN count(tft.id)
                                END total_ticket_wip,
                                CASE
                                    WHEN tft.state = 'in_qa'
                                    THEN count(tft.id)
                                END total_ticket_in_qa
                            FROM
                                tms_forge_ticket tft
                            WHERE
                                tft.state IN ('wip', 'assigned', 'in_qa')
                            GROUP BY
                                tft.project_id,
                                tft.owner_id,
                                tft.state
                            ORDER BY
                                tft.owner_id
                        ) tbl1
                    GROUP BY
                        tbl1.user_id,
                        tbl1.project_id
                ) tbl1_1
                    ON ru.id = tbl1_1.user_id
                        AND tprj.id = tbl1_1.project_id
            WHERE
                ru.is_trobz_member = 't'
                AND ru.active='t'
            GROUP BY
                ru.id,
                rp.name,
                ht.id,
                he.job_id
            ORDER BY
                ru.id,
                total_ticket DESC;
        '''
        self._cr.execute(
            assigned_ticket_query,
            (team_val_param_tuple, tuple(job_val_param_lst))
        )
        assigned_ticket_list = self._cr.fetchall()
        # assigned_ticket_list structure (store all ticket information
        #     group by employee name and team):
        # (id, name, total ticket, total time, team, job, wip, assigned, in qa)

        """
        Get workload for member who do not have assigned tickets in team
        """
        team_ids = list(set([item[4] for item in assigned_ticket_list]))
        for team in team_env.browse(team_ids):
            team_id = team.id
            user_has_assign_ticket_ids = [i[0] for i in assigned_ticket_list
                                          if i[4] == team.id]
            all_user_in_team_ids = team.members_ids.get_user_id()
            user_has_no_assign_ticket_ids = list(
                set(all_user_in_team_ids) -
                set(user_has_assign_ticket_ids))
            user_has_no_assign_ticket = user_env.browse(
                user_has_no_assign_ticket_ids)
            for user in user_has_no_assign_ticket:
                employee = user.employee_id or False
                if employee and employee.job_id and \
                        employee.job_id.name in job_val_param_lst:
                    job_id = employee.job_id.id
                    name = employee.name
                    assigned_ticket_list.append((
                        user.id, name, 0, 0, team_id, job_id
                    ))

        """Group by team and job
        """
        assigned_ticket_dict = {}
        for item in assigned_ticket_list:
            team_record = team_env.browse(item[4])
            job_record = job_env.browse(item[5])
            if team_record.name not in assigned_ticket_dict.keys():
                assigned_ticket_dict.update(
                    {team_record.name: {job_record.name: [item]}})
            else:
                if job_record.name not in \
                        assigned_ticket_dict[team_record.name].keys():
                    assigned_ticket_dict[team_record.name].update(
                        {job_record.name: [item]})
                else:
                    assigned_ticket_dict[team_record.name][
                        job_record.name].append(item)
        # assigned_ticket_dict structure (list of dict)
        # - {team name: ticket infomation form assigned ticket list}

        rs = ''
        # iterate with sort name team
        for team_name in sorted(list(assigned_ticket_dict.keys())):
            # get project name
            rs += '<div><b>%s</b></div><ul>' % team_name
            # get value of assigned ticket
            prj_details = assigned_ticket_dict.get(team_name, dict())

            # iterate and display ticket detail
            for emp_name, tickets in prj_details.iteritems():
                rs += '<li>' + emp_name + ': '
                for ticket in tickets:
                    rs += '<ul>'
                    rs += self.get_string_from_job_type(ticket)
                    rs += '</ul>'
                rs += '</li>'
            rs += '</ul>'
        return rs

    @api.model
    def get_birthday_in_next_7_days(self):
        sql_query = '''
            select id, extract(day from age) as d, extract(month from age) as m
            from
            (
                select H.id,
                age(date('' || date_part('year', now())|| '-'
                || extract(month from birthday) || '-'
                || extract(day from birthday)), NOW()) as age
                from hr_employee as H, resource_resource as R, res_users as U
                where H.resource_id = R.id
                and R.user_id = U.id
                and U.active= 't' and  R.active='t'
            ) tbl_temp
        '''
        self._cr.execute(sql_query)
        res = self._cr.fetchall()
        if not res:
            return ''
        users = []
        dob = []
        employee_env = self.env['hr.employee']
        for row in res:
            if row[0] and row[1] is not None and row[2] is not None and\
                    row[1] >= 0 and row[1] <= 8 and row[2] == 0:
                employees = employee_env.browse([int(row[0])])
                for employee in employees:
                    if employee.resource_id and employee.resource_id.name:
                        users.append(employee.resource_id.name)
                        dob.append(employee.birthday)
        if not users:
            return ''
        rs = self.KEY_FIGURE_ORANGE % 'Birthdays coming'
        rs += '<ul>'
        for i in range(len(users)):
            rs += '<li>' + users[i] + ': ' + dob[i] + '</li>'
        rs += '</ul>'
        return rs

    @api.model
    def check_off_today(self, today, lines):
        for record in lines:
            first_date = record.first_date[:10]
            last_date = record.last_date[:10]
            date = datetime.strptime(today, "%Y-%m-%d").strftime("%A")

            if first_date <= today <= last_date and\
                    date not in("Saturday", "Sunday"):
                return True

        return False

    @api.model
    def get_employee_off_from_today_to_number_of_day(
            self, number_of_day, lines):
        after_current_time_n_days =\
            str(date.today() + timedelta(days=number_of_day))
        flag = self.check_off_today(after_current_time_n_days, lines)
        rs = ''

        if flag:
            rs = '<div>%s</div><ul>' % after_current_time_n_days

            # Unused to_read = ['first_date', 'last_date', 'holiday_id',
            # 'holiday_id']
            for record in lines:
                first_date = record.first_date[:10]
                last_date = record.last_date[:10]
                first_date_type = record.first_date_type == 'full' and\
                    'all-day'\
                    or record.first_date_type
                last_date_type = record.last_date_type == 'full' and\
                    'all-day'\
                    or record.last_date_type

                holiday_state = record.holiday_id.state
                html_li_tag = '<li>%s (from %s-%s to %s-%s)</li>' if \
                    holiday_state == 'validate' else \
                    '<li style="color:blue">%s (from %s-%s to %s-%s)</li>'
                if first_date <= after_current_time_n_days <= last_date:
                    rs += html_li_tag % (record.holiday_id.employee_id.name,
                                         first_date, first_date_type,
                                         last_date, last_date_type)

            rs += '</ul>'

        return rs

    @api.model
    def list_employees_leave_in_next_n_days(self):
        number_of_days = self.env['ir.config_parameter'].get_param(
            'leave_in_next_n_days', '30')
        number_of_days = eval(number_of_days)
        result = ''
        current_time = str(date.today())
        after_current_time_n_days =\
            str(date.today() +
                timedelta(days=number_of_days))

        lines_1 = self.env['hr.holidays.line'].\
            search([
                ('holiday_id.state', 'in', ('validate', 'confirm')),
                ('first_date', '>=', current_time),
                ('first_date', '<=', after_current_time_n_days)])
        lines_2 = self.env['hr.holidays.line'].\
            search([
                ('holiday_id.state', 'in', ('validate', 'confirm')),
                ('last_date', '>=', current_time),
                ('last_date', '<=', after_current_time_n_days)])
        lines_3 = self.env['hr.holidays.line'].\
            search([
                ('holiday_id.state', 'in', ('validate', 'confirm')),
                ('first_date', '<=', current_time),
                ('last_date', '>=', after_current_time_n_days)])
        lines = list(set(lines_1 + lines_2 + lines_3))

        if lines:
            result = self.KEY_FIGURE_ORANGE %\
                'List of employees are off for next %s day(s)' %\
                number_of_days
            for number_of_day in range(number_of_days):
                result += self.\
                    get_employee_off_from_today_to_number_of_day(
                        number_of_day, lines)

        return result

    @api.multi
    @api.depends('employee_capacity_ids',
        'employee_capacity_ids.starting_date',
        'employee_capacity_ids.production_rate')
    def _get_current_capacity(self):
        for employee in self:
            capacity_dict = {}
            for capacity in employee.employee_capacity_ids:
                date = datetime.strptime(capacity.starting_date,
                                         "%Y-%m-%d").date()
                capacity_dict[date] = capacity.production_rate
            #  Find most recent Production Rate
            res = capacity_dict and \
                capacity_dict[max(capacity_dict.keys())] or ''
            employee.current_employee_capacity = res

    @api.multi
    def _compute_capacity_three_months(self):
        for employee in self:
            employee.employee_capacity_three_months = \
                employee.current_employee_capacity * 60

    @api.multi
    def get_user_id(self):
        """ Return user id of employee
        """
        user_env = self.env['res.users']
        users = user_env.search([('employee_id', 'in', self.ids)])
        return users and [user.id for user in users] or []

    @api.multi
    @api.depends(
        'asset_ids', 'asset_ids.purchased_price',
        'depreciate_line_ids', 'depreciate_line_ids.amount',
        'depreciate_line_ids.is_depreciated',)
    def get_debit_benefit(self):
        """
        Debit benefit is sum of
        - All personal assets of employee. Use trobz contibution amount
        to compute
        - From all trobz's assets, get depreciation_lines which assign for
        employee and is_depreciated
        """
        depreciation_line_env = self.env["depreciation.lines"]
        asset_env = self.env['tms.asset']
        for employee in self:
            debit_amount = 0
            # Compute debit from personal assets
            personal_assets = asset_env.search(
                [('type', '=', 'personal'), ('owner_id', '=', employee.id)])
            debit_amount += sum(
                [a.trobz_contribution for a in personal_assets])

            # Compute debit of employee from depreciation line of
            # trobz's assets
            trobz_assets = asset_env.search([('type', '=', 'trobz')])
            trobz_asset_ids = [a.id for a in trobz_assets]
            depreciations = depreciation_line_env.search(
                [('asset_id', 'in', trobz_asset_ids),
                 ('employee_id', '=', employee.id),
                 ('is_depreciated', '=', True)])
            debit_amount += sum([depre.amount for depre in depreciations])

            employee.debit_benefit = debit_amount

    @api.depends('debit_benefit', 'cred_benefit')
    @api.multi
    def compute_balance_benefit(self):
        """
            Get Current Balance of Employee's Benefit at Trobz
            Balance = Credit Benefit - Debit Benefit
        """
        for employee in self:
            employee.balance_benefit = employee.cred_benefit - \
                employee.debit_benefit

    @api.multi
    def compute_benefit_months(self):
        """
        Compute number of month of equipment benefit
        """
        to_date = datetime.now().date()
        for rec in self:
            if not rec.hire_date:
                rec.benefit_months = 0
                continue
            from_date = datetime.strptime(
                rec.benefit_start, DATE_FORMAT).date()
            gap = relativedelta(to_date, from_date)
            rec.benefit_months = gap.years * 12 + gap.months

    @api.model
    def scheduler_compute_balance_benefit(self):
        # employees = self.env['hr.employee'].search([])
        # employees.compute_credit_benefit()
        # All field are automatically computed
        pass

    def can_read_equipment_benefit_info(self, cr, user, employee_id, user_id):
        """
        Return True if use_id can read equipment info of employee_id
        """
        employee = self.pool['hr.employee'].browse(cr, user, [employee_id])
        if not employee:
            return False
        allow_user_ids = []
        emp_user = employee.user_id
        if emp_user:
            allow_user_ids.append(emp_user.id)
        hr_group_id = self.pool.get('ir.model.data').get_object_reference(
            cr, user, 'base', 'group_hr_manager')[1]
        hr_group = self.pool['res.groups'].browse(cr, user, [hr_group_id])
        allow_user_ids.extend(hr_group.users.ids)
        user = self.pool['res.users'].browse(cr, user, [user_id])
        if user.id in allow_user_ids:
            return True
        return False

    def read(
        self, cr, user, ids, fields=None,
        context=None, load='_classic_read'
    ):
        """
        Inherit this function to hide data of tab assets with user who is not
        user of employee or not in HR Manager
        """
        employee_env = self.pool['hr.employee']
        equip_benefit_fields = [
            'benefit_start', 'benefit_months',
            'cred_benefit', 'debit_benefit', 'balance_benefit',
            'asset_ids', 'depreciate_line_ids',
            'it_equipment_bonus_ids'
        ]
        if len(ids) == 1:
            employee = employee_env.browse(cr, user, ids)
            if not self.can_read_equipment_benefit_info(
                    cr, user, employee.id, user):
                for field in equip_benefit_fields:
                    if field in fields:
                        fields.remove(field)
        res = super(hr_employee, self).read(
            cr, user, ids, fields=fields,
            context=context, load='_classic_read'
        )
        return res

    @api.model
    def remove_former_employee_as_follower(self):
        logging.info(
            "====== START: Unfollow %s from all Job Position  ======"
            % (self.name))
        partner_id = self.env['res.partner'].search(
            [("related_user_id", "=", self.user_id.id)])
        followed_pos_ids = self.env['mail.followers'].search([
            ('partner_id', '=', partner_id.id),
            '|',
            ('res_model', '=', 'hr.job'),
            ('res_model', '=', 'hr.applicant')
        ])
        if followed_pos_ids:
            followed_pos_ids.unlink()
        else:
            raise Warning("%s is not following any Job Position/Application"
                          % (self.name))
        logging.info(
            "====== END: Unfollow %s from all Job Position  ======"
            % (self.name))
        return True

    @api.multi
    def button_remove_former_employee_as_follower(self):
        for rec in self:
            rec.remove_former_employee_as_follower()

    @api.model
    def _cron_set_hire_date_for_employee(self, employee_id, hire_date):
        logging.info(
            "====== Set hire_date %s for employee id %s  ======"
            % (hire_date, employee_id))
        employee = self.search([('id', '=', employee_id)])
        if employee and hire_date:
            # Functions compute depends hire_date run are not as expected.
            # Solution is update hire_date by sql then run
            employee.write({'hire_date': hire_date})
        else:
            logging.info(
                "====== Not found employee with id: %s  ======"
                % (employee_id))
        return True
