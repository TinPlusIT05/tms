# -*- encoding: UTF-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class HrHolidaysStatus(models.Model):

    _inherit = "hr.holidays.status"

    # Columns
    activity_id = fields.Many2one('tms.activity',
                                  string='Activity')
    sequence = fields.Integer(string="Sequence", default=10)
    color = fields.Char(
        string="Color",
        help="Choose your color, with hexa code for 7 chacracters")

    @api.multi
    def get_days(self, employee_id, date_to=None):
        """
        Override function:
        If leave type is Sick Leave, get data in current year
        """
        result = super(HrHolidaysStatus, self).get_days(
            employee_id, date_to=date_to)
        sick_paid = self.env.ref(
            'trobz_hr_holiday_vn.hr_holiday_status_sick_paid')
        if not date_to:
            # If there is not date_to, we will count
            # all leaves of employee up to next 12 months from now
            date_to = date.today() + relativedelta(month=12)
        today = date.today()
        begin_year = today.replace(month=1, day=1).strftime(DF)
        cr = self._cr
        for record in self.filtered(lambda x: x == sick_paid):
            record_id = record.id
            status_dict = result[record_id]
            # Maximum Leaves Allowed
            cr.execute("""SELECT SUM(number_of_days)
                                FROM hr_holidays
                                WHERE employee_id = %s
                                AND state='validate'
                                AND holiday_status_id = %s
                                AND renew_casual_leave = False
                                AND type = 'add'
                                AND create_date >= %s
                                GROUP BY type""", (
                                    str(employee_id),
                                    str(record_id),
                                    begin_year))
            max_leaves = cr.fetchone()
            max_leaves = max_leaves and max_leaves[0] or 0

            # Leaves Already Taken
            cr.execute("""SELECT sum(t.number_of_days)
                                FROM hr_holidays as h
                                LEFT JOIN hr_holidays_line AS t
                                ON t.holiday_id=h.id where h.employee_id = %s
                                AND h.state='validate'
                                AND t.holiday_status_id = %s
                                AND renew_casual_leave = False
                                AND type = 'remove'
                                AND date_to <= %s
                                AND t.first_date >= %s
                                GROUP BY type""", (
                                    str(employee_id),
                                    str(record_id),
                                    str(date_to),
                                    begin_year))
            leaves_taken = cr.fetchone()
            leaves_taken = leaves_taken and leaves_taken[0] or 0
            remaining_leaves = max_leaves - leaves_taken

            # Leaves waiting approval
            cr.execute("""SELECT sum(t.number_of_days)
                                FROM hr_holidays as h
                                LEFT JOIN hr_holidays_line AS t
                                ON t.holiday_id=h.id where h.employee_id = %s
                                AND h.state in ('validate1', 'confirm')
                                AND renew_casual_leave = False
                                AND t.holiday_status_id = %s
                                AND type = 'remove'
                                AND date_to <= %s
                                AND t.first_date >= %s
                                GROUP BY type""", (
                                    str(employee_id),
                                    str(record_id),
                                    str(date_to),
                                    begin_year))
            leaves_wait = cr.fetchone()
            leaves_wait = leaves_wait and leaves_wait[0] or 0
            virtual_remaining_leaves = remaining_leaves - leaves_wait

            status_dict['max_leaves'] = max_leaves
            status_dict['leaves_taken'] = leaves_taken
            status_dict['remaining_leaves'] = remaining_leaves
            status_dict['virtual_remaining_leaves'] = virtual_remaining_leaves
        return result
