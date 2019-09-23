# -*- encoding: utf-8 -*-
from openerp import models, fields, api, _
from datetime import date, datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import Warning


class hr_public_holiday(models.Model):
    _name = "hr.public.holiday"
    _order = 'date DESC'

    @api.one
    def _get_day_of_week(self):
        """Returns day of week of this holiday."""
        self.weekday = datetime.strptime(self.date, DF).strftime('%A')

    @api.one
    @api.depends('date')
    def _get_year(self):
        """Returns day of week of this holiday."""
        self.year = datetime.strptime(self.date, DF).strftime('%Y')

    name = fields.Char(required=1, translate=1)
    date = fields.Date(required=1, default=fields.Date.today())
    country_id = fields.Many2one('res.country', 'Country', required=1)
    is_template = fields.Boolean('Template Holiday')
    weekday = fields.Char(compute=_get_day_of_week,
                          string='Day of Week')
    year = fields.Char(compute=_get_year,
                       string='Year',
                       store=True)

    @api.constrains('date', 'country_id', 'is_template')
    def _check_unique(self):
        """
        Cannot have 2 public holiday/public holiday template
            on the the same date
        """
        domain = [
            ('date', '=', self.date),
            ('country_id', '=', self.country_id.id),
            ('is_template', '=', self.is_template),
            ('id', '!=', self.id)
        ]
        avail_hols = self.search(domain)
        if avail_hols:
            raise Warning(_('''Public holiday must be unique
                                in a year of a country!'''))

    @api.model
    def automatic_generate_hr_public_holiday(self, select_year=False):
        """
        This function will be called in scheduler
        Create the public holiday base on the public holiday template
        """
        templates = self.search([('is_template', '=', True)])
        year = date.today().year + 1
        if select_year:
            year = select_year
        for template in templates:
            tmp_day = datetime.strptime(template.date, DF)
            date_str = str(year) + '-' + str(tmp_day.month) + \
                '-' + str(tmp_day.day)
            domain = [
                ('name', '=', template.name),
                ('country_id', '=', template.country_id.id),
                ('date', '=', date_str),
                ('is_template', '=', False)
            ]
            avail_hols = self.search(domain)
            if not avail_hols:
                hol_date = date(year, tmp_day.month, tmp_day.day).strftime(DF)
                default = {
                    'date': hol_date,
                    'is_template': False
                }
                template.copy(default=default)
        return True

hr_public_holiday()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
