# -*- coding: utf-8 -*-
from openerp.report import report_sxw
from openerp import SUPERUSER_ID
import xlwt
from openerp.addons.report_xls.report_xls\
    import report_xls  # @UnresolvedImport
from openerp.tools.translate import _


class Parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        # when calling super function. use SUPPERUSER_ID to pass this statement
        # 'lang': user.company_id.partner_id.lang
        # Because customer user cannot read 'user.company_id.partner_id'

        super(Parser, self).__init__(cr, SUPERUSER_ID, name, context)
        self.localcontext.update({
            # Define function which will be used in generate_xls_report
            "get_mapping_ticket_type": self.get_mapping_ticket_type,
            "get_mapping_ticket_status": self.get_mapping_ticket_status,
            "get_support_tickets": self.get_support_tickets,

            # Define variable
            "report_name": _('Delivery Acceptance Report'),
        })

    def get_mapping_ticket_type(self, value):
        types = dict(self.pool.get("tms.support.ticket").list_ticket_type)
        return types.get(value)

    def get_mapping_ticket_status(self, value):
        statuses = dict(self.pool.get("tms.support.ticket").list_states)
        return statuses.get(value)

    def get_support_tickets(self, wizard):

        # start_date = datetime.strftime(
        #     datetime.strptime(
        #         wizard.start_date, DEFAULT_SERVER_DATETIME_FORMAT),
        #     DEFAULT_SERVER_DATE_FORMAT)

        # end_date = datetime.strftime(
        #     datetime.strptime(
        #         wizard.end_date, DEFAULT_SERVER_DATE_FORMAT),
        #     DEFAULT_SERVER_DATE_FORMAT)
        domain = [('project_id', 'in', wizard.project_ids.ids),
                  ('create_date', '>=', wizard.start_date),
                  ('create_date', '<=', wizard.end_date)]

        if wizard.activity_ids:
            domain.append(('tms_activity_id', 'in', wizard.activity_ids.ids))

        ticket_ids = self.pool.get('tms.support.ticket').search(
            self.cr, self.uid, domain)
        tickets = self.pool.get('tms.support.ticket').browse(
            self.cr, self.uid, ticket_ids)
        return tickets

    def get_project_list(self, wizard):
        return ', '.join([project.name for project in wizard.project_ids])


_column_sizes = [
    ('No', 8),
    ('Description', 25),
    ('Ticket', 13),
    ('Milestone', 13),
    ('Status', 13),
    ('Assignee', 13),
    ('Start Date', 13),
    ('End Date', 13),
    ('Ticket Type', 13),
    ('Project', 13),
    ('Workload', 13),
]


class delivery_acceptance_report_xls(report_xls):
    column_sizes = [x[1] for x in _column_sizes]

    """
        returns xls report

        Input:
        - _p: Parse Class
        - _xs : xls_styles
        - data : wizard datas
        - objects :
        - wb: Excel Workbook
    """

    def generate_xls_report(self, _p, _xs, data, objects, wb):

        ws = wb.add_sheet(_p.report_name[:31], cell_overwrite_ok=True)
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 0
        row_pos = 0

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']
        workload_formula = '#0.000'

        # Title
        ws.row(row_pos).height_mismatch = True
        ws.row(row_pos).height = 256 * 2  # normal height have 256 units
        cell_big_title_style = xlwt.easyxf(_xs['wrap'] +
                                           _xs['center'] +
                                           _xs['bold'] +
                                           'align: vert center;' +
                                           'font: height 300;')
        cell_big_title_style_number = xlwt.easyxf(
            _xs['wrap'] + _xs['center'] + _xs['bold'] + 'align: vert center;' +
            'font: height 300;', num_format_str=workload_formula)

        cell_information_style = xlwt.easyxf(_xs['wrap'] +
                                             _xs['left'] +
                                             _xs['bold'] +
                                             'align: vert center;' +
                                             'font: height 200;')
        report_name = _p.report_name.upper()
        c_specs = [
            ('report_name', 11, 0, 'text', report_name),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_big_title_style)

        ws.row(row_pos).height_mismatch = True
        ws.row(row_pos).height = 300
        # Projects
        c_specs = [
            ('project_list', 11, 0, 'text', 'Project(s): ' + ', '.join(
                [project.name for project in objects[0].project_ids])),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_information_style)

        ws.row(row_pos).height_mismatch = True
        ws.row(row_pos).height = 300
        # From Date
        c_specs = [
            ('from_date', 11, 0, 'text', 'Date From: ' +
                objects[0].start_date),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_information_style)

        ws.row(row_pos).height_mismatch = True
        ws.row(row_pos).height = 300
        # To Date
        c_specs = [
            ('to_date', 11, 0, 'text', 'Date To: ' + objects[0].end_date),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_information_style)

        # write empty row to define column sizes
        c_sizes = self.column_sizes
        c_specs = [('empty%s' % i, 1, c_sizes[i], 'text', None)
                   for i in range(0, len(c_sizes))]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data,
                                     set_column_size=True)

        # Header Table
        header_format = _xs['bold'] + _xs['fill_blue'] + \
            _xs['borders_all'] + _xs['wrap'] + 'alignment: wrap on;'
        cell_style_center = xlwt.easyxf(header_format +
                                        _xs['center'] +
                                        'align: vert center;')

        col_specs_template = {
            item[0]: {
                'header': [1, item[1], 'text', item[0]]
            }
            for item in _column_sizes
        }

        column_list = [x[0] for x in _column_sizes]

        ws.row(row_pos).height_mismatch = True
        ws.row(row_pos).height = 300
        c_specs = map(lambda x: self.render(x, col_specs_template, 'header'),
                      column_list)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])

        for col, size, spec in row_data:
            data = spec[4]
            style = spec[6] and spec[6] or cell_style_center
            if not data:
                # if no data, use default values
                data = report_xls.xls_types_default[spec[3]]
            if size != 1:
                ws.write_merge(row_pos, row_pos,
                               col, col + size - 1, data, style)
            else:
                ws.write_merge(row_pos, row_pos + 1, col, col, data, style)
            ws.col(col).width = spec[2] * 256
        row_pos += 2

        cell_format = _xs['borders_all'] + 'align: vert center;' + \
            _xs['wrap'] + 'alignment: wrap on;'
        cell_style = xlwt.easyxf(cell_format + _xs['center'])
        cell_style_number = xlwt.easyxf(cell_format + _xs['center'],
                                        num_format_str=workload_formula)
        cell_style_left = xlwt.easyxf(cell_format + _xs['left'])
        nb = 0
        begin_row = row_pos + 1
        for st in _p.get_support_tickets(objects[0]):
            ws.row(row_pos).height_mismatch = True
            ws.row(row_pos).height = 3 * 256
            nb += 1
            c_specs = [
                ('no', 1, 0, 'number', nb, None, cell_style),
                ('description', 1, 0, 'text',
                 st.summary, None, cell_style_left),
                ('ticketid', 1, 0, 'number', st.name, None, cell_style),
                ('milestone', 1, 0, 'text',
                    st.milestone_number or 0, None, cell_style),
                ('status', 1, 0, 'text',
                 _p.get_mapping_ticket_status(st.state), None, cell_style),
                ('assignee', 1, 0, 'text',
                 st.owner_id and st.owner_id.name or '', None, cell_style),
                ('start_date', 1, 0, 'text', st.create_date, None, cell_style),
                ('end_date', 1, 0, 'text',
                    st.closing_datetime, None, cell_style),
                ('ttype', 1, 0, 'text',
                 _p.get_mapping_ticket_type(st.ticket_type), None, cell_style),
                ('project', 1, 0, 'text',
                 st.project_id and st.project_id.name or '', None, cell_style),
                ('workload_char', 1, 0, 'number',
                    float(st.workload_char), None, cell_style_number),
            ]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data,
                                         row_style=cell_style)
        end_row = row_pos

        ws.row(row_pos).height_mismatch = True
        ws.row(row_pos).height = 256 * 2

        ws.write_merge(row_pos, row_pos,
                       0, 2, 'Total Workload Manday', cell_big_title_style)

        ws.write(row_pos, 10, xlwt.Formula(
            "SUM(K%s:K%s)" % (begin_row, end_row)),
            cell_big_title_style_number)


delivery_acceptance_report_xls('report.delivery_acceptance_report',
                               'delivery.acceptance.wizard', parser=Parser)
