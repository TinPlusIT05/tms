from openerp import api, fields, models
from openerp.exceptions import Warning


class TMSForgeTicketCard(models.Model):
    _name = 'tms.forge.ticket.card'
    _description = 'TMS Forge Ticket Card'

    name = fields.Char("Card's ID")
    forge_ticket_id = fields.Many2one(
        comodel_name='tms.forge.ticket', string='Forge Ticket',
        required=True)
    assignee_id = fields.Many2one(
        comodel_name='res.users', string="Card's owner",
        required=True)
    pct_complete = fields.Float('% Complete')
    working_date = fields.Date(
        'Sprint',
        default=lambda self: self.env[
            'daily.mail.notification'].get_current_sprint())

    @api.model
    def create(self, vals):
        card = super(TMSForgeTicketCard, self).create(vals)
        card.name = 'C#%s' % card.id
        return card

    @api.constrains('pct_complete')
    def _check_pct_complete(self):
        for record in self:
            cards = self.search([
                ('forge_ticket_id', '=', record.forge_ticket_id.id)])
            total_pct_complete = sum(cards.mapped('pct_complete'))
            if total_pct_complete > 100:
                raise Warning(
                    'Total %s Complete of ticket F#%s must be less or equal '
                    'to 100' % ('%', record.forge_ticket_id.id)
                )

    @api.constrains('assignee_id', 'working_date')
    def _check_assignee_id(self):
        for record in self:
            cards = self.search([
                ('forge_ticket_id', '=', record.forge_ticket_id.id),
                ('assignee_id', '=', record.assignee_id.id),
                ('working_date', '=', record.working_date),
                ('id', '!=', record.id)])
            if cards:
                raise Warning(
                    'Card for %s is already exists in Sprint %s' %(
                        record.assignee_id.name, record.working_date)
                )
