# -*- coding: utf-8 -*-
__author__ = 'chanhle'

from openerp.addons.web.controllers.main import ExcelExport, content_disposition
import openerp.addons.web.http as oeweb
from cStringIO import StringIO
import re
import operator
import simplejson

try:
    import xlwt
except ImportError:
    xlwt = None


class ExcelExport(ExcelExport):
    @oeweb.httprequest
    def index(self, req, data, token):
        model, fields, ids, domain, import_compat = \
            operator.itemgetter('model', 'fields', 'ids', 'domain',
                                'import_compat')(
                simplejson.loads(data))

        Model = req.session.model(model)
        ids = ids or Model.search(domain, 0, False, False, req.context)
        for field in fields:
            field_names = map(operator.itemgetter('name'), fields)
        # get type of fields
        fields_data = Model.fields_get(field_names, req.context)
        field_types = []
        for name in field_names:
            if name in fields_data:
                field_types.append({'name': name, 'type': fields_data[name]['type']})
            else:
                field_types.append({'name': name, 'type': 'strange' })

        import_data = Model.export_data(ids, field_names, req.context).get('datas', [])

        if import_compat:
            columns_headers = field_names
        else:
            columns_headers = [val['label'].strip() for val in fields]
            # add field_types for this parameter
        return req.make_response(self.from_data(columns_headers, import_data, field_types),
                                 headers=[('Content-Disposition',
                                           content_disposition(self.filename(model), req)),
                                          ('Content-Type', self.content_type)],
                                 cookies={'fileToken': token})


    def from_data(self, fields, rows, field_types):
        """
        :param fields:
        :param rows:
        :return:
        """
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')
        # delete external id
        del fields[0]
        for i, fieldname in enumerate(fields):
            worksheet.write(0, i, fieldname)
            worksheet.col(i).width = 8000 # around 220 pixels

        style = xlwt.easyxf('align: wrap yes')

        fmts = {'general': 'general', 'integer': '0', 'float': '#,##0.00'}
        del field_types[0]
        for row_index, row in enumerate(rows):
            # delete cell external id
            del row[0]
            for cell_index, cell_value in enumerate(row):
                if isinstance(cell_value, basestring):
                    cell_value = re.sub("\r", " ", cell_value)
                if cell_value is False: cell_value = None
#                for specific field float but display in integer like Quality On Hand
                if field_types[cell_index]['name'] in ['.id']:
                    cell_value = cell_value and int(cell_value) or ''
                    style.num_format_str = fmts['integer']
                if cell_value and field_types[cell_index]['type'] == 'float' \
                    and field_types[cell_index]['name'] in ['qty_available']:
                    cell_value = int(float(cell_value))
                    style.num_format_str = fmts['integer']
                elif cell_value and field_types[cell_index]['type'] == 'integer':
                    cell_value = int(cell_value)
                    style.num_format_str = fmts['integer']
                elif cell_value and field_types[cell_index]['type'] == 'float':
                    cell_value = float(cell_value)
                    style.num_format_str = fmts['float']
                else:
                    style.num_format_str = ''
                worksheet.write(row_index + 1, cell_index, cell_value, style)

        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

