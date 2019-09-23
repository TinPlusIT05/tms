# -*- coding: utf-8 -*-
import base64
import os
from subprocess import Popen, PIPE
from openerp import models, api, fields


class erppeek_report_wizard(models.TransientModel):
    _name = "erppeek.report.wizard"

    erppeek_config_id = fields.Many2one(
        "erppeek.report.config", "ERP Peeks Report Config", required=True)
    login = fields.Char(
        default=lambda self: self.env.user.login, readonly=True)
    password = fields.Char("Password", size=64, required=True)
    command_options_guide = fields.Char(
        related='erppeek_config_id.command_options_guide',
        string="Command Options Guide", readonly=True
    )
    command_options = fields.Char("Command Options")
    xlsx_file = fields.Binary("xlsx_file")
    res_fname = fields.Char("res_fname")

    @api.multi
    def button_export_erppeek_report(self):

        temp = self.erppeek_config_id.tms_instance_id.xmlrpc_url.split('//')
        https_password = self.env.user.read_secure(
            fields=['https_password'])[0].get('https_password', 'n0-@pplY')
        server = '%s//%s:%s@%s' % (temp[0], self.login,
                                   https_password, temp[1])
        execute_command = (
            'cd erppeek; ' + self.erppeek_config_id.command +
            ' ' + self.erppeek_config_id.file_path +
            ' -s ' + server +
            ' -db ' + self.erppeek_config_id.database_id.name +
            ' -u ' + self.login +
            ' -p ' + self.password +
            ' ' + self.command_options)
        process = Popen(execute_command, stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = process.communicate()
        if stdout and not stderr:
            index = stdout.find("Report")
            if index != -1:
                file_name = stdout[index + 7:-16][11:-9]
                path_export = self.get_erppeek_dir_path() + '/' + file_name
                # Write attachment
                xlsx_file = open(
                    path_export, 'rb')
                attach_data = base64.encodestring(xlsx_file.read())
                self.write(
                    {'xlsx_file': attach_data, 'res_fname': file_name})
                xlsx_file.close()
        else:
            return {}
        models_data = self.env['ir.model.data']

        form_view_obj = models_data.xmlid_to_object(
            "tms_modules.view_erppeek_report_wizard_form_download")
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'erppeek.report.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'name': 'Download',
            'view_id': form_view_obj and form_view_obj[0].id or False,
            'target': 'new',
            'res_id': self[0].id,
        }

    def get_erppeek_dir_path(self):
        head = os.getcwd()
        search_root = True
        while search_root:
            if os.path.exists(os.path.join(head, '.trobz')):
                project_dir_path = os.path.join(head, 'erppeek')
                return project_dir_path
            head = os.path.split(head)[0]
