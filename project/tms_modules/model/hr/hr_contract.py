# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import Warning
from datetime import datetime
from dateutil.relativedelta import relativedelta  # @UnresolvedImport
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.safe_eval import safe_eval


class HrContract(models.Model):

    _inherit = 'hr.contract'
    _order = 'login'

    list_of_month = [
        ('01', '01'), ('02', '02'), ('03', '03'), ('04', '04'),
        ('05', '05'), ('06', '06'), ('07', '07'), ('08', '08'),
        ('09', '09'), ('10', '10'), ('11', '11'), ('12', '12')
    ]

    @api.model
    def compute_mon_contract(self):
        for contract in self:
            contract = datetime.strptime(
                contract['date_start'], "%Y-%m-%d").strftime("%m")

    login = fields.Char(related='employee_id.user_id.login',
                        string='Login',
                        store=True)
    month_contract = fields.Selection(compute='compute_mon_contract',
                                      selection=list_of_month,
                                      string='Month',
                                      method=True,
                                      store=True)
    is_trial = fields.Boolean(
        compute='_compute_is_trial', store=True, readonly=False,
        default=False, string="Is Trial", help="This is in trial period"
    )
    renew_casual_leave = fields.Boolean(
        string='Renew Casual Leave Day (paid)',
    )
    yearly_sick_leaves = fields.Float(
        string='Yearly Sick Leaves',
        default=5,
        digits=(1, 1),
    )

    @api.multi
    def write(self, values):
        if values.get('renew_casual_leave'):
            self.renew_casual_leave_paid()
        return super(HrContract, self).write(values)

    @api.model
    def create(self, values):
        res = super(HrContract, self).create(values)
        if values.get('renew_casual_leave'):
            res.renew_casual_leave_paid()
        return res

    @api.multi
    def renew_casual_leave_paid(self):
        # This function is to renew the casual leave (paid)
        # after sign the formal contract.
        for rec in self:
            holiday_obj = self.env['hr.holidays']
            allo_request = holiday_obj.search([
                ('employee_id', '=', rec.employee_id.id),
                ('type', '=', 'add'),
                ('holiday_status_id', '=', self.env.ref(
                    'hr_holidays.holiday_status_cl').id),
                ('allo_date', '<', rec.date_start)
            ])
            for rc in allo_request:
                rc.write({
                    'renew_casual_leave': True
                })
            leave_requests = holiday_obj.search([
                ('employee_id', '=', rec.employee_id.id),
                ('type', '=', 'remove'),
                ('date_to', '<', rec.date_start)
            ])
            for rc in leave_requests:
                rc.write({
                    'renew_casual_leave': True
                })

    @api.model
    def _domain_month_contract(self, args):
        for arg in args:
            if arg[0] and arg[0] == 'month_contract':
                # filter month_contract by month of date_start
                # or month of date_end
                SQL = '''
                        SELECT id
                        FROM hr_contract
                        WHERE
                            date_part('month',date_start)::INTEGER = %s
                            OR date_part('month',date_end)::INTEGER = %s;
                '''
                self._cr.execute(SQL, (arg[2], arg[2]))
                res = self._cr.fetchall()
                # new arg of month_contact
                months_arg = ['id', 'in', [x[0] for x in res]]
                # replace old month_contract by the new arg
                args[args.index(arg)] = months_arg
        return args

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        args = self._domain_month_contract(args)
        return super(HrContract, self).search(
            args, offset=offset,
            limit=limit, order=order,
            count=count)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0,
                   limit=None, orderby=False, lazy=False):
        domain = self._domain_month_contract(domain)
        return super(HrContract, self).read_group(
            domain=domain, fields=fields, groupby=groupby,
            offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    @api.model
    def get_reviewing_contract_list(self):
        sql = '''
        SELECT hem.name_related, hco.date_start, hco.date_end
        FROM hr_contract hco
            JOIN hr_employee hem
                ON hem.id = hco.employee_id
            JOIN resource_resource rre
                ON rre.id = hem.resource_id
                    AND rre.active = True
        WHERE
            (date_end IS NOT NULL
                AND date_end >= %s
                AND date_end <= %s)
            OR (date_end IS NULL
                    AND date_part('month', date_start)
                        || '-' || date_part('day', date_start) >= %s
                    AND date_part('month', date_start)
                        || '-' || date_part('day', date_start) <= %s)
        ORDER BY hco.date_start, hem.name_related;
        '''
        now = datetime.now().date()
        date_start_1 = (now +
                        relativedelta(day=0, months=1, days=0)).replace(day=1)
        date_end_1 = now + relativedelta(day=1, months=2, days=-1)
        date_start_2 = "%s-%s" % (date_start_1.month, date_start_1.day)
        date_end_2 = "%s-%s" % (date_end_1.month, date_end_1.day)
        self._cr.execute(sql, (date_start_1, date_end_1,
                               date_start_2, date_end_2))
        if self._cr.rowcount:
            info_str = '<div>Details</div><ul>'
            tb_row = '<li>%s (%s - %s)</li>'
            for row in self._cr.fetchall():
                info_str += tb_row % (row[0], row[1], row[2] or '? ')
            info_str += '</ul>'
        else:
            info_str = '<div>There is no employee to'\
                       'review performance in next month.</div>'

        return info_str

    @api.model
    def send_email_hr_manager_remind_review_emp(self):
        email_template = self.env.ref(
            'tms_modules.email_template_monthly_remind_hr_manager_review_emp')
        # Function send_mail need parameter res_id
        # (id of the record to render the template with)
        contract_recs = self.env['hr.contract'].search([])
        if contract_recs and email_template:
            email_template.send_mail(contract_recs[0].id,
                                     force_send=True, raise_exception=True)
        else:
            raise Warning('Warning', 'There is no contract to check!')
        return True

    @api.depends('type_id', 'type_id.auto_tick_trial')
    def _compute_is_trial(self):
        for record in self:
            if record.type_id and record.type_id.auto_tick_trial:
                record.is_trial = True
            else:
                record.is_trial = False

    @api.model
    def create(self, vals):
        res = super(HrContract, self).create(vals)
        res.check_create_allocation_in_trial()
        return res

    @api.multi
    def check_create_allocation_in_trial(self):
        '''
            When employee(not trainee) pass trial contract, system generate
            Allocation Request for the trial time.
        '''
        type_employee = self.env.ref('hr_contract.hr_contract_type_emp')
        for contract in self:
            employee = contract.employee_id
            pass_contract = employee.contract_ids - contract
            trial_contract = pass_contract.filtered(
                lambda x: x.is_trial and x.type_id == type_employee
            )
            if len(pass_contract) == 1 and trial_contract:
                trial_contract.create_allocation_request()
        return True

    @api.multi
    def create_allocation_request(self):
        AllocationRequest = self.env['hr.holidays']
        for rec in self.filtered(lambda x: x.date_start and x.date_end):
            date_start = rec.date_start
            date_end = rec.date_end
            number_of_day = self.get_number_of_allocation(
                date_start, date_end, rec.employee_id)
            if number_of_day > 0:
                AllocationRequest += AllocationRequest.create_allo_request(
                    rec.employee_id.id,
                    number_of_day,
                    name='Allocation request for trial contract'
                )
        return AllocationRequest

    @api.model
    def get_number_of_allocation(self, date_start, date_end, employee):
        '''
            Employee work more than 14days per month will have 1 allocation
        '''
        from_date = datetime.strptime(date_start, DF)
        to_date = datetime.strptime(date_end, DF)
        number_of_day = 0
        work_hour_per_day = employee.user_id.daily_hour or 8
        next_date = from_date + relativedelta(months=1)
        WHs = self.env['tms.working.hour']
        run = True

        param_obj = self.env['ir.config_parameter']
        leave_type_unpaid_ids = param_obj.get_param(
            'leave_type_unpaid_ids', '[]')
        leave_type_unpaid_ids = safe_eval(leave_type_unpaid_ids)

        number_of_day_trial_have_allocation =\
            param_obj.get_param('number_of_day_trial_have_allocation', '14')
        number_of_day_trial_have_allocation = safe_eval(
            number_of_day_trial_have_allocation)
        while(run):
            if next_date > to_date:
                next_date = to_date
                run = False
            work_hours = WHs.search([
                ('employee_id', '=', employee.id),
                ('date', '>=', from_date.strftime(DF)),
                ('date', '<=',
                 (next_date - relativedelta(days=1)).strftime(DF)),
                '|',
                ('hr_holiday_line_id', '=', False),
                ('hr_holiday_line_id.holiday_status_id', 'not in',
                 leave_type_unpaid_ids)])
            hours = sum(work_hours.mapped('duration_hour'))
            number_of_day += (hours / work_hour_per_day) //\
                number_of_day_trial_have_allocation

            from_date = next_date
            next_date += relativedelta(months=1)
        return number_of_day
