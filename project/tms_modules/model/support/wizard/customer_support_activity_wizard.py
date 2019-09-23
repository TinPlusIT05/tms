# -*- coding: utf-8 -*-
from openerp import models, fields, api


class customer_support_activity_wizard(models.TransientModel):
    _name = "customer.support.activity.wizard"

    @api.multi
    @api.onchange('customer_id')
    def get_default_prev_date(self):
        for rcs in self:
            if not rcs.customer_id:
                continue
            sql = """
            SELECT date FROM tms_support_ticket
            Where date is not null and customer_id=%s
            ORDER BY date desc
            limit 1
            """
            self._cr.execute(sql, (rcs.customer_id.id,))
            date_res = self._cr.fetchone()
            date_res = date_res and date_res[0] or False
            rcs.previous_status_date = date_res

    customer_id = fields.Many2one(
        'res.partner', string="Customer", domain=[('customer', '=', True)])
    lang = fields.Selection(related='customer_id.lang', string="Language",
                            help="Set by default with the Language of the " +
                            "customer in the partner form.")
    description = fields.Text(
        string="Description", help="Example: Evolutions March April 2015")
    previous_status_date = fields.Date(
        string="Previous Status Date",
        help="If Previous Status Date is not set in wizard," +
        " use last Invoicing date of the support ticket of this customer.")

    @api.multi
    def button_export_support_activity_by_pdf(self):
        datas = {
            'form': self.read()[0]
        }
        assert len(self) == 1,\
            'This option should only be used for a single id at a time.'
        self.sent = True
        rpname = 'tms_modules.report_customer_support_activity_template'
        report_action = self.env['report'].get_action(self, rpname, data=datas)
        return report_action

    @api.multi
    def button_export_support_activity_by_html(self):
        datas = {
            'form': self.read()[0]
        }
        assert len(self) == 1,\
            'This option should only be used for a single id at a time.'
        self.sent = True
        rpname = 'tms_modules.report_customer_support_activity_template_html'
        report_action = self.env['report'].get_action(self, rpname, data=datas)
        return report_action
