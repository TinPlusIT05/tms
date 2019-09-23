# -*- coding: utf-8 -*-
##############################################################################
from collections import OrderedDict
from openerp.addons.tms_modules.model.hr.tms_working_hour import SUPPORT_TYPE

from openerp.report import report_sxw

import xlwt
from openerp.addons.report_xls.report_xls import report_xls
from openerp.tools.translate import _

from datetime import date, datetime, timedelta


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

            "get_wh_data": self.get_wh_data,
            "get_total_data": self.get_total_data,

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
        order_by = "user_id ASC, project_id ASC, date DESC"

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

    def get_wh_data(self):
        datas = []
        temp_datas = OrderedDict()
        whs = self.get_working_hours()
        index = 0
        for wh in whs:
            support_ticket = wh.tms_support_ticket_id or None
            if not support_ticket and wh.project_id:
                data_key = '%s' % wh.id
                # Index
                index = index + 1
                data = [index, wh.name, str(wh.date), '-', '-',
                        '-', wh.user_id.partner_id.name, '-', '-', '-',
                        ' ', wh.project_id.name, round(
                            wh.duration_hour / 8.0, 3)
                        ]
                temp_datas[data_key] = data
            else:
                project = support_ticket.project_id or None

                # support_ticket summary
                summary = support_ticket.summary or '-',
                # wh date
                date = str(wh.date)
                # support_ticket id
                support_ticket_id = support_ticket.id or '-',
                # milestone number
                milestone = support_ticket.milestone_id or None
                milestone_number = milestone and milestone.number or '-'
                # support state
                status = {
                    'new': 'New',
                    'assigned': 'Assigned',
                    'planned_for_delivery': 'Planned for delivery',
                    'delivered': 'Delivered in Staging',
                    'ok_for_production': 'OK for production',
                    'ok_to_close': 'OK to close',
                    'closed': 'Closed'
                }
                support_state = '-'
                if support_ticket.state in status:
                    support_state = status[support_ticket.state]
                # employee
                partner = wh.user_id and wh.user_id.partner_id or None
                employee = partner and partner.name or '-'
                # support create date
                create_date = support_ticket.create_date
                local_create_date = datetime.strptime(
                    create_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
                support_create_date = str(local_create_date)
                # support closing date
                close_date = support_ticket.closing_datetime
                local_close_date = ''
                if close_date:
                    local_close_date = datetime.strptime(
                        close_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
                support_close_date = local_close_date and str(
                    local_close_date) or '-'
                # support Ok Production Date
                ok_production_date = support_ticket.ok_production_date
                local_ok_production_date = ''
                if ok_production_date:
                    local_ok_production_date = datetime.strptime(
                        ok_production_date, '%Y-%m-%d %H:%M:%S'
                    ) + timedelta(hours=7)
                support_ok_production_date = local_ok_production_date and str(
                    local_ok_production_date) or '-'
                # support ticket type
                ticket_type = support_ticket.ticket_type or None
                if ticket_type:
                    support_ticket_type = self.get_mapping_wh_support_type(
                        ticket_type)
                else:
                    support_ticket_type = '-'
                # project name
                project_name = project and project.name or '-',
                # duration hour
                duration_hour = round(wh.duration_hour / 8.0, 3)

                data_key = '%s-%s' % (support_ticket.id, partner.id)
                if data_key in temp_datas:
                    temp_datas[data_key][
                        12] += round(wh.duration_hour / 8.0, 3)
                    continue
                # Index
                index = index + 1
                data = [
                    index, summary[0], date, support_ticket_id[0],
                    milestone_number, support_state, employee,
                    support_create_date, support_close_date,
                    support_ok_production_date, support_ticket_type,
                    project_name[0], duration_hour,
                ]
                temp_datas[data_key] = data
        print("\n@@@@@@@@ tttttttttttttttt")
        for key in temp_datas.keys():
            datas.append(temp_datas[key])
            print("@@@@@@@@ ----------key----------", temp_datas[key])

        return datas

    def get_total_data(self):
        grand_total_manday = 0
        project_dict = OrderedDict()
        support_type_dict = OrderedDict()
        total_datas = {
            'grand_total_manday': grand_total_manday,
            'project_dict': project_dict,
            'support_type_dict': support_type_dict
        }
        for wh in self.get_working_hours():
            grand_total_manday = grand_total_manday + round(
                wh.duration_hour / 8.0, 3)
            support_ticket = wh.tms_support_ticket_id or None
            if support_ticket:
                # Compute total by project
                project_name = support_ticket.project_id and \
                    support_ticket.project_id.name or 'Other'
                if project_name in total_datas['project_dict']:
                    total_datas['project_dict'][
                        project_name] += round(wh.duration_hour / 8.0, 3)
                else:
                    total_datas['project_dict'][
                        project_name] = round(wh.duration_hour / 8.0, 3)
                # Compute total by ticket type
                support_type_name = self.get_mapping_wh_support_type(
                    support_ticket.ticket_type) or "Other"
                if support_type_name in total_datas['support_type_dict']:
                    total_datas['support_type_dict'][
                        support_type_name] += round(wh.duration_hour / 8.0, 3)
                else:
                    total_datas['support_type_dict'][
                        support_type_name] = round(wh.duration_hour / 8.0, 3)
        total_datas['grand_total_manday'] = grand_total_manday
        return total_datas


class working_hours_dedicate_export_xls(report_xls):

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
        row_pos = 0  # Mark position of row where is write to

        # ======= Define format ========
        _bc = 'black'
        _xs['borders_all'] = 'borders: left thin, \
            right thin, top thin, bottom thin, \
            left_colour %s, right_colour %s, \
            top_colour %s, bottom_colour %s;' % (_bc, _bc, _bc, _bc)
        _xs['middle'] = 'align: vert center;'
        _xs['alignment'] = 'alignment: wrap on;'
        _xs['fill_light_turquoise'] = 'pattern: pattern solid, \
            fore_color light_turquoise;'
        _xs['fill_sky_blue'] = 'pattern: pattern solid, \
            fore_color sky_blue;'

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        cell_big_title_style = xlwt.easyxf(_xs['wrap'] +
                                           _xs['left'] +
                                           _xs['bold'] +
                                           'font: height 300;')
        # CSS for Header
        header_format = _xs['bold'] + _xs['fill_grey'] + \
            _xs['borders_all'] + _xs['wrap'] + \
            _xs['alignment'] + _xs['middle'] + _xs['center']
        header_style_center = xlwt.easyxf(
            header_format + 'font: bold 1,height 240;')
        # CSS for cell
        cell_format = _xs['wrap'] + _xs['alignment'] + \
            _xs['middle'] + _xs['borders_all']
        cell_style_left = xlwt.easyxf(cell_format + _xs['left'])
        cell_style_right = xlwt.easyxf(cell_format + _xs['right'])
        cell_style_right_bold = xlwt.easyxf(
            cell_format + _xs['bold'] + _xs['right'] +
            'font: bold 1,height 280;'
        )

        # ======== Generate report ========
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
        # Write first empty line
        empty_rows = [
            ('empty', 1, 0, 'text', None),
        ]
        row_data = self.xls_row_template(
            empty_rows, [x[0] for x in empty_rows])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_big_title_style)

        # Header table
        header_template = {
            'No.': {
                'header': [1, 5, 'text', _('No')]
            },
            'Summary': {
                'header': [1, 40, 'text', _('Summary')]
            },
            'Date': {
                'header': [1, 10, 'text', _('Date')]
            },
            'Ticket': {
                'header': [1, 8, 'text', _('Ticket')]
            },
            'Milestone': {
                'header': [1, 14, 'text', _('Milestone')]
            },
            'Status': {
                'header': [1, 18, 'text', _('Status')]
            },
            'Employee': {
                'header': [1, 22, 'text', _('Employee')]
            },
            'Opening Date': {
                'header': [1, 12, 'text', _('Opening Date')]
            },
            'Closing Date': {
                'header': [1, 12, 'text', _('Closing Date')]
            },
            'Ok Production Date': {
                'header': [1, 12, 'text', _('Ok Production Date')]
            },
            'Ticket Type': {
                'header': [1, 20, 'text', _('Ticket Type')]
            },
            'Project': {
                'header': [1, 15, 'text', _('Project')]
            },
            'Manday': {
                'header': [1, 10, 'text', _('Manday')]
            },
        }
        header_columns = [
            'No.', 'Summary', 'Date', 'Ticket', 'Milestone', 'Status',
            'Employee', 'Opening Date', 'Closing Date', 'Ok Production Date',
            'Ticket Type', 'Project', 'Manday'
        ]

        ws.row(row_pos).height_mismatch = True
        ws.row(row_pos).height = 300
        print "... header_template: ", header_template
        header_rows = map(lambda x: self.render(x, header_template, 'header'),
                          header_columns)
        row_data = self.xls_row_template(
            header_rows, [x[0] for x in header_rows])
        for col, size, spec in row_data:
            data = spec[4]
            style = spec[6] and spec[6] or header_style_center
            ws.write_merge(row_pos, row_pos + 1, col, col, data, style)
            ws.col(col).width = spec[2] * 256
        row_pos += 2

        # Write content
        for line in _p.get_wh_data():
            ws.row(row_pos).height_mismatch = True
            ws.row(row_pos).height = 2 * 256

            c_specs = [
                ('index', 1, 0, 'text', str(line[0]), None, cell_style_right),
                ('summary', 1, 0, 'text', line[1], None, cell_style_left),
                ('date', 1, 0, 'text', line[2], None, cell_style_left),
                ('ticket', 1, 0, 'text', str(line[3]), None, cell_style_right),
                ('milestone', 1, 0, 'text', str(
                    line[4]), None, cell_style_left),
                ('state', 1, 0, 'text', str(line[5]), None, cell_style_left),
                ('employee', 1, 0, 'text', line[6], None, cell_style_left),
                ('create_date', 1, 0, 'text', str(
                    line[7]), None, cell_style_right),
                ('closing_datetime', 1, 0, 'text', str(
                    line[8]), None, cell_style_right),
                ('ok_production_date', 1, 0, 'text',
                 str(line[9]), None, cell_style_right),
                ('ticket_type', 1, 0, 'text', str(
                    line[10]), None, cell_style_left),
                ('project', 1, 0, 'text', str(
                    line[11]), None, cell_style_left),
                ('manday', 1, 0, 'number', str(
                    line[12]), None, cell_style_right),
            ]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data)

        # Print total data
        total_data = _p.get_total_data()
        # Print total grand
        ws.row(row_pos).height_mismatch = True
        ws.row(row_pos).height = 2 * 256
        label = "The Grand total man-day"
        value = str(total_data['grand_total_manday'])
        ws.write_merge(row_pos, row_pos, 0, 10, label, cell_style_right_bold)
        ws.write_merge(row_pos, row_pos, 11, 11, ' ', cell_style_right_bold)
        ws.write_merge(row_pos, row_pos, 12, 12, value, cell_style_right_bold)
        row_pos += 1
        # Print total manday per project
        for key, val in total_data['project_dict'].iteritems():
            ws.row(row_pos).height_mismatch = True
            ws.row(row_pos).height = 2 * 256
            label = "The total man-day of project %s" % key
            value = str(val)
            ws.write_merge(row_pos, row_pos, 0, 10,
                           label, cell_style_right_bold)
            ws.write_merge(row_pos, row_pos, 11, 11,
                           ' ', cell_style_right_bold)
            ws.write_merge(row_pos, row_pos, 12, 12,
                           value, cell_style_right_bold)
            row_pos += 1
        # Print total manday per support type
        for key, val in total_data['support_type_dict'].iteritems():
            ws.row(row_pos).height_mismatch = True
            ws.row(row_pos).height = 2 * 256
            label = "The total man-day of ticket type %s" % key
            value = str(val)
            ws.write_merge(row_pos, row_pos, 0, 10,
                           label, cell_style_right_bold)
            ws.write_merge(row_pos, row_pos, 11, 11,
                           ' ', cell_style_right_bold)
            ws.write_merge(row_pos, row_pos, 12, 12,
                           value, cell_style_right_bold)
            row_pos += 1


working_hours_dedicate_export_xls(
    'report.working_hours_dedicate_export',
    'tms.working.hour',
    parser=Parser
)
