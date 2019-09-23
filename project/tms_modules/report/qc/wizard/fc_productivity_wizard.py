# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta
import calendar

from openerp import models, fields, api
from openerp.exceptions import Warning


class FcProductivityWizard(models.TransientModel):
    _name = "fc.productivity.wizard"

    from_date = fields.Date(string="From date")
    to_date = fields.Date(string="To date")

    @api.model
    def default_get(self, fields_list):
        defaults = super(FcProductivityWizard, self).default_get(
            fields_list)
        # Set default for date_from and date_to as begin and end of last month
        today = date.today()
        begin_date_of_last_month = (today - relativedelta(months=1)).replace(day=1)
        end_date_of_last_month = begin_date_of_last_month.replace(
            day=calendar.monthrange(
                begin_date_of_last_month.year,
                begin_date_of_last_month.month)[1])

        defaults.update({
            'from_date': str(begin_date_of_last_month),
            'to_date': str(end_date_of_last_month)
        })
        return defaults

    @api.multi
    def btn_export_fc_productivity(self):
        self.ensure_one()
        datas = {
            'from_date': self.from_date,
            'to_date': self.to_date
        }
        report = self.env.ref('tms_modules.fc_productivity_report_xlsx')
        report_action = self.env['report'].get_action(
            self, report.report_name, data=datas)
        return report_action
