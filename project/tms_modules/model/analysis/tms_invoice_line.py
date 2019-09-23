from openerp import fields, models


class TmsInvoiceLine(models.Model):

    _name = 'tms.invoice.line'
    _description = 'TMS Invoice Line'

    name = fields.Char('Customer Invoice Number')
    invoice_due_date = fields.Date('Date')
    activity_id = fields.Many2one('tms.activity', 'Activity')
    product = fields.Char('Product')
    description = fields.Text('Description')
    sold_qty = fields.Float('Sold Quantity', (2, 2))
    budget_man_days = fields.Float('Budget Man-days', (2, 2))
    status = fields.Char('Status')
