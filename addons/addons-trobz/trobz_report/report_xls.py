# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from xlwt.Style import default_style
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import xlwt
import logging

_logger = logging.getLogger(__name__)


class AttrDict(dict):

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class report_xls():

    xls_types = {
        'bool': xlwt.Row.set_cell_boolean,
        'date': xlwt.Row.set_cell_date,
        'text': xlwt.Row.set_cell_text,
        'number': xlwt.Row.set_cell_number,
    }
    xls_types_default = {
        'bool': False,
        'date': None,
        'text': '',
        'number': 0,
    }

    # header/footer
    hf_params = {
        'font_size': 8,
        'font_style': 'I',  # B: Bold, I:  Italic, U: Underline
    }

    xls_headers = {
        'standard': '',
    }
    xls_footers = {
        'standard': ('&L&%(font_size)s&%(font_style)s' +
                     datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT) +
                     '&R&%(font_size)s&%(font_style)s&P / &N') % hf_params,
    }

    # styles
    _pfc = '26'  # default pattern fore_color
    _bc = '0'   # borders color 0: black color
    decimal_format = '#,##0.00'
    date_format = 'YYYY-MM-DD'
    xls_styles = {
        'xls_title': 'font: bold true, height 240;',
        'bold': 'font: bold true;',
        'underline': 'font: underline true;',
        'italic': 'font: italic true;',
        'fill': 'pattern: pattern solid, fore_color %s;' % _pfc,
        'fill_blue': 'pattern: pattern solid, fore_color 27;',
        'fill_grey': 'pattern: pattern solid, fore_color 22;',
        # 'borders_all': 'borders: left thin, right thin, top thin, bottom thin
        # 'left_colour %s, right_colour %s, top_colour %s, bottom_colour %s;'
        # % (_bc, _bc, _bc, _bc),
        'borders_all': 'borders: left thin, right thin, top thin,\
                         bottom thin;',
        'left': 'align: horz left;',
        'center': 'align: horz center;',
        'right': 'align: horz right;',
        'wrap': 'align: wrap true;',
        'top': 'align: vert top;',
        'bottom': 'align: vert bottom;',

        # Trobz customize style
        'middle': 'align: vert center;',
    }

    def xls_row_template(self, specs, wanted_list):
        """
        Returns a row template.

        Input:
        - 'wanted_list': list of Columns that will be returned
            in the row_template
        - 'specs': list with Column Characteristics
            0: Column Name (from wanted_list)
            1: Column Colspan
            2: Column Size (unit = the width of the character ’0′ as
                it appears in the sheet’s default font)
            3: Column Type
            4: Column Data
            5: Column Formula (or 'None' for Data)
            6: Column Style
        """
        r = []
        col = 0
        for w in wanted_list:
            found = False
            for s in specs:
                if s[0] == w:
                    found = True
                    s_len = len(s)
                    c = list(s[:5])
                    # set write_cell_func or formula
                    if s_len > 5 and s[5] is not None:
                        c.append({'formula': s[5]})
                    else:
                        c.append({'write_cell_func':
                                  report_xls.xls_types[c[3]]})
                    # Set custom cell style
                    if s_len > 6 and s[6] is not None:
                        c.append(s[6])
                    else:
                        c.append(None)
                    # Set cell formula
                    if s_len > 7 and s[7] is not None:
                        c.append(s[7])
                    else:
                        c.append(None)
                    r.append((col, c[1], c))
                    col += c[1]
                    break
            if not found:
                _logger.warn("report_xls.xls_row_template, column '%s' not\
                            found in specs", w)
        return r

    def xls_write_row(self, ws, row_pos, row_data,
                      row_style=default_style, set_column_size=False):
        r = ws.row(row_pos)
        for col, size, spec in row_data:
            data = spec[4]
            formula = spec[5].get('formula')\
                and xlwt.Formula(spec[5]['formula']) or None
            style = spec[6] and spec[6] or row_style
            if not data:
                # if no data, use default values
                data = report_xls.xls_types_default[spec[3]]
            if size != 1:
                if formula:
                    ws.write_merge(row_pos, row_pos,
                                   col, col + size - 1, data, style)
                else:
                    ws.write_merge(row_pos, row_pos,
                                   col, col + size - 1, data, style)
            else:
                if formula:
                    ws.write(row_pos, col, formula, style)
                else:
                    try:
                        spec[5]['write_cell_func'](r, col, data, style)
                    except:
                        _logger.warn('Error at spec: %s .', spec)
            if set_column_size:
                ws.col(col).width = spec[2] * 256
        return row_pos + 1

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
