# -*- coding: utf-8 -*-
from openerp import fields, models, api


class fetchmail_server(models.Model):

    _inherit = 'fetchmail.server'

    only_message = fields.Boolean(
        'Remove Previous Content',
        help='Remove previous content and signature from reply',
        required=False
    )

    @api.multi
    def fetch_mail(self):
        """
        Override function
        Add only_message to context
        """
        context = self._context and self._context.copy() or {}
        for server in self:
            if server.only_message:
                if context:
                    context.update({'only_message': server.only_message})
                else:
                    context = {'only_message': server.only_message}
        return super(fetchmail_server, self.with_context(context)).fetch_mail()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
