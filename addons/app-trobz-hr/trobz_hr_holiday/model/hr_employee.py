# -*- encoding: utf-8 -*-
from openerp.osv import osv, fields
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp import models, api, fields as fields_v8


class hr_employee(osv.osv):
    _inherit = "hr.employee"

    def _set_remaining_days(self, cr, uid, empl_id,
                            name, value, arg, context=None):
        """
        Override Function:
        When inputing remaining leaves < the current remaining leaves
        Create Leave Request have a leave request line.
            Because the days off will be calculated base on the holiday lines
        """
        if context is None:
            context = {}
        employee = self.browse(cr, uid, empl_id, context=context)
        diff = value - employee.remaining_leaves
        type_obj = self.pool.get('hr.holidays.status')
        holiday_obj = self.pool.get('hr.holidays')
        # Find for holidays status
        status_ids = type_obj.search(
            cr, uid, [('limit', '=', False)], context=context)
        if not status_ids:
            return False
        if len(status_ids) != 1:
            warn = """The feature behind the field
                     'Remaining Legal Leaves' can only be used
                     when there is only one leave type with the option
                     'Allow to Override Limit' unchecked.
                     (%s Found). Otherwise, the update is ambiguous as
                     we cannot decide on which leave type the update has
                     to be done. \nYou may prefer to use the classic
                     menus 'Leave Requests' and 'Allocation Requests'
                     located in 'Human Resources \ Leaves'
                     to manage the leave days of the employees
                     if the configuration does not allow to use
                     this field.""" % (len(status_ids))
            raise osv.except_osv(_('Warning!'), _(warn))
        if diff > 0:
            val = {
                'name': _('Allocation for %s') % employee.name,
                'employee_id': empl_id,
                'holiday_status_id': status_ids[0],
                'type': 'add',
                'holiday_type': 'employee',
                'number_of_days_temp': diff,
                'holiday_line': [(0, 0, {
                    'holiday_status_id': status_ids[0],
                    'number_of_days': abs(diff),
                    'first_date': '',
                    'last_date': '',
                    'first_date_type': False,
                    'last_date_type': False})]
            }
            leave_id = holiday_obj.create(cr, uid, val, context=context)
        elif diff < 0:
            raise osv.except_osv(
                _('Warning!'),
                _('You cannot reduce validated allocation requests'))
        else:
            return False
        for sig in ('confirm', 'validate', 'second_validate'):
            holiday_obj.signal_workflow(cr, uid, [leave_id], sig)
        return True

    def _get_remaining_days(self, cr, uid, ids, name, args, context=None):
        if context is None:
            context = {}
        res = {}
        status_pool = self.pool.get('hr.holidays.status')
        holiday_pool = self.pool.get('hr.holidays')
        status_ids = status_pool.search(
            cr, uid, [('limit', '=', False)], context=context)
        for emp_id in ids:
            allo_days = holiday_pool.compute_allo_days(
                cr, uid, emp_id, status_ids, context=context)
            leave_days = holiday_pool.compute_leave_days(
                cr, uid, emp_id, status_ids, context=context)
            res[emp_id] = allo_days - leave_days
        return res

    _columns = {
        'remaining_leaves': fields.function(
            _get_remaining_days, string='Remaining Legal Leaves',
            fnct_inv=_set_remaining_days, type="float",
            help="Total number of legal leaves allocated to this employee,"
            " change this value to create allocation/leave request."
            " Total based on all the leave type without overriding limit."
        ),
    }


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def calculate_work_seniority_month(self):
        """
        Calculate the number of months from hire_date to given date in context
        context {'to_date': datetime object}
        If not to_date, use current_date
        """
        context = dict(self._context) or {}
        to_date = context.get('to_date', datetime.now())
        for employee in self:
            hire_date = employee.hire_date
            if hire_date:
                hire_date = datetime.strptime(hire_date, DF)
                gap = relativedelta(to_date, hire_date)
                gap_year = gap.years
                gap_month = gap.months
                employee.work_seniority_month = gap_year * 12 + gap_month
            else:
                employee.work_seniority_month = 0

    work_seniority_month = fields_v8.Float(
        compute=calculate_work_seniority_month,
        string='Work Seniority Month ',
        help="The working months from hired date to the current date")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
