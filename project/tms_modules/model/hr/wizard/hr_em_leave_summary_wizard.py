from openerp import fields, models, api
from datetime import date, datetime


class HrEmLeaveSummaryWizard(models.TransientModel):
    _name = 'hr.em.leave.summary.wizard'

    year = fields.Selection(
        string='Year',
        selection=[(y, '%s' % y) for y in range(2010, 2051)],
        default=lambda self: date.today().year,
        required=True,
    )
    update_date = fields.Date(
        string='Update to',
        default=fields.Date.today(),
        required=True,
    )

    @api.constrains('year', 'update_date')
    def _check_year(self):
        convert_update_date = datetime.strptime(self.update_date, "%Y-%m-%d")
        if convert_update_date.year != self.year:
            raise Warning("The year of \"Update to\" must "
                          "be same with \"Year\"")

    @api.multi
    def button_print_em_leave_report(self):
        self.ensure_one()
        wizard_input_data = {
            "year": self.year,
            "update_to": self.update_date,
            "model": "hr.em.leave.summary.wizard",
        }
        return {
            "datas": wizard_input_data,
            "type": "ir.actions.report.xml",
            "report_name": "report.em.leave.summary.xlsx",
            "name": u"Emergency-Medical-Summary-{0}".format(self.year)
        }
