from openerp import fields, models


class hr_holidays_summary_line(models.TransientModel):

    _name = 'hr.holidays.summary.line'

    year = fields.Char('Year', size=4, required=True)
    holidays_summary_id = fields.Many2one(
        'hr.holidays.summary', 'Holidays Summary')
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    allocation_day = fields.Float('Allocation days')
    casual_leave_paid_day = fields.Float('Casual leave (paid)')
    sick_leave_paid_day = fields.Float('Sick leaves (paid)')
    upaid_leave_day = fields.Float(' Unpaid leave')
    other_paid_leave_day = fields.Float('Other')
    remaining_total = fields.Float('Remaining Total')
