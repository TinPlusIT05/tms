# -*- coding: utf-8 -*-
##############################################################################
# @UnresolvedImport
from openerp.addons.tms_modules.model.hr.tms_working_hour import SUPPORT_TYPE

from openerp.report import report_sxw
from datetime import date

import xlwt
from openerp.addons.report_xls.report_xls import report_xls
from openerp.tools.translate import _


class Parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            "get_print_date": self.get_print_date,
            "get_mapping_forge_priority": self.get_mapping_forge_priority,

            "get_mapping_support_priority": self.get_mapping_support_priority,
            "get_mapping_support_type": self.get_mapping_support_type,

            "get_mapping_billable": self.get_mapping_billable,
            "get_mapping_wh_support_type": self.get_mapping_wh_support_type,

            "get_forge_data": self.get_forge_data,
            "get_support_data": self.get_support_data,

            "get_wizard_data": self.get_wizard_data,
            "get_working_hours": self.get_working_hours,

            "report_name": _('WORKING HOURS EXPORT REPORT'),
        })

    def get_print_date(self):
        return str(date.today())

    def get_mapping_forge_priority(self, value):
        priotities = dict(self.pool.get("tms.forge.ticket").PRIORITY)
        return priotities.get(value)

    def get_mapping_support_priority(self, value):
        priorities = dict(self.pool.get("tms.support.ticket").list_priority)
        return priorities.get(value)

    def get_mapping_support_type(self, value):
        types = dict(self.pool.get("tms.support.ticket").list_ticket_type)
        return types.get(value)

    def get_mapping_billable(self, value):
        if value:
            return "Yes"
        return "No"

    def get_mapping_wh_support_type(self, value):
        types = dict(SUPPORT_TYPE)
        return types.get(value)

    def get_forge_data(self, forge):
        return forge and {
            "name": forge.name,
            "priority": forge.priority,
        } or {}

    def get_support_data(self, support):
        return support and {
            "name": support.name,
            "priority": support.priority,
            "ticket_type": support.ticket_type
        } or {}

    def get_wizard_data(self):
        return self.localcontext.get("data")

    def get_working_hours(self):

        # Get wizard input data
        wizard_input_data = self.get_wizard_data()

        # compose Order By clause
        domain = []
        order_by = "sprint DESC, date DESC, project_id ASC, user_id ASC"

        # Support tickets will be exported for which projects
        if wizard_input_data.get('project_ids'):
            domain.append(('project_id', 'in',
                           wizard_input_data.get('project_ids')))

        # Within a specific period
        if wizard_input_data.get('from_date'):
            domain.append(('date', '>=', wizard_input_data.get('from_date')))

        # Within a specific period
        if wizard_input_data.get('to_date'):
            domain.append(('date', '<=', wizard_input_data.get('to_date')))

        # get Working hours data
        working_pool = self.pool.get("tms.working.hour")
        working_ids = working_pool.search(
            self.cr, self.uid, domain, order=order_by) or False
        working_hours = working_ids and working_pool.browse(
            self.cr, self.uid, working_ids) or []

        return working_hours


class working_hours_export_xls(report_xls):

    '''
    Return xls report

    Input:
    - _p: Parse Class
    - _xs: xls_style
    - data: Wizard datas
    - objects:
    - wb: Excel Workbook
    If you want more colors:
    https://github.com/python-excel/xlwt/blob/master/xlwt/Style.py
    '''

    def generate_xls_report(self, _p, _xs, data, objects, wb):
        ws = wb.add_sheet(_p.report_name[:31], cell_overwrite_ok=True)
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 0
        row_pos = 0
        _bc = 'black'
        _xs['borders_all'] = 'borders: left thin, \
            right thin, top thin, bottom thin, \
            left_colour %s, right_colour %s, \
            top_colour %s, bottom_colour %s;' % (_bc, _bc, _bc, _bc)
        _xs['middle'] = 'align: vert center;'
        _xs['alignment'] = 'alignment: wrap on;'
        _xs['fill_pale_blue'] = 'pattern: pattern solid, fore_color pale_blue;'
        _xs['fill_ice_blue'] = 'pattern: pattern solid, fore_color ice_blue;'
        _xs['fill_light_turquoise'] = 'pattern: pattern solid, \
            fore_color light_turquoise;'
        _xs['fill_sky_blue'] = 'pattern: pattern solid, \
            fore_color sky_blue;'

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        # Title
        ws.row(row_pos).height_mismatch = True
        ws.row(row_pos).height = 256 * 2  # normal height have 256 units
        cell_big_title_style = xlwt.easyxf(_xs['wrap'] +
                                           _xs['left'] +
                                           _xs['bold'] +
                                           'font: height 300;')
        report_name = _p.report_name.upper() + ': ' + _p.get_print_date()
        c_specs = [
            ('report_name', 10, 0, 'text', report_name),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_big_title_style)

        # Write an empty line
        c_specs = [
            ('empty', 1, 0, 'text', None),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_big_title_style)

        # Write from date, to date
        ws.row(row_pos).height_mismatch = True
        ws.row(row_pos).height = 2 * 256
        cell_format = _xs['middle'] + \
            _xs['wrap'] + \
            _xs['alignment']
        cell_format_bold = cell_format + _xs['bold']
        cell_style_bold_left = xlwt.easyxf(cell_format_bold + _xs['left'])
        c_specs = [
            ('fromdate', 2, 15, 'text', _('FROM DATE: ') +
             data.get('from_date', None)),
            ('todate', 2, 15, 'text', _('TO DATE: ') +
             data.get('to_date', None)),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style_bold_left)

        # Write an empty line
        c_specs = [
            ('empty', 1, 0, 'text', None),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_big_title_style)

        # CSS for Header
        header_format = _xs['bold'] + _xs['fill_grey'] + \
            _xs['borders_all'] + _xs['wrap'] + \
            _xs['alignment'] + _xs['middle'] + _xs['center']
        header_style_center = xlwt.easyxf(header_format)
        header_style_center_force = xlwt.easyxf(header_format +
                                                _xs['fill_ice_blue'])
        header_style_center_support = xlwt.easyxf(header_format +
                                                  _xs['fill_pale_blue'])
        # Header table
        col_specs_template = {
            'SPRINT': {
                'header': [1, 12, 'text', _('SPRINT')]
            },
            'DATE': {
                'header': [1, 12, 'text', _('DATE')]
            },
            'USER': {
                'header': [1, 16, 'text', _('USER')]
            },
            'NAME': {
                'header': [1, 16, 'text', _('NAME')]
            },
            'PROJECT': {
                'header': [1, 16, 'text', _('PROJECT')]
            },
            'ACTIVITY': {
                'header': [1, 16, 'text', _('ACTIVITY')]
            },
            'DURATION': {
                'header': [1, 12, 'text', _('DURATION')]
            },
            'FORCE TICKET': {
                'header': [2, 14, 'text', _('FORGE TICKET'), None,
                           header_style_center_force]
            },
            'SUPPORT TICKET': {
                'header': [3, 14, 'text', _('SUPPORT TICKET'), None,
                           header_style_center_support]
            },
            'ANALYTIC SECOND AXIS': {
                'header': [1, 18, 'text', _('ANALYTIC SECOND AXIS')]
            },
            'BILLABLE': {
                'header': [1, 12, 'text', _('BILLABLE')]
            },
            'WEEKDAY': {
                'header': [1, 12, 'text', _('WEEKDAY')]
            },
            'CUSTOMER': {
                'header': [1, 14, 'text', _('CUSTOMER')]
            },
            'COMPANY': {
                'header': [1, 14, 'text', _('COMPANY')]
            },
            'SUPPORT TYPE': {
                'header': [1, 14, 'text', _('SUPPORT TYPE')]
            },
            'USERNAME': {
                'header': [1, 14, 'text', _('USERNAME')]
            },
        }
        columns_list = [
            'SPRINT', 'DATE', 'USER', 'NAME',
            'PROJECT', 'ACTIVITY', 'DURATION', 'FORCE TICKET',
            'SUPPORT TICKET', 'ANALYTIC SECOND AXIS', 'BILLABLE',
            'WEEKDAY', 'CUSTOMER', 'COMPANY', 'SUPPORT TYPE', 'USERNAME',
        ]
        sub_col_specs_template1 = {
            'ID': {
                'header': [1, 14, 'text', _('ID')]
            },
            'PRIORITY': {
                'header': [1, 14, 'text', _('PRIORITY')]
            },
        }
        sub_columns_list1 = [
            'ID', 'PRIORITY'
        ]
        sub_col_specs_template2 = {
            'ID': {
                'header': [1, 112, 'text', _('ID')]
            },
            'PRIORITY': {
                'header': [1, 14, 'text', _('PRIORITY')]
            },
            'TICKET TYPE': {
                'header': [1, 18, 'text', _('TICKET TYPE')]
            },
        }
        sub_columns_list2 = [
            'ID', 'PRIORITY', 'TICKET TYPE'
        ]

        ws.row(row_pos).height_mismatch = True
        ws.row(row_pos).height = 300
        c_specs = map(lambda x: self.render(x, col_specs_template, 'header'),
                      columns_list)
        sub_c_specs1 = map(lambda x: self.render(x, sub_col_specs_template1,
                                                 'header'), sub_columns_list1)
        sub_c_specs2 = map(lambda x: self.render(x, sub_col_specs_template2,
                                                 'header'), sub_columns_list2)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        sub_row_data1 = self.xls_row_template(sub_c_specs1,
                                              [x[0] for x in sub_c_specs1])
        sub_row_data2 = self.xls_row_template(sub_c_specs2,
                                              [x[0] for x in sub_c_specs2])
        for col, size, spec in row_data:
            data = spec[4]
            style = spec[6] and spec[6] or header_style_center
            if not data:
                # if no data, use default values
                data = report_xls.xls_types_default[spec[3]]
            if size != 1 and spec:
                ws.write_merge(row_pos, row_pos,
                               col, col + size - 1, data, style)
                if spec[0] == 'FORCE TICKET':
                    for sub_col, sub_size, sub_spec in sub_row_data1:
                        sub_data = sub_spec[4]
                        sub_style = sub_spec[6] and \
                            sub_spec[6] or header_style_center_force
                        if sub_size == 1:
                            ws.col(col + sub_col).width = spec[2] * 256
                            ws.row(row_pos + 1).height = 600
                            ws.write_merge(row_pos + 1, row_pos + 1,
                                           col + sub_col, col + sub_col +
                                           sub_size - 1,
                                           sub_data, sub_style)
                elif spec[0] == 'SUPPORT TICKET':
                    for sub_col, sub_size, sub_spec in sub_row_data2:
                        sub_data = sub_spec[4]
                        sub_style = sub_spec[6] and \
                            sub_spec[6] or header_style_center_support
                        if sub_size == 1:
                            ws.col(col + sub_col).width = spec[2] * 256
                            ws.row(row_pos + 1).height = 600
                            ws.write_merge(row_pos + 1, row_pos + 1,
                                           col + sub_col, col + sub_col +
                                           sub_size - 1,
                                           sub_data, sub_style)
            else:
                ws.write_merge(row_pos, row_pos + 1, col, col, data, style)
            ws.col(col).width = spec[2] * 256
        row_pos += 2

        # Write content
        # CSS for cell
        cell_format = _xs['wrap'] + _xs['alignment'] + \
            _xs['middle'] + _xs['borders_all']
        cell_style = xlwt.easyxf(cell_format + _xs['center'])
        cell_style_left = xlwt.easyxf(cell_format + _xs['left'])
        cell_style1 = xlwt.easyxf(cell_format + _xs['center'] +
                                  _xs['fill_light_turquoise'])
        cell_style2 = xlwt.easyxf(cell_format + _xs['center'] +
                                  _xs['fill_sky_blue'])
        for wh in _p.get_working_hours():
            ws.row(row_pos).height_mismatch = True
            ws.row(row_pos).height = 2 * 256
            c_specs = [
                ('sprint', 1, 0, 'text',
                 wh.sprint and wh.sprint or ' ', None, cell_style),
                ('date', 1, 0, 'text', str(wh.date) or ' ', None, cell_style),
                ('user', 1, 0, 'text',
                 wh.user_id and wh.user_id.name or ' ', None, cell_style),
                ('name', 1, 0, 'text', wh.name or ' ', None, cell_style_left),
                ('project', 1, 0, 'text',
                 wh.project_id and wh.project_id.name or ' ',
                 None, cell_style),
                ('activity', 1, 0, 'text',
                 wh.tms_activity_id and wh.tms_activity_id.name or ' ',
                 None, cell_style),
                ('duration', 1, 0, 'number', wh.duration_hour or 0,
                 None, cell_style),
                ('fid', 1, 0, 'text',
                 str(_p.get_forge_data(
                     wh.tms_forge_ticket_id).get("name", ' ')),
                 None, cell_style1),
                ('fpriority', 1, 0, 'text',
                 _p.get_mapping_forge_priority(
                     _p.get_forge_data(
                         wh.tms_forge_ticket_id).get("priority", ' ')),
                 None, cell_style1),
                ('sid', 1, 0, 'text',
                 str(_p.get_support_data(
                     wh.tms_support_ticket_id).get("name", ' ')),
                 None, cell_style2),
                ('spriority', 1, 0, 'text',
                 _p.get_mapping_support_priority(
                     _p.get_support_data(
                         wh.tms_support_ticket_id).get("priority", ' ')),
                 None, cell_style2),
                ('type', 1, 0, 'text',
                 _p.get_mapping_support_type(
                     _p.get_support_data(
                         wh.tms_support_ticket_id).get("ticket_type", ' ')),
                 None, cell_style2),
                ('ana', 1, 0, 'text',
                 wh.analytic_secondaxis_id and
                 wh.analytic_secondaxis_id.name or ' ', None, cell_style),
                ('billable', 1, 0, 'text',
                 _p.get_mapping_billable(wh.is_billable) or ' ',
                 None, cell_style),
                ('weekday', 1, 0, 'text', wh.weekday or 1, None, cell_style),
                ('customer', 1, 0, 'text',
                 wh.project_id and wh.project_id.partner_id and
                 wh.project_id.partner_id.name or '', None, cell_style),
                ('company', 1, 0, 'text',
                 wh.project_id and wh.project_id.partner_id and
                 wh.project_id.partner_id.company_id and
                 wh.project_id.partner_id.company_id.name or '',
                 None, cell_style),
                ('stype', 1, 0, 'text',
                 _p.get_mapping_wh_support_type(wh.support_type) or ' ',
                 None, cell_style),
                ('username', 1, 0, 'text', wh.user_id and
                 wh.user_id.login or ' ', None, cell_style),
            ]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data)


working_hours_export_xls('report.working_hours_export',
                         'tms.working.hour',
                         parser=Parser)
