from openerp import models, api, fields, _
WARNING_TYPES = [('warning', _('Warning')), ('information', _('Information'))]


class InformationPopup(models.TransientModel):
    _name = 'information.popup'
    _description = 'Information Popup'

    message_details = fields.Text(string="Message", readonly=True)
    type = fields.Selection(WARNING_TYPES, string='Type', readonly=True)
    title = fields.Char(string="Title", size=100, readonly=True)

    @api.multi
    def message(self):
        information_popup = \
            self.env.ref('information_popup.view_information_popup_form')
        for message in self:
            message_type = \
                [t[1]for t in WARNING_TYPES if message.type == t[0]][0]
            return {
                'name': '%s: %s' % (_(message_type), _(message.title)),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': information_popup and information_popup.id or False,
                'res_model': 'information.popup',
                'domain': [],
                'context': self._context,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': message.id
            }

    @api.model
    def warning(self, title='', message='', warn_type='warning'):
        message_record = self.create(
            {'title': title, 'message_details': message, 'type': warn_type})
        return message_record.message()
