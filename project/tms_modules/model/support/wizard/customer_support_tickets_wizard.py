# -*- coding: utf-8 -*-
from openerp import fields, api, models


class customer_support_tickets_wizard(models.TransientModel):
    _name = "customer.support.tickets.wizard"

    ASSIGNED_TO_MAP = [('customer', 'Customer'), ('trobz', 'Trobz')]

    opening_fromdate = fields.Date("Opening From Date")
    opening_todate = fields.Date("Opening To Date")
    quotation_approval_fromdate = fields.Date("Quotation Approval From Date")
    quotation_approval_todate = fields.Date("Quotation Approval From Date")
    invoicing_fromdate = fields.Date("Invoicing From Date")
    invoicing_todate = fields.Date("Invoicing To Date")
    staging_delivery_fromdate = fields.Date("Staging Delivery From Date")
    staging_delivery_todate = fields.Date("Staging Delivery To Date")
    ok_production_fromdate = fields.Date("OK Production From Date")
    ok_production_todate = fields.Date("OK Production To Date")
    closing_fromdate = fields.Date("Closing From Date")
    closing_todate = fields.Date("Closing To Date")
    assigned_to = fields.Selection(ASSIGNED_TO_MAP, "Assigned To")
    owner_id = fields.Many2one("res.users", "Assignee")
    ticket_type = fields.Selection(
        selection=[('opened', 'Opened'), ('closed', 'Closed'),
                   ('both', 'Both Opened and Closed')],
        string='Type of Ticket',
        default='opened')
    opened = fields.Boolean('Only Open Tickets', default=True)
    project_ids = fields.Many2many(
        "tms.project", "tms_support_ticket_project_export_rel",
        "wizard_id", "project_id", string="Project", required=True
    )
    is_offered = fields.Boolean('Offered')
    quotation_approved = fields.Boolean('Quotation Approved')

    @api.onchange('assigned_to')
    def onchange_assignee(self):
        self.owner_id = False

    @api.multi
    def button_export_support_ticket(self):
        # Get wizard input data to call the report
        wizard_input = self[0]

        # Update wizard input data to call the report
        wizard_input_data = {
            "ids": self.ids,
            "model": "customer.support.tickets.wizard",
            "opening_fromdate": wizard_input.opening_fromdate,
            "opening_todate": wizard_input.opening_todate,
            "quotation_approval_fromdate":
                wizard_input.quotation_approval_fromdate,
            "quotation_approval_todate":
                wizard_input.quotation_approval_todate,
            "invoicing_fromdate": wizard_input.invoicing_fromdate,
            "invoicing_todate": wizard_input.invoicing_todate,
            "staging_delivery_fromdate":
                wizard_input.staging_delivery_fromdate,
            "staging_delivery_todate": wizard_input.staging_delivery_todate,
            "ok_production_fromdate": wizard_input.ok_production_fromdate,
            "ok_production_todate": wizard_input.ok_production_todate,
            "closing_fromdate": wizard_input.closing_fromdate,
            "closing_todate": wizard_input.closing_todate,
            "assigned_to": wizard_input.assigned_to,
            "owner_id": wizard_input.owner_id and wizard_input.owner_id.id or
            False,
            "ticket_type": wizard_input.opening_todate,
            "project_ids": wizard_input.project_ids and
            wizard_input.project_ids.ids or [],
            "is_offered": wizard_input.is_offered,
            "quotation_approved": wizard_input.quotation_approved
        }
        if wizard_input.opened:
            wizard_input_data.update({'ticket_type': 'opened'})
        else:
            wizard_input_data.update({'ticket_type': 'both'})

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'customer_support_tickets',
            'datas': wizard_input_data}
