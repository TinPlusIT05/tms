# -*- coding: utf-8 -*-
from openerp.osv import fields
from openerp.report import report_sxw
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

from operator import itemgetter
from datetime import date, datetime
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
            "get_print_date": self.get_print_date,
            "get_wizard_input_data": self.get_wizard_input_data,
            "format_datetime": self.format_datetime,
            "get_mapping_ticket_type": self.get_mapping_ticket_type,
            "get_mapping_priority": self.get_mapping_priority,
            "get_mapping_ticket_status": self.get_mapping_ticket_status,
            "get_last_comment": self.get_last_comment,
            "get_support_tickets": self.get_support_tickets,

            # Define variable
            "report_name": _('Trobz Customer Support Tickets Report'),
        })

    def get_print_date(self):
        return str(date.today())

    def format_datetime(self, date_string):
        if date_string:
            dot_index = date_string.find(".")
            if dot_index != -1:
                date_string = date_string[:dot_index]

        if isinstance(date_string, basestring):
            if date_string.find(' ') != -1:
                date_string = self.to_timezone(date_string,
                                               DEFAULT_SERVER_DATETIME_FORMAT)
            else:
                date_string = self.to_timezone(date_string,
                                               DEFAULT_SERVER_DATE_FORMAT)

        return date_string

    def to_timezone(self, timestring, time_format):
        _cdatetime = datetime.strptime(timestring, time_format)
        _ctime_zoned = fields.datetime.context_timestamp(self.cr, self.uid,
                                                         _cdatetime)
        return _ctime_zoned.strftime(time_format)

    def get_mapping_ticket_type(self, value):
        types = dict(self.pool.get("tms.support.ticket").list_ticket_type)
        return types.get(value)

    def get_mapping_priority(self, value):
        priorities = dict(self.pool.get("tms.support.ticket").list_priority)
        return priorities.get(value)

    def get_mapping_ticket_status(self, value):
        statuses = dict(self.pool.get("tms.support.ticket").list_states)
        return statuses.get(value)

    def get_last_comment(self, comments):
        cmts = []
        if comments:
            cmts = [(comment.name, comment.comment)
                    for comment in comments if comment.type == 'comment']
            cmts = sorted(cmts, reverse=True, key=itemgetter(0))
        return cmts and cmts[0] and cmts[0][1] or ""

    def get_wizard_input_data(self):
        return self.localcontext.get("data")

    def get_support_tickets(self):

        # Get wizard input data
        wizard_input_data = self.get_wizard_input_data()

        # Componse SQL Query
        sql_query, where_clause = u"""
            SELECT tst.id
            FROM tms_support_ticket tst
            JOIN res_users rus ON tst.owner_id = rus.id
            WHERE {0}
            ORDER BY tst.project_id, CASE
                WHEN tst.priority='urgent' THEN 0
                WHEN tst.priority='major' THEN 1
                WHEN tst.priority='normal' THEN 2
                WHEN tst.priority='minor' THEN 3
                ELSE 4
            END
        """, []

        # If user specified 'assigned to'
        if wizard_input_data.get("assigned_to"):
            if wizard_input_data["assigned_to"] == "trobz":
                where_clause.append(u"rus.is_trobz_member = 't'")
            else:
                where_clause.append(u"rus.is_trobz_member = 'f'")

        # If user specified 'owner'
        if wizard_input_data.get("owner_id", False):
            owner_id = wizard_input_data.get("owner_id")
            if isinstance(owner_id, list):
                owner_id = owner_id and owner_id[0]
            where_clause.append(u"tst.owner_id = {0}".format(owner_id))

        # If user specified 'project'
        if wizard_input_data.get("project_ids", []):
            project_ids = wizard_input_data.get("project_ids")
            project_ids = ",".join(map(str, project_ids))
            where_clause.append(u"tst.project_id IN ({0})".format(project_ids))

        # If user specified 'Opened'
        if wizard_input_data.get("ticket_type"):
            if wizard_input_data["ticket_type"] == "opened":
                where_clause.append(u"tst.state != 'closed'")
            elif wizard_input_data["ticket_type"] == "closed":
                where_clause.append(u"tst.state = 'closed'")

        # If user specifies opening date range
        if wizard_input_data.get("opening_fromdate"):
            where_clause.append(
                u"date(tst.create_date) >= '{0}'".format(
                    wizard_input_data.get('opening_fromdate')))

        if wizard_input_data.get("opening_todate"):
            where_clause.append(
                u"date(tst.create_date) <= '{0}'".format(
                    wizard_input_data.get('opening_todate')))

        # If user specifies quotation approval date range
        if wizard_input_data.get("quotation_approval_fromdate"):
            where_clause.append(
                u"date(tst.quotation_approved_date) >= '{0}'".format(
                    wizard_input_data.get('quotation_approval_fromdate')))

        if wizard_input_data.get("quotation_approval_todate"):
            where_clause.append(
                u"date(tst.quotation_approved_date) <= '{0}'".format(
                    wizard_input_data.get('quotation_approval_todate')))

        # If user specifies invoicing date range
        if wizard_input_data.get("invoicing_fromdate"):
            where_clause.append(
                u"date(tst.date) >= '{0}'".format(
                    wizard_input_data.get('invoicing_fromdate')))

        if wizard_input_data.get("invoicing_todate"):
            where_clause.append(
                u"date(tst.date) <= '{0}'".format(
                    wizard_input_data.get('invoicing_todate')))

        # If user specifies staging delivery date range
        if wizard_input_data.get("staging_delivery_fromdate"):
            where_clause.append(
                u"date(tst.staging_delivery_date) >= '{0}'".format(
                    wizard_input_data.get('staging_delivery_fromdate')))

        if wizard_input_data.get("staging_delivery_todate"):
            where_clause.append(
                u"date(tst.staging_delivery_date) <= '{0}'".format(
                    wizard_input_data.get('staging_delivery_todate')))

        # If user specifies ok production date range
        if wizard_input_data.get("ok_production_fromdate"):
            where_clause.append(
                u"date(tst.ok_production_date) >= '{0}'".format(
                    wizard_input_data.get('ok_production_fromdate')))

        if wizard_input_data.get("ok_production_todate"):
            where_clause.append(
                u"date(tst.ok_production_date) <= '{0}'".format(
                    wizard_input_data.get('ok_production_todate')))

        # If user specifies closing date range
        if wizard_input_data.get("closing_fromdate"):
            where_clause.append(
                u"date(tst.closing_datetime) >= '{0}'".format(
                    wizard_input_data.get('closing_fromdate')))

        if wizard_input_data.get("closing_todate"):
            where_clause.append(
                u"date(tst.closing_datetime) <= '{0}'".format(
                    wizard_input_data.get('closing_todate')))

        # Recombine SQL Query with 'Where' clause
        sql_query = sql_query.format(" AND ".join(where_clause))
        # Execute SQL query
        self.cr.execute(sql_query)
        result = self.cr.fetchall()

        # Get list of support tickets
        support_ticket_pool = self.pool.get("tms.support.ticket")
        support_ticket_ids = [data[0] for data in result] or False
        support_tickets = support_ticket_ids and \
            support_ticket_pool.browse(self.cr, self.uid,
                                       support_ticket_ids) or []

        # Pass result to report
        return support_tickets


_column_sizes = [
    ('TICKET ID', 12),
    ('SUMMARY', 12),
    ('PROJECT', 20),
    ('ASSIGNEE', 12),
    ('REPORTER', 12),
    ('TICKET TYPE', 30),
    ('FUNCTIONAL BLOCK', 45),
    ('INVOICEABLE', 30),
    ('OFFERED', 12),
    ('QUOTATION APPROVED', 15),
    ('PRIORITY', 15),
    ('MILESTONE', 15),
    ('ACTIVITY', 15),
    ('STATUS', 15),
    ('RESOLUTION', 15),
    ('DATE', 7),
    ('DESCRIPTION', 7),
    ('LAST COMMENT', 7),
]


class customer_support_ticket_xls(report_xls):
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
            'TICKET ID': {
                'header': [1, 8, 'text', _('TICKET ID')]
            },
            'SUMMARY': {
                'header': [1, 25, 'text', _('SUMMARY')],
            },
            'PROJECT': {
                'header': [1, 13, 'text', _('PROJECT')],
            },
            'ASSIGNEE': {
                'header': [1, 13, 'text', _('ASSIGNEE')],
            },
            'REPORTER': {
                'header': [1, 15, 'text', _('REPORTER')],
            },
            'TICKET TYPE': {
                'header': [1, 15, 'text', _('TICKET TYPE')],
            },
            'FUNCTIONAL BLOCK': {
                'header': [1, 15, 'text', _('FUNCTIONAL BLOCK')],
            },
            'INVOICEABLE WORKLOAD': {
                'header': [1, 15, 'text', _('INVOICEABLE WORKLOAD')],
            },
            'OFFERED': {
                'header': [1, 12, 'text', _('OFFERED')],
            },
            'QUOTATION APPROVED': {
                'header': [1, 15, 'text', _('QUOTATION APPROVED')],
            },
            'PRIORITY': {
                'header': [1, 13, 'text', _('PRIORITY')],
            },
            'MILESTONE': {
                'header': [1, 13, 'text', _('MILESTONE')],
            },
            'ACTIVITY': {
                'header': [1, 13, 'text', _('ACTIVITY')],
            },
            'STATUS': {
                'header': [1, 13, 'text', _('STATUS')],
            },
            'RESOLUTION': {
                'header': [1, 13, 'text', _('RESOLUTION')],
            },
            'DATE': {
                'header': [6, 13, 'text', _('DATE')],
            },
            'DESCRIPTION': {
                'header': [1, 35, 'text', _('DESCRIPTION')],
            },
            'LAST COMMENT': {
                'header': [1, 35, 'text', _('LAST COMMENT')],
            },
        }

        col_specs_sub_template = {
            'OPENING': {
                'header': [1, 12, 'text', _('OPENING')]
            },
            'CLOSING': {
                'header': [1, 12, 'text', _('CLOSING')]
            },
            'INVOICING': {
                'header': [1, 12, 'text', _('INVOICING')]
            },
            'QUOTATION APPROVAL': {
                'header': [1, 14, 'text', _('QUOTATION APPROVAL')]
            },
            'STAGING DELIVERY': {
                'header': [1, 14, 'text', _('STAGING DELIVERY')]
            },
            'OK PRODUCTION': {
                'header': [1, 14, 'text', _('OK PRODUCTION')]
            },
        }

        column_list = [
            'TICKET ID', 'SUMMARY', 'PROJECT', 'ASSIGNEE', 'REPORTER',
            'TICKET TYPE', 'FUNCTIONAL BLOCK', 'INVOICEABLE WORKLOAD',
            'OFFERED', 'QUOTATION APPROVED', 'PRIORITY', 'MILESTONE',
            'ACTIVITY', 'STATUS', 'RESOLUTION', 'DATE',
            'DESCRIPTION', 'LAST COMMENT',
        ]

        column_sub_list = [
            'OPENING', 'CLOSING', 'INVOICING', 'QUOTATION APPROVAL',
            'STAGING DELIVERY', 'OK PRODUCTION'
        ]

        ws.row(row_pos).height_mismatch = True
        ws.row(row_pos).height = 300
        c_specs = map(lambda x: self.render(x, col_specs_template, 'header'),
                      column_list)
        c_sub_specs = map(lambda x: self.render(x, col_specs_sub_template,
                                                'header'),
                          column_sub_list)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_sub_data = self.xls_row_template(c_sub_specs,
                                             [x[0] for x in c_sub_specs])

        for col, size, spec in row_data:
            data = spec[4]
            style = spec[6] and spec[6] or cell_style_center
            if not data:
                # if no data, use default values
                data = report_xls.xls_types_default[spec[3]]
            if size != 1:
                ws.write_merge(row_pos, row_pos,
                               col, col + size - 1, data, style)
                for sub_col, sub_size, sub_spec in row_sub_data:
                    sub_data = sub_spec[4]
                    sub_style = sub_spec[6] and \
                        sub_spec[6] or cell_style_center
                    if sub_size == 1:
                        ws.col(col + sub_col).width = spec[2] * 256
                        ws.row(row_pos + 1).height = 600
                        ws.write_merge(row_pos + 1, row_pos + 1,
                                       col + sub_col, col +
                                       sub_col + sub_size - 1,
                                       sub_data, sub_style)
            else:
                ws.write_merge(row_pos, row_pos + 1, col, col, data, style)
            ws.col(col).width = spec[2] * 256
        row_pos += 2

        cell_format = _xs['borders_all'] + 'align: vert center;' + \
            _xs['wrap'] + 'alignment: wrap on;'
        cell_style = xlwt.easyxf(cell_format + _xs['center'])
        cell_style_left = xlwt.easyxf(cell_format + _xs['left'])
        for st in _p.get_support_tickets():
            ws.row(row_pos).height_mismatch = True
            ws.row(row_pos).height = 3 * 256
            c_specs = [
                ('ticketid', 1, 0, 'number', st.name, None, cell_style),
                ('summary', 1, 0, 'text', st.summary, None, cell_style_left),
                ('project', 1, 0, 'text',
                 st.project_id and st.project_id.name or '', None, cell_style),
                ('assignee', 1, 0, 'text',
                 st.owner_id and st.owner_id.name or '', None, cell_style),
                ('reporter', 1, 0, 'text',
                 st.reporter_id and st.reporter_id.name or '', None,
                 cell_style),
                ('ttype', 1, 0, 'text',
                 _p.get_mapping_ticket_type(st.ticket_type), None, cell_style),
                ('fblock', 1, 0, 'text',
                 st.tms_functional_block_id and
                 st.tms_functional_block_id.name or '', None, cell_style),
                ('invoice', 1, 0, 'text', st.workload_char, None, cell_style),
                ('is_offered', 1, 0, 'text',
                 st.is_offered and 'Yes' or 'No', None, cell_style),
                ('quotation_approved', 1, 0, 'text',
                 st.quotation_approved and 'Yes' or 'No', None, cell_style),
                ('priority', 1, 0, 'text',
                 _p.get_mapping_priority(st.priority), None, cell_style),
                ('milestone', 1, 0, 'text',
                 st.milestone_number or 0, None, cell_style),
                ('activity', 1, 0, 'text',
                 st.tms_activity_id and st.tms_activity_id.name or
                 '', None, cell_style),
                ('status', 1, 0, 'text',
                 _p.get_mapping_ticket_status(st.state), None, cell_style),
                ('resolution', 1, 0, 'text', st.resolution or '', None,
                 cell_style),
                ('opening', 1, 0, 'text',
                 st.create_date, None, cell_style),
                ('closing', 1, 0, 'text',
                 st.closing_datetime, None, cell_style),
                ('invoicing', 1, 0, 'text', st.date, None, cell_style),
                ('quotation', 1, 0, 'text',
                 st.quotation_approved_date, None, cell_style),
                ('staging', 1, 0, 'text',
                 st.staging_delivery_date, None, cell_style),
                ('production', 1, 0, 'text',
                 st.ok_production_date, None, cell_style),
                ('description', 1, 0, 'text',
                 st.description, None, cell_style_left),
                ('lcomment', 1, 0, 'text',
                 _p.get_last_comment(st.tms_support_ticket_comment_ids),
                 None, cell_style_left),
            ]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data,
                                         row_style=cell_style)


customer_support_ticket_xls('report.customer_support_tickets',
                            'tms.support.ticket', parser=Parser)
