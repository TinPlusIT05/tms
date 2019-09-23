# -*- encoding: utf-8 -*-
from openerp import models, fields, api
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


class hr_holidays_status(models.Model):
    _inherit = "hr.holidays.status"

    @api.multi
    def get_days(self, employee_id, date_to=None):
        """
        Override function:
        Calculate based on the number_of_days of leave lines
            instead of leave request
        """
        result = dict((status_id, dict(max_leaves=0,
                                       leaves_taken=0,
                                       remaining_leaves=0,
                                       virtual_remaining_leaves=0))
                      for status_id in self.ids)
        status_dict = {}
        if not employee_id:
            return status_dict
        if not date_to:
          # If there is not date_to, we will count 
          # all leaves of employee up to next 12 months from now
          date_to = date.today() + relativedelta(month=12)
        cr = self._cr
        # Calculate value of fields
        for record in self:
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
                              GROUP BY type""", (str(employee_id),
                                                 str(record_id)))
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
                              GROUP BY type""", (str(employee_id),
                                                 str(record_id),
                                                 str(date_to)))
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
                              GROUP BY type""", (str(employee_id),
                                                 str(record_id),
                                                 str(date_to)))
            leaves_wait = cr.fetchone()
            leaves_wait = leaves_wait and leaves_wait[0] or 0
            virtual_remaining_leaves = remaining_leaves - leaves_wait

            status_dict['max_leaves'] = max_leaves
            status_dict['leaves_taken'] = leaves_taken
            status_dict['remaining_leaves'] = remaining_leaves
            status_dict['virtual_remaining_leaves'] = virtual_remaining_leaves
        return result

    code = fields.Char(string='Code', size=16)
    payment_type = fields.Selection([('paid', 'Paid by Company'),
                                     ('unpaid', 'Unpaid'),
                                     ('paid_social', 'Paid by Social'),
                                     ('to_confirm', 'To be confirm')],
                                    string='Payment Type',
                                    default="paid")
    # TODO: there are have no any control based on max_days_allowed,
    # Could add a warning when user takes days off over this field value
    max_days_allowed = fields.Float(
        string='Maximum Days Allowed',
        help='Maximum Days Allowed for this type of Leave.')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
