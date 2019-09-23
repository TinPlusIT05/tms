# -*- encoding: UTF-8 -*-
from datetime import datetime, timedelta, date
import logging
from openerp import models, api, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from dateutil.relativedelta import relativedelta
from openerp.exceptions import Warning


class hr_holidays(models.Model):
    _inherit = "hr.holidays"
    _order = "allo_date DESC, date_from DESC, employee_id ASC"

    full_description = fields.Char(
        'Full Description',
        help='Detail leave reason. Only HR team and your manager can see ' +
        'personal reason')
    name = fields.Char('Description')
    renew_casual_leave = fields.Boolean()
    notify_message = fields.Char(
        compute='_compute_notify_message',
        readonly=True
    )

    @api.multi
    def _compute_notify_message(self):
        '''
        Show message about leave Emergency Leave(aka Sick Leave) to show
        number of day until now employee have.
        '''
        sick_paid = self.env.ref(
            'trobz_hr_holiday_vn.hr_holiday_status_sick_paid')
        today = date.today()
        begin_year = today.replace(month=1, day=1).strftime(DF)
        for rec in self:
            line_eml = rec.holiday_line.filtered(
                lambda l: l.holiday_status_id == sick_paid)
            notify_message = ''
            if line_eml:
                employee = rec.employee_id
                # hire_date is compute and store, when use employee.hire_date
                # system get from function compute of this field
                # But we want value exactly from databse.
                hire_date = employee.read(['hire_date'])[0]['hire_date']
                date_start_eml = max(begin_year, hire_date)
                date_start_eml_obj = datetime.strptime(date_start_eml, DF)
                contract = employee.contract_ids.filtered(
                    lambda c: not c.date_end or today.strftime(DF) < c.date_end
                )
                yearly_sick_leaves = contract and\
                    contract[0].yearly_sick_leaves or 0
                gap = relativedelta(today, date_start_eml_obj)
                gap_month = gap.months
                days = round(gap_month * yearly_sick_leaves / 12, 2)
                notify_message = \
                    'Actual %s this employee have: %s days. Count from %s '\
                    'to %s' % (
                        sick_paid.name, days,
                        date_start_eml_obj.strftime('%d/%m/%Y'),
                        today.strftime('%d/%m/%Y')
                    )
            rec.notify_message = notify_message

    @api.multi
    @api.depends('holiday_line', 'holiday_line.holiday_status_id',
                 'holiday_line.holiday_status_id.name')
    def _get_leave_type(self):
        """
        Concatenate of leave type in holiday lines
        """
        for holiday in self:
            holiday_types = []
            for holiday_line in holiday.holiday_line:
                if holiday_line.holiday_status_id \
                        and holiday_line.holiday_status_id.name \
                        and holiday_line.holiday_status_id.name \
                        not in holiday_types:
                    holiday_types.append(holiday_line.holiday_status_id.name)

            if holiday_types:
                holiday.leave_type = ', '.join(holiday_types)
            else:
                holiday.leave_type = ''

    @api.multi
    @api.depends('holiday_line', 'holiday_line.holiday_status_id',
                 'holiday_line.holiday_status_id.name')
    def _get_sick_leave_paid(self):
        """
        Show `Change to Paid` button if leave type is sick leave unpaid
        """
        param_obj = self.env['ir.config_parameter']

        config_value_unpaid = param_obj.get_param(
            'default_unpaid_sick_leave_types',
        )
        sick_leaves_unpaid = config_value_unpaid and eval(
            config_value_unpaid) or []

        config_value_paid = param_obj.get_param(
            'default_sick_leave_paid_new',
        )
        sick_leaves_paid = config_value_paid and eval(config_value_paid) or []

        config_value_soc_ins = param_obj.get_param(
            'default_sick_leave_social_ins',
        )
        sick_leaves_soc_ins = config_value_soc_ins and eval(
            config_value_soc_ins) or []

        for holiday in self:
            is_specific_paid = False
            is_specific_unpaid = False
            is_specific_soc_ins = False

            for line in holiday.holiday_line:
                if line.holiday_status_id and line.holiday_status_id.name:
                    if line.holiday_status_id.name in sick_leaves_paid:
                        is_specific_paid = True
                    if line.holiday_status_id.name in sick_leaves_unpaid:
                        is_specific_unpaid = True
                    if line.holiday_status_id.name in sick_leaves_soc_ins:
                        is_specific_soc_ins = True

            holiday.sick_leave_flag = is_specific_paid
            holiday.sick_leave_unpaid_flag = is_specific_unpaid
            holiday.sick_leave_social_ins_flag = is_specific_soc_ins

    # Columns
    leave_type = fields.Text(
        compute=_get_leave_type, store=True,
        string="Leave Type"
    )
    sick_leave_social_ins_flag = fields.Boolean(
        compute=_get_sick_leave_paid, store=True,
        string='Sick leave (Social Ins)'
    )
    sick_leave_unpaid_flag = fields.Boolean(
        compute=_get_sick_leave_paid, store=True,
        string='Sick Leave (Unpaid)'
    )
    sick_leave_flag = fields.Boolean(
        compute=_get_sick_leave_paid, store=True,
        string='Sick Leave'
    )
    double_validation = fields.Boolean(
        string='Apply Double Validation',
        compute='_compute_double_validation',
        store=True
    )
    remider_add_attachment = fields.Boolean(
        compute='_compute_remider_add_attachment',
        store=True,
        default=False)
    state = fields.Selection(default='draft')
    support_training_id = fields.Many2one(
        comodel_name='tms.support.training',
        string='Business Trip')

    @api.multi
    @api.depends('state', 'double_validation')
    def _compute_remider_add_attachment(self):
        for record in self:
            ir_attachment_obj = record.env['ir.attachment']
            active_model = 'hr.holidays'
            attachment_num = ir_attachment_obj.search_count(
                [('res_model', '=', active_model),
                 ('res_id', '=', record.id)])
            if record.state in ('draft', 'confirm', 'validate1') and\
                    not attachment_num and record.double_validation:
                record.remider_add_attachment = True
            else:
                record.remider_add_attachment = False

    @api.multi
    @api.depends('holiday_line', 'holiday_line.holiday_status_id')
    def _compute_double_validation(self):
        for record in self:
            record.double_validation = False
            holiday_lines = record.holiday_line
            for line in holiday_lines:
                if line.holiday_status_id.double_validation:
                    record.double_validation = True

    @api.model
    def function_update_activity_for_leave_type(self):
        logging.info('==== START function_update_activity_for_leave_type')
        sql = """
        UPDATE hr_holidays_status
        SET activity_id =
            (SELECT id from tms_activity WHERE name = 'Days Off')
        WHERE  name != 'Off with compensation';
        UPDATE hr_holidays_status
        SET activity_id =
            (SELECT id from tms_activity WHERE name = 'Compensation')
        WHERE  name = 'Off with compensation';
        """
        self._cr.execute(sql)
        logging.info('==== END function_update_activity_for_leave_type')
        return True

    @api.model
    def function_update_holiday_lines_for_leave_summary(self):
        """
        Make up data, create allocation request line
        to show on leaves summary.
        """
        logging.info(
            '==== START function_update_holiday_lines_for_leave_summary')
        allocation_requests = self.search([
            ('type', '=', 'add'), ('holiday_line', '=', False)
        ])
        for request in allocation_requests:
            if not request.holiday_status_id:
                continue
            vals = {
                'holiday_id': request.id,
                'number_of_days': request.number_of_days_temp,
                'employee_id': request.employee_id.id,
                'first_date_type': False,
                'last_date_type': False,
                'holiday_status_id': request.holiday_status_id.id
            }
            self.env['hr.holidays.line'].create(vals)

        # Update number_of_days_temp = - number_of_days for leave request lines
        self._cr.execute("""
            UPDATE hr_holidays_line
            SET number_of_days_temp = - number_of_days
            WHERE number_of_days_temp IS NULL;
        """)
        logging.info(
            '==== END function_update_holiday_lines_for_leave_summary')
        return True

    @api.model
    def add_allocation_request_each_month(
            self, allo_date=None, emps=None,
            update_extra_leave=False, create_extra_leave=False, 
            description=None):
        """
        Override function
        TMS cases:
            - before 01/2013, only create AR with extra leaves only
                + use create_extra_leave argument
            - After 01/2013, update days = current days on AR + extra leaves
                + use update_extra_leave argument
        Only calculate extra leave for employee in Vietnam
        """
        ctx = dict(self._context) or {}
        res = []
        contract_obj = self.env['hr.contract']

        # Only create allocation request in indicated period
        if allo_date:
            allo_date = datetime.strptime(
                allo_date, DF)
        else:
            allo_date = datetime.today()
        logging.info(
            "======= ALLOCATION DATE: %s======"
            % allo_date)
        fifteenth_date = allo_date + relativedelta(day=15)
        str_fifteenth_date = fifteenth_date.strftime(DF)
        twentyfive_date = allo_date + relativedelta(day=25)
        str_twentyfive_date = twentyfive_date.strftime(DF)
        # Create allocation request for contracts:
        # Official contracts (is_trial is inactive)
        # Start the 15th/Month
        # End after 15th/Month
        domain = [
            ('date_start', '<=', str_twentyfive_date),
            '|', ('date_end', '>=', str_fifteenth_date),
            ('date_end', '=', False),
            ('is_trial', '=', False),
            ('employee_id.active', '=', True),
        ]
        if emps:
            # Only create allocation request for the indicated employees
            if isinstance(emps, str):
                emps = eval(emps)
            domain += [('employee_id', 'in', emps)]

        contracts = contract_obj.search(domain)
        for contract in contracts:
            # Create allocation request with
            # allocation days = monthly paid leaves + extra leaves
            # end of month of the contract with: 15 < date_end < 25
            allocation_days = contract.monthly_paid_leaves
            add_extra = True
            if contract.date_end:

                end_month_contract = datetime.strptime(
                        contract.date_end, DF).month
                end_year_contract = datetime.strptime(
                    contract.date_end, DF).year

                if contract.date_end > str_fifteenth_date and \
                    contract.date_end <= str_twentyfive_date and \
                        end_month_contract == fifteenth_date.month and \
                            end_year_contract == fifteenth_date.year:

                    allocation_days = 0.5
                    add_extra = False
            
            if contract.date_start > str_fifteenth_date and \
                    contract.date_start <= str_twentyfive_date:
                    allocation_days = 0.5

            employee = contract.employee_id
            logging.info("=== EMPLOYEE %s ===" % employee.name)
            if not employee.country_id:
                logging.info("=== No defined nationality.")
            # Specific for TMS
            param = self.env.ref('tms_modules.country_add_extra_leave')
            if not description:
                description = 'Allocation Request for every month'
            if (not param or \
                    (param and employee.country_id.code in eval(
                        param.value))) and add_extra:
                # Calculate extra leaves
                job = contract and contract.job_id or False
                if not job:
                    logging.info(
                        "=== There is no job title defined on %s's contract."
                        % employee.name)
                else:
                    # Calculate extra leave for Work Seniority
                    # Plus to total_extra_leave
                    # if work seniority of this employee equal to
                    #    factor * work seniority interval (defined on job)
                    seniority_config = job.work_seniority_interval * 12
                    if not seniority_config:
                        logging.info(
                            "=== Work Seniority Interval is not set on %s job"
                            % job.name)
                    else:
                        # work_seniority_month from hire_date to allo_date
                        ctx.update({'to_date': allo_date})
                        seniority_emp = employee.with_context(ctx).\
                            work_seniority_month
                        logging.info("=== Work Seniority: %s" % seniority_emp)
                        factor = seniority_emp / seniority_config
                        if seniority_emp \
                           and seniority_emp == seniority_config * int(factor):
                            extra_leaves = \
                                job.extra_annual_leaves_for_work_seniority\
                                * factor
                            if create_extra_leave:
                                # only create AR for extra leave
                                allocation_days = extra_leaves
                            else:
                                # Create allocation request as usual
                                allocation_days += extra_leaves
                            description += ' - Plus %s extra leave(s)' \
                                ' for %s year(s) '\
                                % (extra_leaves, seniority_emp / 12) + \
                                'working seniority'
            logging.info("=== Allocation days: %s" % allocation_days)
            record = self.create_allo_request(
                employee.id, days=allocation_days,
                update_extra_leave=update_extra_leave,
                name=description, allo_date=allo_date)
            res.append(record.id)
            description = ''
        return res

    @api.model
    def create_allocation_request_for_sick_leave_paid(self):
        """
        Create 5 sick leaves (paid) for all employees every first day
        of the year.
        """
        logging.info(
            "*** START: create_allocation_request_for_sick_leave_paid")
        ctx = dict(self._context) or {}
        res = []
        contract_obj = self.env['hr.contract']
        allo_date = datetime.today()
        sick_leaves_paid_rec = self.env.ref(
            'trobz_hr_holiday_vn.hr_holiday_status_sick_paid')
        logging.info(
            "======= ALLOCATION DATE: %s======"
            % allo_date)
        domain = [
            ('is_trial', '=', False),
            ('employee_id.active', '=', True),
            ('date_start', '<=', allo_date),
            '|',
            ('date_end', '>=', allo_date),
            ('date_end', '=', False),
        ]
        contracts = contract_obj.search(domain)
        for contract in contracts:
            # Create allocation request with
            # allocation days = Yearly Sick Leave
            employee = contract.employee_id
            allocation_days = contract.yearly_sick_leaves
            if allocation_days:
                logging.info("=== EMPLOYEE %s ===" % employee.name)
                if not employee.country_id:
                    logging.info("=== No defined nationality.")
                # Specific for TMS
                description = 'Allocation Request for sick leaves - %s'\
                              % allo_date.strftime('%Y')
                logging.info("=== Allocation days: %s" % allocation_days)
                record = self.create_allo_request(
                    employee.id, days=allocation_days,
                    leave_type=sick_leaves_paid_rec,
                    name=description,
                    allo_date=allo_date)
                res.append(record.id)
            else:
                logging.info(
                    "=== %s still remains %s days for sick leaves (paid)==="
                    % (employee.name, contract.yearly_sick_leaves))
        return res

    @api.model
    def update_missing_allocation_request_previous_month(self):
        """
        Update missing allocation for new contract in previous month
        """
        logging.info(
            "*** START: update_missing_allocation_request_previous_month")
        first_date_current_month = datetime.today().replace(day=1)
        first_date_last_month = first_date_current_month - relativedelta(months=1)
        str_first_date_last_month = first_date_last_month.strftime(DF)
        fifteenth_date_last_month = first_date_last_month + relativedelta(day=15)
        twentyfive_date_last_month = first_date_last_month + relativedelta(day=25)
        str_fifteenth_date_last_month = fifteenth_date_last_month.strftime(DF)
        str_twentyfive_date_last_month = twentyfive_date_last_month.strftime(DF)
        ctx = dict(self._context) or {}
        contract_obj = self.env['hr.contract'].search([
            ('date_start', ">=", str_first_date_last_month),
            ('date_start', "<=", str_twentyfive_date_last_month),
            ('is_trial', '=', False),
            ('employee_id.active', '=', True),
            ])
        res = []
        for contract in contract_obj:
            description = ''
            extra_leaves = 0
            employee = contract.employee_id
            param = self.env.ref('tms_modules.country_add_extra_leave')
            if not param or \
                    (param and employee.country_id.code in eval(param.value)):
                # Calculate extra leaves
                job = contract and contract.job_id or False
                if not job:
                    logging.info(
                        "=== There is no job title defined on %s's contract."
                        % employee.name)
                else:
                    # Calculate extra leave for Work Seniority
                    # Plus to total_extra_leave
                    # if work seniority of this employee equal to
                    #    factor * work seniority interval (defined on job)
                    seniority_config = job.work_seniority_interval * 12
                    if not seniority_config:
                        logging.info(
                            "=== Work Seniority Interval is not set on %s job"
                            % job.name)
                    else:
                        # work_seniority_month from hire_date to allo_date
                        ctx.update({'to_date': first_date_current_month})
                        seniority_emp = employee.with_context(ctx).\
                            work_seniority_month
                        logging.info("=== Work Seniority: %s" % seniority_emp)
                        factor = seniority_emp / seniority_config
                        if seniority_emp \
                           and seniority_emp == seniority_config * int(factor):
                            extra_leaves = \
                                job.extra_annual_leaves_for_work_seniority\
                                * factor

                            description = ' - Plus %s extra leave(s)' \
                                ' for %s year(s) '\
                                % (extra_leaves, seniority_emp / 12) + \
                                'working seniority'

            if contract.date_start <= str_fifteenth_date_last_month:
                
                logging.info(
                    '===== START update missing allocation request for %s'
                    % employee.name + " - Contract's ID: \
                        %s" % contract.id + ' =====')
                new_id = self.create_allo_request(
                    employee.id,
                    allo_date=first_date_last_month,
                    days=1 + extra_leaves,
                    name='Allocation Request for previous month \
                        (%s).' % (
                         first_date_last_month.strftime('%m-%Y')) + description
                )
            elif str_fifteenth_date_last_month < contract.date_start \
                    <= str_twentyfive_date_last_month:
                logging.info(
                    '===== START update missing allocation request for %s'
                    % employee.name + " - Contract's ID: \
                        %s" % contract.id + ' =====')
                new_id = self.create_allo_request(
                    employee.id,
                    allo_date=first_date_last_month,
                    days=0.5 + extra_leaves,
                    name='Allocation Request for previous month \
                         (%s).' % (
                         first_date_last_month.strftime('%m-%Y')) + description
                )
                logging.info(
                    '===== END update missing allocation request \
                        for %s' % employee.name + ' =====')
            if new_id:
                res += new_id
                logging.info(
                    "*** END: update_missing_allocation_request_previous_month")
                logging.info('*** UPDATED %s' % str(res))
        return True

    @api.model
    def function_update_allocation_request_for_work_seniority(self):
        """
        Update extra leaves for TMS
        """
        logging.info("*** START: update_allocation_request_for_work_seniority")

        # UPDATE month_year 2015-11 (v7) to 11/2015 (v8)
        allocations = self.search([])
        for allocation in allocations:
            if not allocation.allo_date and not allocation.month_year:
                continue
            elif not allocation.allo_date and allocation.month_year:
                allocation.allo_date = allocation.month_year + '-01'
            allocation.month_year = datetime.strptime(
                allocation.allo_date, DF).strftime('%m/%Y')

        # UPDATE EXTRA LEAVES
        # In TMS, only exist AR from 01/2013
        # S0 we need create_extra_leave in context
        #     for creating AR before 01/2013
        #     to only create AR with extra leaves
        # - If existed allocation request, update
        #     days = days on current AR + extra days
        # - If not, create allocation request with
        #     days = extra days
        res = []
        emp_obj = self.env['hr.employee']
        context = dict(self._context) or {}
        context.update({
            'create_extra_leave': True,  # Create new AR with extra leaves only
        })
        emps = emp_obj.search([('country_id.code', '=', 'VN')])
        for emp in emps:
            logging.info('===== START update extra allocation request for %s'
                         % emp.name + ' =====')
            if not emp.hire_date:
                logging.info('=== NO employee hired date')
                continue
            hire_date = datetime.strptime(emp.hire_date, DF) + \
                relativedelta(months=12)
            first_date_of_month = datetime.now()
            while hire_date <= first_date_of_month:
                new_id = self.with_context(context).\
                    add_allocation_request_each_month(
                        allo_date=hire_date.strftime(DF), emps=[emp.id],
                        update_extra_leave=True, create_extra_leave=True)
                res += new_id
                hire_date += relativedelta(months=12)
            logging.info('===== END update extra allocation request for %s'
                         % emp.name + ' =====')
        logging.info("*** END: update_allocation_request_for_work_seniority")
        logging.info('*** UPDATED %s' % str(res))
        return True

    @api.model
    def function_update_booking_chart_for_leave_request(self):
        logging.info(
            "====== START: UPDATE BOOKING RESOURCE FOR LEAVE REQUEST =======")
        line_env = self.env['hr.holidays.line']

        # find hr_holidays_ids having existing booking resources
        sql = '''
            SELECT substring(origin_ref from 13 for 5) FROM booking_resource
            WHERE origin_ref ilike 'hr.holidays,%';
        '''
        self.env.cr.execute(sql)
        datas = self.env.cr.fetchall()
        existing_leave_booking_ids = []
        for data in datas:
            existing_leave_booking_ids.append(int(data[0]))

        # find hr_holidays_ids not having existing booking resources
        not_existing_leave_booking_ids = []
        today = fields.Date.today()
        line_objs = line_env.search([('last_date', '>=', today)])
        for line in line_objs:
            if line.holiday_id.type == 'remove' and \
                    line.holiday_id.id not in existing_leave_booking_ids:
                not_existing_leave_booking_ids.append(line.holiday_id.id)

        # creating missing booking resources
        if not_existing_leave_booking_ids:
            not_existing_leave_bookings = self.browse(
                not_existing_leave_booking_ids)
            not_existing_leave_bookings.create_booking_resource()

        logging.info(
            "====== END: UPDATE BOOKING RESOURCE FOR LEAVE REQUEST =======")
        return True

    def _generate_order_by(self, order_spec, query):
        res = super(hr_holidays, self)._generate_order_by(order_spec, query)
        if "month_year" in res:
            res = res.replace("month_year", "allo_date")
        return res

    @api.multi
    def holidays_first_validate(self):
        self.check_approve_permission()
        super(hr_holidays, self).holidays_first_validate()
        self._send_email_remain_holiday_second_approval()
        return True

    @api.multi
    def _send_email_remain_holiday_second_approval(self):
        for holiday in self:
            template = holiday.env.ref(
                'tms_modules.email_template_holiday_second_approval')
            if template:
                logging.info("=== Send email remain second approval ====")
                logging.info("START Send holiday reminder email")
                template.send_mail(holiday.id)
                logging.info("END Send holiday reminder email")

    @api.model
    @api.depends('group_profile_id')
    def _check_user_is_emp_manager(self, user_id):
        res = False
        if user_id and user_id != 1:
            profile_sysadmin_manager = self.env.ref(
                'tms_modules.group_profile_tms_sysadmin_manager')
            profile_team_manager = self.env.ref(
                'tms_modules.group_profile_tms_delivery_team_manager')
            user = self.env['res.users'].browse(user_id)
            user_profiles = [
                profile_sysadmin_manager.id, profile_team_manager.id]
            # It's better when we use group_ext_ids
            if user.group_profile_id and\
                    user.group_profile_id.id in user_profiles:
                res = True
        return res

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
        Allow to display leave requests of employee
        belong to user's subordinate
        """
        context = self._context and self._context.copy() or {}
        user_id = context.get('uid', False)
        if self._check_user_is_emp_manager(user_id):
            related_emp_ids = self.env['hr.employee'].search(
                [('user_id', '=', user_id)])
            if related_emp_ids:
                dict_ids = [related_emp_ids.id]
                dict_ids = dict_ids + related_emp_ids.child_ids.ids + \
                    related_emp_ids.approval_employee_ids.ids
                args.append(('employee_id', 'in', dict_ids))
        return super(hr_holidays, self).search(
            args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0,
                   limit=None, orderby=False, lazy=False):
        context = self._context and self._context.copy() or {}
        user_id = context.get('uid', False)

        if self._check_user_is_emp_manager(user_id):
            related_emp_ids = self.env['hr.employee'].search(
                [('user_id', '=', user_id)])
            if related_emp_ids:
                dict_ids = [related_emp_ids.id]
                dict_ids = dict_ids + related_emp_ids.child_ids.ids + \
                    related_emp_ids.approval_employee_ids.ids
                domain.append(
                    ['employee_id', 'in', dict_ids])
        else:
            domain = domain
        return super(hr_holidays, self).read_group(
            domain=domain, fields=fields, groupby=groupby,
            offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )

    @api.multi
    def to_partner_mail(self):
        """
        Leave request notification email to be sent in cc to Partner in case
        the employee as a "Dedicated Resource Contract"
        for this Partner at the time of the Leave Request
        """
        partner_emails = []
        employee_id = self.employee_id and self.employee_id.id or False
        if employee_id:
            hr_drc_obj = self.env['hr.dedicated.resource.contract']
            hr_drc_ls = hr_drc_obj.search([('employee_id', '=', employee_id)])
            res_contracts = []
            for dedicated_contract in hr_drc_ls:
                contract_start = dedicated_contract.start_date and \
                    datetime.strptime(
                        dedicated_contract.start_date, '%Y-%m-%d').date() \
                    or False
                contract_end = dedicated_contract.end_date and \
                    datetime.strptime(
                        dedicated_contract.end_date, '%Y-%m-%d').date() \
                    or False
                for line in self.holiday_line:
                    line_start = datetime.strptime(
                        line.first_date, '%Y-%m-%d').date()
                    line_end = datetime.strptime(
                        line.last_date, '%Y-%m-%d').date()
                    if contract_end:
                        is_overlap = (contract_start <= line_end) and \
                            (contract_end >= line_start)
                    else:
                        is_overlap = (line_end >= contract_start)
                    if is_overlap:
                        res_contracts.append(dedicated_contract)
                        break

            for contract in res_contracts:
                partner_email = contract.name and contract.name.email or ''
                if partner_email:
                    partner_emails.append(partner_email)
        return ', '.join(partner_emails)

    @api.multi
    def create_working_hour(self):
        working_hour_pool = self.env['tms.working.hour']
        for request in self:
            if request.type and request.type == 'add':
                # Ignore the allocation request
                continue

            employee = request.employee_id
            for line in request.holiday_line:
                activity = line.holiday_status_id.activity_id

                vals = {
                    'employee_id': employee.id,
                    'date': line.first_date,
                    'user_id': employee.user_id.id,
                    'name': activity.name or 'Days off',
                    'tms_activity_id': activity.id,
                    'hr_holiday_line_id': line.id
                }

                # Create working hour from first_date+1 to last_date-1
                first_date = datetime.strptime(
                    line.first_date, '%Y-%m-%d').date()
                last_date = datetime.strptime(
                    line.last_date, '%Y-%m-%d').date()
                date = first_date

                while date <= last_date:

                    # TODO: should be based on employee working schedule
                    date_in_week = date.strftime("%A")
                    if date_in_week in ("Saturday", "Sunday"):
                        date = date + timedelta(1)
                        continue

                    duration_hour = 8

                    if date == first_date:
                        # Create working hour on first_date
                        if line.first_date_type in ['morning', 'afternoon']:
                            duration_hour = 4
                        # if line.first_date == line.last_date: this is not
                        # a special case.
                    elif date == last_date:
                        # Create working hour on first_date
                        if line.last_date_type in ['morning', 'afternoon']:
                            duration_hour = 4

                    vals.update({
                        'duration_hour': duration_hour,
                        'date': date.strftime("%Y-%m-%d"),
                    })
                    working_hour_pool.create(vals)
                    date = date + timedelta(1)
        return True

    @api.multi
    def holidays_validate(self):
        """
        - Auto create a working hour record when approving a leave request
        - Auto add approved records into booking resource and show up in
        Booking Resource Allocation
        """
        self.check_approve_permission()
        # if LR (Leave Request) is in state 'request_cancelation'
        # LR can go back to state 'validate' again
        # to avoid duplicate working_hour, booking_resource,
        # we should clean it before creating a new one
        context_temp = self._context and self._context.copy() or {}
        context_temp.update(
            {
                'sudo': True
            })
        for rec in self:
            if rec.state == 'cancel_request':
                self.with_context(context_temp).remove_working_hour()
                self.remove_booking_resource()

        super(hr_holidays, self).holidays_validate()

        self.with_context(context_temp).create_working_hour()
        self.create_booking_resource()

        self.create_resource_allocation_per_sprint()
        return True

    @api.model
    def check_approve_permission(self):
        current_user = self.env['res.users'].browse(self._uid)
        is_manager = current_user.has_group(
            'tms_modules.group_profile_tms_delivery_team_manager')
        is_sysadmin = current_user.has_group(
            'tms_modules.group_profile_tms_sysadmin_manager')
        is_hr_manager = current_user.has_group('base.group_hr_manager')
        if is_hr_manager:
            return True
        elif (is_manager or is_sysadmin) and\
                self._uid == self.employee_id.user_id.id:
            raise Warning('Permission denied',
                          'Sorry, you are not allowed to confirm your leave request. Please contact HR or Manager to do this')
        return True

    @api.multi
    def remove_working_hour(self):
        """
        Remove working hour records when canceling a leave request
        """
        working_hour_env = self.env['tms.working.hour']
        working_recs = working_hour_env.browse()
        for request in self:
            if request.type and request.type == 'add':
                continue
            for line in request.holiday_line:
                # Remove working hours in leave request line's period
                activity_id = line.holiday_status_id.activity_id.id
                domain = [
                    ('user_id', '=', request.employee_id.user_id.id),
                    ('tms_activity_id', '=', activity_id),
                    ('date', '>=', line.first_date),
                    ('date', '<=', line.last_date),
                    ('hr_holiday_line_id', '=', line.id),
                ]
                working_recs += working_hour_env.search(domain)
        working_recs.unlink()
        return True

    @api.multi
    def holidays_cancel(self):
        """
        Remove working hour when canceling a leave request
        Remove records in booking resource when canceling leave requests
        """
        res = super(hr_holidays, self).holidays_cancel()

        self.with_context({'sudo': True}).remove_working_hour()
        self.remove_booking_resource()
        return res

    @api.multi
    def change_state_to_cancel(self):
        """
        Manager accepts the Cancellation Request from employee.
        Then status of this leave request is `cancel`
        """
        res = super(hr_holidays, self).change_state_to_cancel()
        self.with_context({'sudo': True}).remove_working_hour()
        self.remove_booking_resource()
        return res

    @api.multi
    def button_sick_unpaid_to_sick_paid(self):
        self.change_to_sick_type(
            'default_unpaid_sick_leave_types',
            'default_sick_leave_paid_new')

    @api.multi
    def button_sick_unpaid_to_sick_social_ins(self):
        self.change_to_sick_type(
            'default_unpaid_sick_leave_types',
            'default_sick_leave_social_ins')

    @api.multi
    def button_sick_paid_to_sick_social_ins(self):
        self.change_to_sick_type(
            'default_sick_leave_paid_new',
            'default_sick_leave_social_ins')

    @api.multi
    def button_sick_paid_to_sick_unpaid(self):
        self.change_to_sick_type(
            'default_sick_leave_paid_new',
            'default_unpaid_sick_leave_types')

    @api.multi
    def button_sick_social_ins_to_sick_paid(self):
        self.change_to_sick_type(
            'default_sick_leave_social_ins',
            'default_sick_leave_paid_new')

    @api.multi
    def button_sick_social_ins_to_sick_unpaid(self):
        self.change_to_sick_type(
            'default_sick_leave_social_ins',
            'default_unpaid_sick_leave_types')

    @api.multi
    def change_to_sick_type(self, from_sick_type, to_sick_type):
        line_obj = self.env['hr.holidays.line']
        param_obj = self.env['ir.config_parameter']
        status_obj = self.env['hr.holidays.status']
        config_value = param_obj.get_param(from_sick_type,)
        from_sick_leave = config_value and eval(config_value) or []
        to_sick_leave = param_obj.get_param(to_sick_type) or None 
        sick_leave_recs = status_obj.search(
            [('name', '=', to_sick_leave and eval(to_sick_leave)[0] or '')])
        if not sick_leave_recs:
            return True
        update_ids = []
        for holiday in self:
            for line in holiday.holiday_line:
                if line.holiday_status_id.name not in from_sick_leave:
                    continue
                update_ids.append(line.id)
        line_recs = line_obj.browse(update_ids)
        line_recs.write(
            {'holiday_status_id': sick_leave_recs[0].id})
        return True

    @api.multi
    def create_booking_resource(self):
        booking_resource_env = self.env['booking.resource']
        ir_model_env = self.env['ir.model.data']

        for approved_request in self:
            if approved_request.type == 'add':
                # Ignore the ALLOCATION REQUEST
                continue
            # For each holiday line, add into booking resource
            for line in approved_request.holiday_line:

                # create dedicated resource contract
                is_dedicated_resource = approved_request.employee_id and \
                    approved_request.employee_id.is_dedicated_resource or False

                # only create if this employee is a dedicated resource
                # and leave request type is not 'Casual Leave (paid)'
                casual_leave_paid_obj = ir_model_env.get_object_reference(
                    'hr_holidays', 'holiday_status_cl')
                if not is_dedicated_resource:
                    continue

                if not line.holiday_status_id:
                    continue

                if line.holiday_status_id.id != casual_leave_paid_obj[1]:
                    dedicated_resource_chart_obj = \
                        ir_model_env.get_object_reference(
                            'tms_modules',
                            'dedicated_resource_contract_chart')
                    dedicated_resource_vals = {
                        'name': 'Day Off %s day(s)' %
                                abs(line.number_of_days_temp),
                        'resource_ref':
                        'hr.employee,%s' % approved_request.employee_id.id,
                        'origin_ref': 'hr.holidays,%s' % approved_request.id,
                        'message': approved_request.name,
                        'date_start': line.first_date,
                        'date_end': line.last_date,
                        'css_class': 'red',
                        'chart_id': dedicated_resource_chart_obj[1],
                    }
                    booking_resource_env.create(dedicated_resource_vals)
        return True

    @api.multi
    def create_resource_allocation_per_sprint(self):
        resource_alloc_pool = self.env['hr.resource.allocation']
        date_formate = '%Y-%m-%d'
        for approved_request in self:

            if approved_request.type == 'add':
                continue
            # For each holiday line, create resource allocations
            for line in approved_request.holiday_line:
                day_off_in_week = 0
                # get list of sprints date
                first_day = datetime.strptime(line.first_date, date_formate)
                last_day = datetime.strptime(line.last_date, date_formate)
                sprint_start = first_day + timedelta(days=(
                    5 - first_day.weekday()
                ))
                sprint_end = last_day + timedelta(days=(
                    5 - last_day.weekday()
                ))
                sprints = []
                sprints.append(sprint_start)
                date_tmp = sprint_start
                while date_tmp < sprint_end:
                    date_tmp = date_tmp + timedelta(days=7)
                    if date_tmp == sprint_end:
                        sprints.append(date_tmp)
                        break
                    sprints.append(date_tmp)
                if sprints:
                    weeks_off = len(sprints)  # Number of week off
                    activity_id = line.holiday_status_id and \
                        line.holiday_status_id.activity_id and \
                        line.holiday_status_id.activity_id.id or False
                    for sprint in sprints:
                        if weeks_off > 1:
                            sp_date_start = sprint - timedelta(days=6)
                            sp_date_end = sprint
                            if (first_day > sp_date_start) and \
                                    (sp_date_end < last_day):
                                day_off_in_week = (
                                    sp_date_end - first_day).days
                            elif (first_day < sp_date_start) and \
                                    (sp_date_end < last_day):
                                day_off_in_week = 5
                            elif (first_day < sp_date_start) and \
                                    (last_day < sp_date_end):
                                day_off_in_week = (
                                    last_day - sp_date_start).days
                        else:
                            day_off_in_week = float(line.number_of_days)
                        occupancy = (day_off_in_week * 20)
                        vals = {
                            'employee_id': approved_request.employee_id.id,
                            'activity_id': activity_id,
                            'sprint': datetime.strftime(sprint, '%Y-%m-%d'),
                            'occupancy': occupancy,
                            'holiday_id': line.id
                        }
                        resource_alloc_pool.create(vals)
        return True

    @api.multi
    def remove_booking_resource(self):
        booking_resource_pool = self.env['booking.resource']
        for record in self.ids:
            cancel_requests_recs = booking_resource_pool.search(
                [('origin_ref', 'ilike', 'hr.holidays,%s' % record)])
            cancel_requests_recs.unlink()
        return True
