from openerp import fields, models


class hr_holidays_summary(models.TransientModel):

    _name = 'hr.holidays.summary'

    year = fields.Char('Year', size=4, required=True)
    holidays_summary_line_ids = fields.One2many(
        comodel_name='hr.holidays.summary.line',
        inverse_name='holidays_summary_id')
