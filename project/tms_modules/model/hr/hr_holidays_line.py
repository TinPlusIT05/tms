# -*- encoding: UTF-8 -*-

from datetime import datetime, timedelta
from openerp import models, api, _


class hr_holidays_line(models.Model):
    _inherit = "hr.holidays.line"

    @api.multi
    def is_exist_leave(self, date, half_day_type='full'):
        """
        Return True if employee has leave on date with type as half_day_type
        """
        self.ensure_one()
        employee = self.holiday_id and self.holiday_id.employee_id or None
        if not employee:
            return True
        # Find all leve line overlap @date
        domain = [
            ('id', '!=', self.id),
            ('state', 'not in', ['cancel', 'refuse']),
            ('holiday_id.employee_id', '=', employee.id),
            ('holiday_id.type', '=', 'remove'),
            ('first_date', '<=', date),
            ('last_date', '>=', date),
        ]
        exist_leaves = self.search(domain)
        for leave in exist_leaves:
            # Chack case @date is last_date
            if str(date) == leave.last_date:
                if half_day_type == 'full':
                    return True
                elif half_day_type == leave.last_date_type:
                    return True
                else:
                    False
            # Check case @date is first_date
            elif str(date) == leave.first_date:
                if half_day_type == 'full':
                    return
                if half_day_type == leave.first_date_type:
                    return True
                else:
                    False
            else:
                return True
        return False

    @api.constrains('first_date', 'last_date',
                    'first_date_type', 'last_date_type')
    def _check_date(self):
        """
        Check leave lines overlaps on same period of time
        """
        for line in self:
            holiday = line.holiday_id or None
            if not holiday:
                continue
            if holiday.type == 'add':
                continue
            start = datetime.strptime(line.first_date, '%Y-%m-%d').date()
            end = datetime.strptime(line.last_date, '%Y-%m-%d').date()
            # Does not allow first_date and last_date in different year
            if start.year != end.year:
                raise Warning(
                    _("First Day and Last Day must in the same year!"))
            employee = line.holiday_id.employee_id
            if not employee:
                return True
            day_count = (end - start).days + 1
            for date in (start + timedelta(n) for n in range(day_count)):
                date_type = 'full'
                if date == start:
                    date_type = line.first_date_type
                elif date == end:
                    date_type = line.last_date_type
                if line.is_exist_leave(date, date_type):
                    raise Warning(
                        _("You can not have 2 leaves \
                        that overlaps on same period of time!"))
        return True

    @api.multi
    def write(self, vals):
        res = super(hr_holidays_line, self).write(vals)
        # when state's hr_holidays_lines in ('refuse', 'cancel')
        # remove the hr_resource_allocation if any
        if vals.get('state', '') in ('refuse', 'cancel'):
            self.remove_hr_resource_allocation()
        return res

    @api.multi
    def remove_hr_resource_allocation(self):
        hr_resource_env = self.env['hr.resource.allocation']
        for record in self:
            cancel_hr_resource = hr_resource_env.search([('holiday_id',
                                                          'ilike', record.id)])
            cancel_hr_resource.unlink()
        return True
