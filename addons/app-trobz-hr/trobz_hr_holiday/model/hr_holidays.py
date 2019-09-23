# -*- encoding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
from datetime import date, datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import Warning
from openerp.osv import osv, fields as fields_v7
import logging
from dateutil.relativedelta import relativedelta


class HrHolidays(models.Model):
    _inherit = "hr.holidays"

    # TODO
    # To be removed after fixing
    # https://github.com/odoo/odoo/issues/2605
    def init(self, cr):
        cr.execute("""
        ALTER TABLE hr_holidays ALTER COLUMN holiday_status_id DROP NOT NULL;
        ALTER TABLE hr_holidays DROP CONSTRAINT hr_holidays_type_value;
        ALTER table hr_holidays
                  ADD constraint hr_holidays_type_value
                  CHECK((holiday_type='employees')
                  or (holiday_type='employee' AND employee_id IS NOT NULL)
                  or (holiday_type='category' AND category_id IS NOT NULL));
                """)

    @api.multi
    def _check_date(self):
        """
        Override function
        - Remove all source code in this function
            because now all processes base on leave lines
            instead of leave request
        - Move this control into leave lines
        """
        return True

    @api.multi
    def _get_can_reset(self):
        """
        Override function
        User can reset a leave request
            if it is its own leave request or if he is an HR Officer.
        """
        user = self.env.user

        for holiday in self:
            if user.has_group('base.group_hr_user'):
                holiday.can_reset = True
            elif holiday.employee_id and holiday.employee_id.user_id and\
                            holiday.employee_id.user_id.id == user.id:
                holiday.can_reset = True

    can_reset = fields.Boolean(compute=_get_can_reset, string='Can Reset')

    # Change size of field name
    name = fields.Char(string='Description', size=255)

    # Change date_from, date_to from datetime to date
    date_from = fields.Date()
    date_to = fields.Date()

    # Set Leave Type is not required
    holiday_status_id = fields.Many2one(required=False)

    # New fields
    is_unpaid = fields.Boolean("Filter Unpaid")
    allo_date = fields.Date(readonly=1)
    month_year = fields.Char(string='Period', readonly=1)
    holiday_line = fields.One2many(
        'hr.holidays.line', 'holiday_id',
        readonly=True,
        states={'draft': [('readonly', False)],
                'confirm': [('readonly', False)]})
    is_over_allocation_days = fields.Boolean(
        default=False,
        help='The balance of allowed holidays is negative, \
        it is a request for advance leaves'
    )
    employee_ids = fields.Many2many(
        'hr.employee', 'hr_holiday_employee_rel',
        'holiday_id', 'employee_id',
        string="Employees",
        readonly=True,
        states={'draft': [('readonly', False)],
                'confirm': [('readonly', False)]}
    )

    _constraints = [
        # Override to remove this constraint
        (_check_date, 'You can not have 2 leaves that overlaps on same day!',
            ['date_from', 'date_to']),
    ]

    _sql_constraints = [
        # Override to change this constraints base on employees holiday_type
        ('type_value',
         """CHECK((holiday_type='employees')
         or (holiday_type='employee' AND employee_id IS NOT NULL)
         or (holiday_type='category' AND category_id IS NOT NULL))""",
         """The employee or employee category of this request is missing.
         Please make sure that your user login is linked to an employee."""),
    ]

    @api.onchange('holiday_type')
    def _onchange_type(self):
        """
        @param holiday_type: employee/employees
        @return:
            - If holiday type is employees, set employee_id = False
            - If holiday type is employee, set employee_ids = []
        """
        emp_obj = self.env['hr.employee']
        if self.holiday_type == 'employee':
            employees = emp_obj.search([('user_id', '=', self._uid)])
            self.employee_ids = []
            self.category_id = False
            self.employee_id = employees and employees[0].id
        elif self.holiday_type == 'employees':
            self.employee_id = False
            self.category_id = False
        else:
            self.employee_ids = []
            self.employee_id = False

    @api.multi
    def check_holidays(self):
        """
        For each leave request line, check the remaining leaves enough or not
        If balance < 0, update is_over_allocation_days and show
            the warning on leave request from
        """

        is_over_allocation_days = False
        for record in self:
            if record.type == 'add':
                continue

            # Check leaves balance for leave requests
            # leaves_rest: remaining_leaves of employee by leave type
            # leave_asked: number_of_days of holiday_line
            if record.holiday_type == 'employee'\
               and record.employee_id:
                for i in record.holiday_line:
                    leave_asked = -(i.number_of_days)
                    if leave_asked < 0.00:
                        if i.holiday_status_id \
                           and not i.holiday_status_id.limit:
                            status_id = i.holiday_status_id.id
                            employee_id = record.employee_id.id
                            status = i.holiday_status_id.get_days(employee_id)
                            leaves_rest = status[status_id]['remaining_leaves']
                            if (record.state == 'validate' and
                                leaves_rest < 0) or \
                                    (record.state != 'validate' and
                                     leaves_rest < -(leave_asked)):
                                # 1. For approved leave request,
                                # the number of days on holiday lines
                                # is taken into the remaining leaves.
                                # if remaining leaves < 0, means balance < 0
                                # 2. For leave request not approved
                                # the remaining leaves must be greater than
                                # number of days on leave request line,
                                # means balance < 0
                                is_over_allocation_days = True
            elif record.holiday_type == 'category' and record.category_id:
                for i in record.holiday_line:
                    leave_asked = -(i.number_of_days)
                    if leave_asked < 0.00:
                        if not i.holiday_status_id.limit:
                            cate_id = record.category_id.id
                            status_id = i.holiday_status_id.id
                            status = i.holiday_status_id.get_days(cate_id)
                            leaves_rest = status['remaining_leaves']
                            if leaves_rest < -(leave_asked):
                                is_over_allocation_days = True
            record.write({'is_over_allocation_days': is_over_allocation_days})
        return True

    @api.multi
    def holidays_validate(self):
        """
        Override function:
        - When approve the allocation request
            update is_over_allocation_days = False if remmaining_leaves >= 0
        """
        emp_obj = self.env['hr.employee']
        line_obj = self.env['hr.holidays.line']
        status_obj = self.env['hr.holidays.status']

        manager = emp_obj.search([('user_id', '=', self._uid)], limit=1)
        manager = manager and manager.id or False
        val_update = {}
        for record in self:
            if record.state == 'cancel_request':
                # Leave request with status `cancel_request`
                # Only need to update status to `validate`
                continue
            if record.double_validation:
                val_update.update({'manager_id2': manager})
            else:
                val_update.update({'manager_id': manager})

            if record.type == 'add':
                # UPDATE is_over_allocation_days = False
                #     if remmaining_leaves >= 0
                # When approve allocation requests
                leaves_rest = status_obj.get_days(record.employee_id.id)
                status_id = record.holiday_status_id.id
                leaves_rest = leaves_rest\
                    and leaves_rest[status_id]['remaining_leaves'] or 0
                if leaves_rest >= 0:
                    domain = [('is_over_allocation_days', '=', True),
                              ('type', '=', 'remove'),
                              ('employee_id', '=', record.employee_id.id)]
                    leaves = self.search(domain)
                    leaves.check_holidays()

            if record.holiday_type == 'employee' and record.type == 'remove':
                # Create calendar event base leave request lines
                for line in record.holiday_line:
                    meeting_obj = self.env['calendar.event']
                    categ_ids = line.holiday_status_id.categ_id\
                        and [(6, 0, [record.holiday_status_id.categ_id.id])]\
                        or []
                    start_date = datetime.strptime(line.first_date, DF)
                    stop_date = datetime.strptime(line.last_date, DF)
                    meeting_vals = {
                        'name': record.name or _('Leave Request'),
                        'categ_ids': categ_ids,
                        'duration': line.number_of_days * 8,
                        'description': record.notes,
                        'user_id': record.user_id.id,
                        'start': start_date.strftime("%Y-%m-%d 00:00:00"),
                        'stop': stop_date.strftime("%Y-%m-%d 00:00:00"),
                        'allday': False,
                        'state': 'open',  # block this date in the calendar
                        'class': 'confidential'
                    }
                    # Add the partner_id (if exist) as an attendee
                    if record.user_id and record.user_id.partner_id:
                        partner_ids = [(4, record.user_id.partner_id.id)]
                        meeting_vals['partner_ids'] = partner_ids

                    context = dict(self._context)
                    context.update({'no_email': True})
                    meeting = meeting_obj.with_context(
                        context).create(meeting_vals)
                    self._create_resource_leave([record])
                    val_update.update({'meeting_id': meeting.id})

            elif record.holiday_type in ('category', 'employees'):
                if record.holiday_type == 'category':
                    domain = [('category_ids', 'child_of',
                               [record.category_id.id])]
                    emp_ids = emp_obj.search(domain)
                else:
                    emp_ids = [employee.id for employee in record.employee_ids]
                if not emp_ids:
                    continue

                leaves = []
                for employee_id in emp_ids:
                    total_days = 0.0
                    # create leave request for each employee
                    leave = self.create({
                        'name': record.name,
                        'holiday_type': 'employee',
                        'employee_id': employee_id,
                        'number_of_days_temp': record.number_of_days_temp,
                        'date_from': record.date_from,
                        'date_to': record.date_to
                    })
                    leaves.append(leave)

                    # create leave request lines
                    for line in record.holiday_line:
                        total_days += line.number_of_days
                        line_obj.create({
                            'holiday_id': leave.id,
                            'holiday_status_id': line.holiday_status_id.id,
                            'first_date': line.first_date,
                            'last_date': line.last_date,
                            'first_date_type': line.first_date_type,
                            'last_date_type': line.last_date_type,
                            'number_of_days': line.number_of_days,
                        })

                    # update number of date in leave request
                    leave.write({'number_of_days_temp': total_days})

                # Approve all leave request created from
                #     leave request of many employees
                for leave in leaves:
                    for sig in ('confirm', 'validate', 'second_validate'):
                        leave.signal_workflow(sig)
        val_update.update({'state': 'validate'})
        self.write(val_update)
        return True

    @api.multi
    def change_state_to_cancel(self):
        """
        Manager accepts the Cancellation Request from employee.
        Then status of this leave request is `cancel`
        """
        self.write({'state': 'cancel'})
        for record in self:
            # Delete the meeting
            if record.meeting_id:
                record.meeting_id.unlink()
            record.signal_workflow('accept_cancellation')
        self._remove_resource_leave()
        return True

    @api.model
    def create_allo_request(
            self, employee_id, days, leave_type=False,
            allo_date=False, update_extra_leave=False,
            name=_('Allocation request for every month')):
        """
        Create allocation request every month for an employee
        If existed, update name and allocation days.
        @param name: default "Allocation Request for every month"
        @param leave_type: default "Casual Leave"
        @param employee_id: Employee ID
        @param days: monthly_paid_leave + extra leaves (if any) on contract
        @param allo_date: date create allocation request
        @return: New validated allocation request
        """
        allocation = False
        status_obj = self.env['hr.holidays.status']
        param_obj = self.env['ir.config_parameter']
        if not leave_type:
            # If there have no an indicated leave type
            # Find the leave type defined in the parameter
            # default_leave_type_to_add_allocation_each_month
            status_name = 'default_leave_type_to_add_allocation_each_month'
            status_name = param_obj.get_param(status_name)
            leave_type = status_obj.search([('name', '=', status_name)])
            if not leave_type:
                return allocation

        # Find the allocation request of the indicated employee in this month
        if not allo_date:
            allo_date = date.today()
        domain = [('employee_id', '=', employee_id),
                  ('type', '=', 'add'),
                  ('holiday_status_id', '=', leave_type.id),
                  ('month_year', '=', allo_date.strftime('%m/%Y')),
                  ('number_of_days_temp', '=', days),
                  ]
        allocation = self.search(domain)
        if allocation:
            # Do nothing or update if needed
            allocation = allocation[0]
            logging.info(
                '=== Allocation request was already existed (ID: %s)'
                % (allocation.id)
            )
            if update_extra_leave and days > 0:
                # update number_of_days of AR if:
                # - update_extra_leave = True
                #     + Use in script re-calculate for old data
                #     + Use in re-run scheduler create AR
                #        for specific date, employee
                # - New allocation days > allocation days on this AR
                updated_days = allocation.number_of_days_temp + days
                name += ' - Auto update the duration from %s to %s'\
                    % (allocation.number_of_days_temp, updated_days)
                allocation.write({
                    'name': name,
                    'number_of_days_temp': updated_days
                })
                logging.info(
                    '=== UPDATE allocation request (ID: %s, %s, %s)'
                    % (allocation.id, name, updated_days)
                )
        else:
            # Create allocation request
            values = {
                'name': name,
                'holiday_status_id': leave_type.id,
                'holiday_type': 'employee',
                'employee_id': employee_id,
                'number_of_days_temp': days,
                'type': 'add',
                'allo_date': allo_date,
                'month_year': allo_date.strftime('%m/%Y'),
            }
            allocation = self.create(values)
            for sig in ('confirm', 'validate', 'second_validate'):
                allocation.signal_workflow(sig)
            logging.info(
                '=== CREATE allocation request (ID: %s)'
                % (allocation.id)
            )
        return allocation

    @api.model
    def add_allocation_request_each_month(
            self, allo_date=None, emps=None, update_extra_leave=False):
        """
        Scheduler function:
        Add allocation request at beginning of every month
        Only Create AR for the employees start working before 15th/M
        @param year_month: indicated period to create AR
            Example: ('2015-01-01', list of employee IDs)
        @param emps: list employee to create AR
        @param update_extra_leave:
            If active, allow to update existed AR,
                days= current number_of_days + extra leaves
            If not, only create new AR if not exist.
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
        # Create allocation request for contracts:
        # Official contracts (is_trial is inactive)
        # Start the 15th/Month
        # End after 15th/Month
        domain = [
            ('date_start', '<=', str_fifteenth_date),
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
            allocation_days = contract.monthly_paid_leaves
            employee = contract.employee_id
            logging.info("=== EMPLOYEE %s" % employee.name)
            description = 'Allocation Request for every month'
            job = contract and contract.job_id or False
            if not job:
                logging.warning(
                    "=== There is no job title defined on %s's contract."
                    % employee.name)
            else:
                # Calculate extra leave for Work Seniority
                # Plus to total_extra_leave
                # if work seniority of this employee equal to
                #    factor * work seniority interval (defined on job)
                seniority_config = job.work_seniority_interval * 12
                if not seniority_config:
                    logging.warning(
                        "=== Work Seniority Interval is not set on %s job"
                        % job.name)
                else:
                    # work_seniority_month from hire_date to allo_date
                    ctx.update({'to_date': allo_date})
                    seniority_emp = employee.with_context(ctx).\
                        work_seniority_month
                    logging.info(
                        "=== Work Seniority: %s" % seniority_emp)
                    factor = seniority_config > 0 and \
                        seniority_emp / seniority_config or 0
                    if seniority_emp \
                       and seniority_emp == seniority_config * int(factor):
                        extra_leaves = \
                            job.extra_annual_leaves_for_work_seniority * factor
                        allocation_days += extra_leaves
                        description += ' - Plus %s extra leave(s)' \
                            ' for %s year(s) '\
                            % (extra_leaves, seniority_emp / 12) + \
                            'working seniority'
            record = self.create_allo_request(
                employee.id, days=allocation_days,
                update_extra_leave=update_extra_leave,
                name=description, allo_date=allo_date)
            res.append(record.id)
        return res

    @api.model
    def create(self, vals):
        """ For Leave Request, The number_of_days of
            Leave Request is sum of number_of_days of Leave Request lines
            For Allocation Request, Update these fields:
            - Allocation created date
            - Month/year
        """
        context = self._context
        if context and context.get('default_type', False):
            vals['type'] = context['default_type']

        line_obj = self.env['hr.holidays.line']
        emp_obj = self.env['hr.employee']

        if vals.get('type', False) == 'add':
            # Allocation Request
            month_year = vals.get('month_year', False) \
                or date.today().strftime('%m/%Y')
            vals.update({
                'allo_date': date.today(),
                'month_year': month_year
            })
            # Create allocation request line to show to leave summary
            holiday_line = {
                'holiday_status_id': vals.get('holiday_status_id', False),
                'number_of_days': vals.get('number_of_days_temp', 0),
                'first_date_type': False,
                'last_date_type': False
            }
            vals.update({'holiday_line': [[0, False, holiday_line]]})
        else:
            # Leave Request
            holiday_lines = vals.get('holiday_line', False)
            if holiday_lines:
                # Get values of first holiday line
                first_line = holiday_lines[0][2]
                first_date = first_line['first_date']
                last_date = first_line['last_date']
                first_date_type = first_line['first_date_type']
                last_date_type = first_line['last_date_type']
                employee = emp_obj.browse(vals['employee_id'])
                days = line_obj._calculate_days(employee,
                                                first_date,
                                                last_date,
                                                first_date_type,
                                                last_date_type)
                for holiday_line in holiday_lines[1:]:
                    # Fore in each the rest of holiday line
                    line = holiday_line[2]
                    if line:
                        line_first_date = line['first_date']
                        line_last_date = line['last_date']
                        line_first_date_type = line['first_date_type']
                        line_last_date_type = line['last_date_type']
                        days += line_obj._calculate_days(employee,
                                                         line_first_date,
                                                         line_last_date,
                                                         line_first_date_type,
                                                         line_last_date_type)
                        if line_first_date < first_date:
                            first_date = line_first_date
                        if line_last_date > last_date:
                            last_date = line_last_date
                vals['date_from'] = first_date
                vals['date_to'] = last_date
                vals['number_of_days_temp'] = days
        return super(HrHolidays, self).create(vals)

    @api.multi
    def write(self, vals):
        """
        - Update state of leave request line = state of leave request
        - For Leave Request, The number_of_days of
            Leave Request is sum of number_of_days of Leave Request lines
        """
        line_obj = self.env['hr.holidays.line']
        emp_obj = self.env['hr.employee']
        user_obj = self.env['res.users']

        if vals.get('state') \
                and vals['state'] not in ['draft', 'confirm',
                                          'cancel', 'cancel_request']\
                and not user_obj.has_group('base.group_hr_user'):
            # Add cancel_request in list of status that a normal user
            # can change
            raise Warning(_('You cannot set a leave request as'
                            ' \'%s\'. Contact a human resource manager.')
                          % vals.get('state'))

        for record in self:
            holiday_lines = record.holiday_line
            holiday_line_vals = {}
            # Update number of days to allocation request line
            if record.type == 'add' and 'number_of_days_temp' in vals:
                holiday_line_vals = {
                    'number_of_days': vals['number_of_days_temp']
                }

            # Update state to holiday lines
            if vals.get('state', False):
                holiday_line_vals.update({'state': vals['state']})

            # Update state to holiday lines
            if vals.get('employee_id', False):
                holiday_line_vals.update({'employee_id': vals['employee_id']})

            if holiday_line_vals:
                # Update vals from holiday to holiday lines
                holiday_lines.write(holiday_line_vals)

            # Calculate number_of_days = sum(number_of_days of holiday lines)
            if vals.get('holiday_line', False):
                # Leave Request
                holiday_lines = vals.get('holiday_line', False)
                employee = record.employee_id
                if vals.get('employee_id'):
                    employee = emp_obj.browse(vals['employee_id'])

                # The first holiday line
                # flag: Get number describe action of each row:
                # 0-new; 4-update and 2-delete.
                # In this case, we want to check "DELETE" case
                flag = holiday_lines[0][0]
                line_id = holiday_lines[0][1]
                line_rec = line_id and line_obj.browse(line_id)
                line_vals = holiday_lines[0][2]
                days = record.number_of_days_temp
                # Get old values of the first holiday
                first_date = line_id and line_rec.first_date or False
                last_date = line_id and line_rec.last_date or False
                first_date_type = line_id and line_rec.first_date_type or False
                last_date_type = line_id and line_rec.last_date_type or False

                if flag == 2:
                    # This line is deleted
                    days -= line_rec.number_of_days
                else:
                    # This is new line or updated line
                    # Calculate number_of_days for the first holiday_line
                    if line_vals:
                        # Get changed values on the first holiday
                        # If not, get the old values
                        first_date = line_vals.get('first_date', first_date)
                        last_date = line_vals.get('last_date', last_date)
                        first_date_type = line_vals.get('first_date_type',
                                                        first_date_type)
                        last_date_type = line_vals.get('last_date_type',
                                                       last_date_type)
                        day = line_obj._calculate_days(
                            employee, first_date, last_date, first_date_type,
                            last_date_type)
                        if line_rec:
                            days += day - line_rec.number_of_days
                        else:
                            days += day

                for holiday_line in holiday_lines[1:]:
                    # flag: Get number describe action of each row:
                    # 0-new; 4-update and 2-delete.
                    # In this case, we want to check "DELETE" case
                    flag = holiday_line[0]
                    line_id = holiday_line[1]
                    line_rec = line_id and line_obj.browse(line_id)
                    line_vals = holiday_line[2]

                    # The old values of this holiday_line
                    line_first_date = line_id and line_rec.first_date or False
                    line_last_date = line_id and line_rec.last_date or False
                    line_first_date_type = line_id and \
                        line_rec.first_date_type \
                        or False
                    line_last_date_type = line_id and line_rec.last_date_type \
                        or False

                    if flag == 2:
                        days -= line_rec.number_of_days
                    else:
                        if not line_vals:
                            continue
                        # Get new values of this holiday line
                        line_first_date = line_vals.get(
                            'first_date', line_first_date)
                        line_last_date = line_vals.get(
                            'last_date', line_last_date)
                        line_first_date_type = line_vals.get(
                            'first_date_type', line_first_date_type)
                        line_last_date_type = line_vals.get(
                            'last_date_type', line_last_date_type)
                        day = line_obj._calculate_days(
                            employee, line_first_date, line_last_date,
                            line_first_date_type, line_last_date_type)
                        if line_rec:
                            days += day - line_rec.number_of_days
                        else:
                            days += day

                    # Recalculate date_from = MIN first_date of holiday lines
                    # date_to = MAX last_date of holiday lines
                    if line_first_date < first_date:
                        first_date = line_first_date
                    if line_last_date > last_date:
                        last_date = line_last_date

                vals['date_from'] = first_date
                vals['date_to'] = last_date
                vals['number_of_days_temp'] = days
            super(models.Model, self).write(vals)
        return True

    # TODO: check why the return value of search_count is not correct
    # when overriding search function by using v8 code style.
    def search(self, cr, uid, args, offset=0, limit=None, order=None,
               count=False, context={}):
        """ Override function:
        For leave request, the filter by using leave type must be searched on
            the Leave Request line_ids
        """
        hol_line_obj = self.pool['hr.holidays.line']
        hol_status_obj = self.pool['hr.holidays.status']
        # ticket 3,772 - filter Unpaid payment type
        is_unpaid = False
        for arg in args:
            if arg[0] == 'is_unpaid':
                is_unpaid = True
                del args[args.index(arg)]
                break
        if is_unpaid:
            status_rec_ids = hol_status_obj.search(
                cr, uid, [('payment_type', '=', 'unpaid')]
            )
            result = []
            if status_rec_ids:
                line_ids = hol_line_obj.search(
                    cr, uid, [('holiday_status_id', 'in', status_rec_ids)]
                )
                if line_ids:
                    result = []
                    for line in hol_line_obj.browse(cr, uid, line_ids,
                                                    context=context):
                        if line.holiday_id.id not in result:
                            result.append(line.holiday_id.id)
            args.append(['id', 'in', result])

        # Ticket 2912: The filter by using leave type doesn't work
        # Filter by leave type on leave request line
        # OR leave type on allocation request
        type_value = ''
        for arg in args:
            try:
                if arg.index('type') == 0:
                    type_value = arg[2]
                    break
            except ValueError:
                pass
        if type_value == 'remove':
            value = False
            for arg in args:
                try:
                    if arg.index('holiday_status_id') == 0:
                        value = arg[2]
                        operator = arg[1]
                        del args[args.index(arg)]
                except ValueError:
                    pass
            if value:
                domain = []
                if operator in ('ilike', 'like'):
                    domain.append(('holiday_status_id.name', operator, value))
                else:
                    domain.append(('holiday_status_id', operator, value))
                line_ids = hol_line_obj.search(cr, uid, domain)
                holiday_ids = [x.holiday_id.id
                               for x in hol_line_obj.browse(cr, uid, line_ids,
                                                            context=context)]
                args.append(['id', 'in', holiday_ids])

        return super(HrHolidays, self).search(
            cr, uid, args, offset=offset, limit=limit, order=order, count=count
        )

    @api.model
    def compute_allo_days(self, employee_id, hol_status_ids,
                          date_from=False, date_to=False):
        """
        Calculate the allocation request which was approved
        """
        if not hol_status_ids:
            return 0
        sql = """
        SELECT
            CASE
                WHEN SUM(h.number_of_days) > 0 THEN SUM(h.number_of_days)
                ELSE 0
            END as allo_days
            FROM
                hr_holidays h
                join hr_holidays_status s on (s.id=h.holiday_status_id)
            WHERE
                h.type='add' AND
                h.state='validate' AND
                s.limit=False AND
                h.employee_id = %s AND
                h.holiday_status_id in (%s)
        """ % (employee_id, ','.join(map(str, hol_status_ids)),)
        if date_from and date_to:
            sql += """ AND h.allo_date >= '%s'
                       AND h.time_of_allocation_date <= '%s'
                       """ % (date_from, date_to)
        elif not date_from and date_to:
            sql += " AND h.allo_date <= '%s'" % (date_to)
        elif date_from and not date_to:
            sql += " AND h.allo_date >= '%s'" % (date_from)
        self._cr.execute(sql)
        res = self._cr.fetchone()
        return res and res[0] or 0

    @api.model
    def compute_leave_days(self, employee_id, hol_status_ids,
                           date_from=False, date_to=False):
        """
        Calculate the number of leave days in the indicated period of time
        """

        if not hol_status_ids:
            return 0
        condition = """
            FROM
                hr_holidays h
                join hr_holidays_line hl on (h.id=hl.holiday_id)
            WHERE
                h.type='remove' AND
                h.state='validate' AND
                h.employee_id = %s AND
                hl.holiday_status_id in (%s)
            """ % (employee_id, ','.join(map(str, hol_status_ids)))

        sql = "SELECT sum(hl.number_of_days)" + condition
        other_sql = """SELECT hl.first_date, hl.last_date, hl.first_date_type,
                        hl.last_date_type""" + condition
        cr = self._cr
        line_obj = self.env['hr.holidays.line']
        contract_obj = self.env['hr.contract']

        if date_from and date_to:
            # first date > date from and last date < date to
            sql += """AND hl.last_date < '%s'
                      AND hl.first_date > '%s'""" % (date_to, date_from)
            cr.execute(sql)
            res = cr.fetchone()
            # first date <= date from and last date >= date from
            # OR first date <= date to and last date >= date to
            other_sql += """AND (( hl.first_date <= '%s' AND hl.last_date >= '%s')
                            OR (hl.first_date <= '%s' AND hl.last_date >= '%s')
                            )""" % (date_from, date_from, date_to, date_to)
            cr.execute(other_sql)
            other_res = cr.fetchall()

        elif not date_from and date_to:
            # NOT date from and last date < date to
            sql += "AND hl.last_date < '%s'" % (date_to)
            cr.execute(sql)
            res = cr.fetchone()

            # OR first date <= date to and last date >= date to
            other_sql += """AND (hl.first_date <= '%s'
                            AND hl.last_date >= '%s')""" % (date_to, date_to)
            cr.execute(other_sql)
            other_res = cr.fetchall()

        elif date_from and not date_to:
            # first date > date from and NOT date to
            sql += "AND hl.first_date > '%s'" % (date_from)
            cr.execute(sql)
            res = cr.fetchone()

            # first date <= date from and last date >= date from
            other_sql += """AND ( hl.first_date <= '%s'
                            AND hl.last_date >= '%s')
                            """ % (date_from, date_from)
            cr.execute(other_sql)
            other_res = cr.fetchall()
        else:
            cr.execute(sql)
            res = cr.fetchone()
            return res and res[0] or 0

        """Calculate number of days"""
        number_of_days = res and res[0] or 0
        employee = self.env['hr.employee'].browse(employee_id)

        company = employee.company_id
        country_id = False
        if company and company.country_id:
            country_id = company.country_id.id
        for line in other_res:
            str_start_date = date_from and max(line[0], date_from) or line[0]
            start_date = datetime.strptime(str_start_date, DF).date()
            str_date_end = date_to and min(line[1], date_to) or line[1]
            end_date = datetime.strptime(str_date_end, DF).date()
            # Get the valid contract in (start_date, end_date)
            # Get the latest valid contract
            # Get the working schedule of this contract
            working_hours = False
            contract_obj = self.env['hr.contract']
            contract_ids = contract_obj.get_contract(
                employee.id, start_date, end_date)
            if contract_ids:
                contract = contract_obj.browse(contract_ids[-1])
                if contract.working_hours:
                    working_hours = contract.working_hours.id

            while start_date <= end_date:
                date_type = 'full'
                if start_date == datetime.strptime(line[0], '%Y-%m-%d').date():
                    date_type = line[2]
                if start_date == datetime.strptime(line[1], '%Y-%m-%d').date():
                    date_type = line[3]
                number_of_days += line_obj.plus_day(working_hours,
                                                    start_date,
                                                    date_type, country_id)
                start_date = start_date + timedelta(1)
        return number_of_days

HrHolidays()


class hr_holidays(osv.osv):
    _inherit = "hr.holidays"

# TODO:
# Waiting for this issue below is fixed
# https://github.com/odoo/odoo/issues/2088
    _columns = {
        # Add state cancel_request
        'state': fields_v7.selection([
            ('cancel_request', 'To Cancel'),
            ('draft', 'To Submit'), ('cancel', 'Cancelled'),
            ('confirm', 'To Approve'), ('refuse', 'Refused'),
            ('validate1', 'Second Approval'), ('validate', 'Approved')],
            'Status', readonly=True, track_visibility='onchange', copy=False,
            help='The status is set to \'To Submit\', \
            when a holiday request is created.\
            \nThe status is \'To Cancel\'\
            when holiday is request a cancellation by user.\
            \nThe status is \'To Approve\', \
            when holiday request is confirmed by user.\
            \nThe status is \'Refused\', \
            when holiday request is refused by manager.\
            \nThe status is \'Approved\', \
            when holiday request is approved by manager.'
        ),
        # add holiday_type employees
        'holiday_type': fields_v7.selection([
            ('employee', 'By Employee'),
            ('employees', 'By Employees'),
            ('category', 'By Employee Category')],
            string="Type",
            help='By Employee: Allocation/Request for individual Employee,\
            By Employee Category: Allocation/Request for \
            group of employees in category,\
            By Employees: Allocation/Request for selected employees',
            states={'draft': [('readonly', False)],
                    'confirm': [('readonly', False)]}
        )
    }

    @api.multi
    def holidays_cancellation_request(self):
        """
        Employee request to manager that he want to cancel his approved
        leave request.
        """
        for holiday in self:
            if holiday.date_from < datetime.today().strftime('%Y-%m-%d'):
                raise Warning(
                    _("The request date must be before the first leave date!"))
            holiday.signal_workflow('request_cancellation')
        self.write({'state': 'cancel_request'})
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
