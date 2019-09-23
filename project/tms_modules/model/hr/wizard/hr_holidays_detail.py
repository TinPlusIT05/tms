# -*- coding: utf-8 -*-
from datetime import datetime, date
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp import fields, api, models
# from openerp.osv import fields, osv


class hr_holidays_detail(models.TransientModel):
    _name = 'hr.holidays.detail'
    _description = 'Detail Leaves Request For Employees In Year'

    year = fields.Char('Year', size=4, required=True,
                       default=str(datetime.now().year))

    @api.multi
    def execute_detail_employee(self):
        holidays_summary_env = self.env['hr.holidays.summary']
        holidays_summary_line_env = self.env['hr.holidays.summary.line']
        employee_env = self.env['hr.employee']
        hol_status_env = self.env['hr.holidays.status']
        config_pool = self.env['ir.config_parameter']
        hol_env = self.env['hr.holidays']

        view_id = False
        if self.ids:
            # Get wizard record details
            data_obj = self[0]

            # Get the current year entered through wizard
            myear = data_obj.year or False
            date_from = date(
                int(myear),
                1,
                1).strftime(DEFAULT_SERVER_DATE_FORMAT)
            date_to = date(
                int(myear),
                12,
                31).strftime(DEFAULT_SERVER_DATE_FORMAT)

            # Delete all old records
            holidays_summary_objs = holidays_summary_env.search(
                [('year', '=', myear)])
            if holidays_summary_objs:
                holidays_summary_objs.unlink()

            # Create new one
            holidays_summary_obj = holidays_summary_env.create({'year': myear})
            if holidays_summary_obj:
                view_id = holidays_summary_obj.id

                # Get all employee IDS
                employee_objs = employee_env.search([])
                if employee_objs:
                    for employee_obj in employee_objs:
                        # Calculate Casual allocation and leave request
                        casual_leave = config_pool.get_param(
                            "default_leave_type_to_add_allocation_each_month",
                            False)
                        hol_status_objs = hol_status_env.search(
                            [('name', '=', casual_leave)])

                        # 1.Total allocation days (Count all)
                        allocation_day = hol_env.compute_allo_days(
                            employee_obj.id,
                            hol_status_objs.ids)

                        # 2.Total casual leave (paid) days (Count all)
                        casual_leave_day = 0.0
                        if hol_status_objs:
                            casual_leave_day = hol_env.compute_leave_days(
                                employee_obj.id,
                                hol_status_objs.ids)

                        # 3.Total sick leave (paid) days + Total Sick leave
                        # EXPAT (paid) days (in specific year)
                        sick_leave_day = 0.0
                        sick_leave = config_pool.get_param(
                            "default_sick_leave_paid",
                            False)
                        sick_expat_leave = config_pool.get_param(
                            "default_sick_leave_expat_paid",
                            False)
                        hol_status_objs = hol_status_env.search(
                            [('name', 'in', (sick_leave, sick_expat_leave))])
                        if hol_status_objs:
                            sick_leave_day = hol_env.compute_leave_days(
                                employee_obj.id,
                                hol_status_objs.ids,
                                date_from=date_from,
                                date_to=date_to)
                        # 4.Total unpaid leave days (in specific year)
                        unpaid_leave_day = 0.0
                        hol_status_objs = hol_status_env.search(
                            [('payment_type', '=', 'unpaid')])
                        if hol_status_objs:
                            unpaid_leave_day = hol_env.compute_leave_days(
                                employee_obj.id,
                                hol_status_objs.ids,
                                date_from=date_from,
                                date_to=date_to)

                        # 5.Total remaining paid leave day (in specific year)
                        remain_paid_leave_day = 0.0
                        hol_status_objs = hol_status_env.search(
                            [('payment_type', '=', 'paid'),
                             ('name', 'not in',
                              [casual_leave, sick_leave, sick_expat_leave])])
                        if hol_status_objs:
                            remain_paid_leave_day = hol_env.compute_leave_days(
                                employee_obj.id,
                                hol_status_objs.ids,
                                date_from=date_from,
                                date_to=date_to)

                        # 6.Allocation balance for each employee
                        balance_casual_day = allocation_day - casual_leave_day
                        vals = {
                            'year': myear,
                            'holidays_summary_id': holidays_summary_obj.id,
                            'employee_id': employee_obj.id,
                            'allocation_day': allocation_day,
                            'casual_leave_paid_day': casual_leave_day,
                            'sick_leave_paid_day': sick_leave_day,
                            'upaid_leave_day': unpaid_leave_day,
                            'other_paid_leave_day': remain_paid_leave_day,
                            'remaining_total': balance_casual_day
                        }
                        holidays_summary_line_env.create(vals)

        return {
            'name': 'Detail Leaves Request For Employees',
            'view_type': 'tree,form',
            'view_mode': 'form',
            'res_model': 'hr.holidays.summary',
            'type': 'ir.actions.act_window',
            'res_id': view_id,
            'views': [(False, 'form')],
            'target': 'current',
        }


hr_holidays_detail()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
