# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2016 Trobz (<http://trobz.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api
from datetime import datetime
import tempfile
import zipfile
import os
import base64


class DowloadAllAttachmentsWizard(models.TransientModel):
    _name = 'dowload.all.attachments.wizard'

    datas = fields.Binary(string='All Attachment .Zip File')
    file_name = fields.Char('File Name')
    state = fields.Selection(
        [('before', 'Before'),
         ('after', 'After')], string='State', default='before')

    @api.multi
    def button_zip_file(self):
        model_name = ''
        lang = self.env['res.lang'].\
            search([('code', '=', self._context.get('lang'))])
        dt_format = '%s %s' % (lang.date_format, lang.time_format)
        send_date = datetime.now().strftime(dt_format)
        reports_tmp_directory = tempfile.mkdtemp()
        # prepare zip file to save in directory /tmp
        date_time = datetime.now().strftime("%Y-%m-%d")
        zipfile_name = 'zip_all_file_attachments' + '_' + date_time + '.zip'
        zipfile_path = reports_tmp_directory + '/' + zipfile_name
        zf = zipfile.ZipFile(zipfile_path, mode='w')
        zf.close()
        ir_attachment_objs = self.get_attachments()
        dct_file_binary = self.create_dict_file_binary(ir_attachment_objs)
        for key, value in dct_file_binary.iteritems():
            self.add_file_to_directory(
                reports_tmp_directory, value, key)
        zip_files_name = [f for f in os.listdir(
            reports_tmp_directory) if os.path.isfile(
                os.path.join(reports_tmp_directory, f)) and f != zipfile_name]
        if zip_files_name:
            zf = zipfile.ZipFile(zipfile_path, mode='a')
            for file_name in zip_files_name:
                zf.write(reports_tmp_directory +
                         '/' + file_name, file_name)
            zf.close()
        f = open(zipfile_path, 'rb')
        data = base64.encodestring(f.read())
        active_model = self._context.get('active_model', False)
        if active_model:
            model_name = self.env[active_model]._description or ''
        name = '%s_Attachment_[%s].zip' % (model_name, send_date)
        attachment_values = {
            'name': name,
            'res_model': 'dowload.all.attachments.wizard',
            'datas_fname': name,
            'type': 'binary',
            'datas': data,
            'res_id': self.id
        }
        self.env['ir.attachment'].create(attachment_values)
        self.write({
            'datas': data,
            'file_name': name,
            'state': 'after'
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dowload.all.attachments.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    @api.multi
    def get_attachments(self):
        ir_attachment_objs = self.env['ir.attachment']
        active_model = self._context.get('active_model', False)
        active_ids = self._context.get('active_ids', [])
        for active_id in active_ids:
            ir_attachment_obj = self.env['ir.attachment'].search(
                [('res_model', '=', active_model),
                 ('res_id', '=', active_id)])
            ir_attachment_objs += ir_attachment_obj
        return ir_attachment_objs

    @api.multi
    def create_dict_file_binary(self, ir_attachment_objs):
        dct_file_binary = {}
        lst_file_name = []
        for ir_attachment in ir_attachment_objs:
            data = base64.b64decode(ir_attachment.datas)
            file_name = '%s_%s' % (
                ir_attachment.res_id, ir_attachment.name)
            if file_name in lst_file_name:
                file_name = self.get_filename_duplicate(
                    file_name, lst_file_name)
            lst_file_name.append(file_name)
            dct_file_binary.update({file_name: data})

        return dct_file_binary

    @api.model
    def get_filename_duplicate(self, file_name, lst_file_name):
        # Change name when name duplicate
        temp = file_name.split('.')
        count = 1
        if len(temp) == 2:
            name = file_name.replace('.', ' (%s).' % count)
            while (name in lst_file_name):
                count += 1
                name = file_name.replace('.', ' (%s).' % count)
        else:
            name = file_name + ' (%s)' % count
            while (name in lst_file_name):
                count += 1
                name = file_name + ' (%s)' % count
        return name

    @api.multi
    def add_file_to_directory(self, reports_tmp_directory, result, name):
        try:
            report_file = ''
            if name:
                report_file = '%s/%s' % (reports_tmp_directory, name)
                fp = open(report_file, 'wb+')
                fp.write(result)
                fp.close()
        except Exception:
            return False
        return True
