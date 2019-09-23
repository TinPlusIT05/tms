# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import Warning


class AssetAssignHistory(models.Model):
    _name = 'asset.assign.history'
    _description = 'Assigning history of Assets'
    _inherit = ['mail.thread']

    asset_id = fields.Many2one(
        'tms.asset', string="Asset", required=True
    )
    assignee_id = fields.Many2one(
        'hr.employee', string="Owner"
    )
    start_date = fields.Date(
        "Start Date"
    )
    end_date = fields.Date(
        "End Date"
    )

    @api.constrains('start_date', 'end_date')
    def _check_date(self):
        """
        Check constraints of time for Asset Owner:
        - Start date must before end date
        - An asset can not be owned at the same time (period of them can not
        be overlapped)
        """
        for rec in self:
            if rec.start_date and rec.end_date and \
                    rec.start_date > rec.end_date:
                raise Warning("Start date must before end date!")
            item_ids = self.search(
                [('start_date', '<', rec.end_date),
                 ('end_date', '>', rec.start_date),
                 ('asset_id', '=', rec.asset_id.id),
                 ('id', '!=', rec.id)])
            if item_ids:
                raise Warning('An asset owner can not be overlapped!')
