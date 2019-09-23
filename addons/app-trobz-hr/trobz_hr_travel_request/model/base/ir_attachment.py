# -*- coding: utf-8 -*-

from openerp import models, fields, api


class ir_attachment(models.Model):
    _inherit = 'ir.attachment'

    # Dummy field to search attachments of a travel request.
    # No need to store this field because we already have two fields
    # res_model and res_id.
    travel_request_id = fields.Many2one(
        comodel_name='hr.travel.request', string='Travel Request',
        compute=lambda *a: False, store=False
    )

    @api.model
    def create(self, vals):
        """
        When a document of a travel request is attached,
        increase a counting field of documents of that travel request.
        """
        attachment = super(ir_attachment, self).create(vals)
        if vals.get('res_model', '') == 'hr.travel.request'\
                and vals.get('res_id', False):
            model_obj = self.env['hr.travel.request']
            model = model_obj.browse(vals['res_id'])
            model.attachments_count = model.attachments_count + 1
        return attachment

    @api.multi
    def unlink(self):
        """
        When a document of a travel request is removed,
        decrease a counting field of documents of that travel request.
        """
        request_ids = []
        for attachment in self:
            if attachment.res_model == 'hr.travel.request'\
                    and attachment.res_id:
                request_ids.append(attachment.res_id)
        res = super(ir_attachment, self).unlink()
        if not request_ids:
            return res
        request_obj = self.env['hr.travel.request']
        for request in request_obj.browse(request_ids):
            request.attachments_count = request.attachments_count - 1
        return res

    @api.model
    @api.returns('self')
    def search(self, args, offset=0, limit=None, order=None,
               count=False):
        """
        Search documents by travel request.
        """
        new_args = []
        for domain in args:
            if isinstance(domain, (list, tuple))\
                    and domain[0] == 'travel_request_id':
                request_obj = self.env['hr.travel.request']
                requests = request_obj.search([('name', 'ilike', domain[2])])
                if not requests:
                    continue
                new_args += [('res_model', '=', 'hr.travel.request'),
                             ('res_id', 'in', requests.ids)]
            else:
                new_args.append(domain)
        return super(ir_attachment, self).search(
            new_args, offset=offset, limit=limit, order=order, count=count
        )

ir_attachment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
