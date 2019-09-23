# -*- encoding: utf-8 -*-
from datetime import datetime, date, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp import fields, models, api, _
from openerp.exceptions import Warning
from openerp.addons.booking_chart.mixin import mixin  # @UnresolvedImport


HOLIDAY_STATES = (
    ('cancel_request', 'Leave Cancellation Request'),
    ('draft', 'To Submit'),
    ('cancel', 'Cancelled'),
    ('confirm', 'To Approve'),
    ('refuse', 'Refused'),
    ('validate1', 'Second Approval'),
    ('validate', 'Approved')
)


class hr_holidays_line(models.Model):
    _name = 'hr.holidays.line'
    _description = 'Leave request lines'

    @api.constrains('first_date', 'last_date',
                    'first_date_type', 'last_date_type')
    def _check_date(self):
        """
        Check leave lines overlaps on same period of time
        """
        for line in self:
            employee = line.holiday_id.employee_id
            if not employee:
                return True
            domain = [
                ('id', '!=', line.id),
                ('state', 'not in', ['cancel', 'refuse']),
                ('holiday_id.employee_id', '=', employee.id),
                ('holiday_id.type', '=', 'remove')]
            # Condition with the different dates
            overlap_on_first_date = [
                '&', ('first_date', '<', line.first_date),
                ('last_date', '>', line.first_date)]
            overlap_on_last_date = [
                '&', ('first_date', '<', line.last_date),
                ('last_date', '>', line.last_date)]
            overlap_on_first_last_date = [
                '&', ('first_date', '>', line.first_date),
                ('last_date', '<', line.last_date)]
            domain_differ_dates = domain + ['|', '|'] + \
                overlap_on_first_date + \
                overlap_on_last_date + \
                overlap_on_first_last_date
            overlap_lines = self.search(domain_differ_dates)
            if overlap_lines:
                raise Warning(
                    _("You can not have 2 leaves \
                    that overlaps on same period of time!"))
            # first date of existed lines = last date of the current line
            overlap_same_first_date = [('first_date', '=', line.last_date)]
            overlap_lines = self.search(domain + overlap_same_first_date)
            for overlap_line in overlap_lines:
                if not (line.last_date_type == 'morning'
                        and overlap_line.first_date_type == 'afternoon'):
                    raise Warning(
                        _("You can not have 2 leaves \
                        that overlaps on same period of time!"))
            # last date of existed lines = first date of the current line
            overlap_same_last_date = [('last_date', '=', line.first_date)]
            overlap_lines = self.search(domain + overlap_same_last_date)
            for overlap_line in overlap_lines:
                if not (line.first_date_type == 'afternoon'
                        and overlap_line.last_date_type == 'morning'):
                    raise Warning(
                        _("You can not have 2 leaves \
                        that overlaps on same period of time!"))
        return True

    @api.one
    @api.depends('first_date', 'holiday_id')
    def _get_period(self):
        """
        Get period time in format MM/YYYY to search holiday line by month/year
        """
        self.period = self.first_date \
            and datetime.strptime(self.first_date, DF).strftime('%m/%Y')

    @api.one
    @api.depends('number_of_days')
    def _compute_number_of_days_temp(self):
        """
        Calculate number_of_days of leave/allocation request
        to show on leave summary
        """
        if self.holiday_id.type == 'remove':
            self.number_of_days_temp = -self.number_of_days
        else:
            self.number_of_days_temp = self.number_of_days

    _DATE_TYPE = [('morning', 'Morning'),
                  ('afternoon', 'Afternoon'),
                  ('full', 'Full Day')]
    holiday_status_id = fields.Many2one("hr.holidays.status", "Leave Type",
                                        required=True)
    holiday_id = fields.Many2one('hr.holidays', 'Holiday', ondelete='cascade')
    first_date = fields.Date('First Day')
    last_date = fields.Date('Last Day')
    first_date_type = fields.Selection(_DATE_TYPE, string='First Day Type',
                                       default='full')
    last_date_type = fields.Selection(_DATE_TYPE, string='Last Day Type',
                                      default='full')
    number_of_days = fields.Float('Number of Days', digits=(16, 2),
                                  readonly=1)
    number_of_days_temp = fields.Float(
        compute=_compute_number_of_days_temp,
        string='Number of Days', store=True
    )
    payment_type = fields.Selection(related='holiday_status_id.payment_type',
                                    string="Payment Type")
    employee_id = fields.Many2one('hr.employee', 'Employee')
    state = fields.Selection(HOLIDAY_STATES, string='Status', default='draft')
    period = fields.Char(compute=_get_period, size=64,
                         store=True, string='Period')

    @api.model
    def plus_day(self, working_hours, date, date_type, country_id):
        """
        Calculate day: number_of days on holiday line += day
        1. The date is the public holiday, return 0
        2. Base on the working schedule set on the employee contract
            (1 working schedule line = 0.5 day)
        3. Base on the day of week if not the working schedule
        """
        public_obj = self.env['hr.public.holiday']
        pub_hol = public_obj.search([('country_id', '=', country_id),
                                     ('date', '=', date.strftime(DF)),
                                     ('is_template', '=', False)])
        if pub_hol:
            return 0

        day = 0
        if working_hours:
            self._cr.execute("""SELECT COUNT(dayofweek)
                          FROM resource_calendar_attendance
                          WHERE calendar_id = %s
                          AND (date_from <= '%s' OR date_from IS NULL)
                          AND dayofweek = '%s'
                        """ % (working_hours, date, date.weekday()))
            res = self._cr.fetchone()
            day = date_type == 'full' and 1 or 0.5
            day = res and min(res[0] * 0.5, day) or 0
        else:
            if date.weekday() not in (5, 6):
                day = date_type == 'full' and 1 or 0.5
        return day

    @api.model
    def _calculate_days(self, employee=False, first_date=False,
                        last_date=False, first_date_type=False,
                        last_date_type=False):
        """ Calculate number_of_days on leave request lines
            - If the employee has a contract and working calendar:
                the number_of_days must be calculated based on working calendar
            - If not, number_of_days will be calculated base on the day of week
        """
        number_of_days = 0
        employee = employee or self.holiday_id.employee_id
        first_date = first_date or self.first_date
        last_date = last_date or self.last_date
        first_date_type = first_date_type or self.first_date_type
        last_date_type = last_date_type or self.last_date_type

        if first_date and last_date and first_date_type \
           and last_date_type and employee:

            if first_date > last_date:
                raise Warning(_("""The First Date must be
                                before the Last Date !"""))
            country_id = False
            if self._context.get('country_id', False):
                country_id = self._context['country_id']
            else:
                if employee.company_id and employee.company_id.country_id:
                    country_id = employee.company_id.country_id.id

            working_hours = False
            contract = employee.contract_id
            if contract:
                if contract.working_hours:
                    if contract.working_hours.attendance_ids:
                        working_hours = contract.working_hours.id

            first_date = datetime.strptime(first_date, DF).date()
            last_date = datetime.strptime(last_date, DF).date()
            date_type = first_date_type
            next_date = date(first_date.year, first_date.month, first_date.day)
            while next_date <= last_date:
                number_of_days += self.plus_day(working_hours, next_date,
                                                date_type, country_id)
                next_date = (next_date + timedelta(days=1))
                date_type = 'full'
                if next_date == last_date:
                    date_type = last_date_type
        return number_of_days

    @api.onchange('first_date', 'last_date', 'first_date_type',
                  'last_date_type', 'employee_id')
    def _onchange_holiday_line(self):
        """ - When selecting first date, last date, date types,
                calculate the number of days
            - If first_date equal to last_date,
                return the last_date_type is first_date_type
        """
        self.number_of_days = self._calculate_days()
        # Only run when input data on leave request form.
        # No need to run in create/write hr.holiday.line
        if ('no_update_last_date_type' not in self._context and
                self.first_date == self.last_date):
            self.last_date_type = self.first_date_type

    # F#14484
    @api.multi
    def create_booking_resource(self):
        booking_resource_pool = self.env['booking.resource']
        # Take chart_id in booking resource
        'trobz_hr_holiday.hr_holidays_line_booking_chart'
        ir_model_env = self.env['ir.model.data']
        ir_model_obj = ir_model_env.get_object_reference(
            'trobz_hr_holiday', 'hr_holidays_line_booking_chart')
        for line in self:
            leave_type = line.holiday_status_id.name
            days_temp = line.number_of_days_temp
            _get_name = '%s - %s day(s)' % (leave_type, abs(days_temp))

            vals = {
                'name': _get_name,
                'resource_ref': 'hr.employee,%s' % line.employee_id.id,
                'origin_ref': 'hr.holidays.line,%s' % line.id,
                'target_ref': 'hr.holidays,%s' % line.holiday_id.id,
                'message': line.holiday_id and line.holiday_id.name or '',
                'date_start': line.first_date,
                'date_end': line.last_date,
                'chart_id': ir_model_obj[1],
            }
            booking_resource_pool.create(vals)

    @api.model
    def create(self, vals):
        """
        Override function:
        - Update employee_id on leave request to leave request line
        - Update number_of_days because of its readonly attribute
        """
        res = False
        if vals.get('holiday_id', False):
            # Update employee_id for leave request to holiday lines
            hol_obj = self.env['hr.holidays']
            hol = hol_obj.browse(vals['holiday_id'])
            employee_id = hol and hol.employee_id and hol.employee_id.id
            vals.update({'employee_id': employee_id})
            res = super(hr_holidays_line, self).create(vals)
            if hol.type == 'remove':
                # If leave request
                # Update number_of_days because of its readonly
                # Update no_update_last_date_type in context to know
                # onchange_holiday_line is called in write function
                # No need to run onchange on last_date_type
                ctx = dict(self._context)
                ctx.update(no_update_last_date_type=1)
                res.with_context(ctx)._onchange_holiday_line()
        return res

    @api.multi
    def write(self, vals):
        """
        Override function:
        - Update number_of_days because of its readonly attribute
        """
        res = super(hr_holidays_line, self).write(vals)
        for line in self:
            if line.holiday_id.type == 'remove' \
               and (vals.get('last_date_type', False)
                    or vals.get('first_date_type', False)
                    or vals.get('last_date', False)
                    or vals.get('first_date', False)):
                # Update no_update_last_date_type in context to know
                # onchange_holiday_line is called in write function
                # No need to run onchange on last_date_type
                ctx = dict(self._context)
                ctx.update(no_update_last_date_type=1)
                line.with_context(ctx)._onchange_holiday_line()
            if vals.get('state', False) == 'validate' and \
                    line.holiday_id.type == 'remove':
                line.create_booking_resource()

        # when state's hr_holidays_lines in ('refuse', 'cancel')
        # remove the resource if any
        if vals.get('state', '') in ('refuse', 'cancel'):
            self.remove_booking_resource()
        return res

    @api.multi
    def _get_name(self):
        line = self[0]
        leave_type = line.holiday_status_id.name
        days_temp = line.number_of_days_temp
        return '%s - %s day(s)' % (leave_type, abs(days_temp))

    @api.multi
    def _get_hr_employee_id(self, resource_allocation):
        return 'hr.employee,%s' % resource_allocation.employee_id.id

    @api.multi
    def remove_booking_resource(self):
        booking_resource_env = self.env['booking.resource']
        for record in self:
            cancel_requests_rec = \
                booking_resource_env.search([('origin_ref',
                                              'ilike', record.id)])
            cancel_requests_rec.unlink()
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
