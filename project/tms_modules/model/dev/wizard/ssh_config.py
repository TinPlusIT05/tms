# -*- encoding: UTF-8 -*-
# from openerp.osv import fields, osv
from openerp import fields, api, models
import base64


class ssh_config(models.TransientModel):

    _name = 'ssh.config'
    _description = 'Generate ssh config file'

    name = fields.Char(string="name", size=56, readonly=True,
                       default='config')
    data = fields.Binary(string="File", readonly=True)
    state = fields.Selection(
        [('export', 'export'), ('down', 'down')],
        default='export')
    username = fields.Char(String="User", default="openerp")

    @api.multi
    def generate_ssh_config_file(self):
        res = ''
        username = self.username
        tms_host_env = self.env['tms.host']
        host_objs = tms_host_env.search([('state', '=', 'active')])
        for host in host_objs:
            host_info = "host " + str(host.name) or ""
            host_info += "\n"
            host_info += "hostname " + str(host.host_address) or ""
            host_info += "\n"
            host_info += 'user ' + username or ''
            host_info += "\n"
            host_info += 'port ' + str(host.port) or ''
            host_info += "\n\n"
            res += host_info
        data = base64.encodestring(res)

        self.write({'data': data, 'state': 'down', 'name': 'config'})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ssh.config',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'views': [(False, 'form')],
            'target': 'new',
        }
