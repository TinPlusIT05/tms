# -*- encoding: utf-8 -*-
import xlwt
from datetime import datetime
from openerp.osv import orm
from openerp.report import report_sxw
from report_xls.report_xls import report_xls
from report_xls.utils import _render
from openerp.tools.translate import translate, _
from openerp import pooler
import logging
_logger = logging.getLogger(__name__)

_ir_translation_name = 'contract.list.report'


class contract_list_report_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(contract_list_report_parser, self).__init__(
            cr, uid, name, context=context
        )
        wanted_list = [
            'department', 'team', 'sub_team', 'employee',
            'job', 'contract_type', 'wage', 'date_start',
            'date_end', 'cost_center'
        ]
        self.context = context
        self.localcontext.update({
            'datetime': datetime,
            'wanted_list': wanted_list,
            'template_changes': {},
            '_': self._,
        })

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        return translate(self.cr, _ir_translation_name, 'report', lang, src)\
            or src


class contract_list_report(report_xls):

    def __init__(
            self, name, table, rml=False,
            parser=False, header=True, store=False):

        super(contract_list_report, self).__init__(
            name, table, rml, parser, header, store
        )
        # Cell Styles
        _xs = self.xls_styles
        # header
        rh_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rh_cell_style_center = xlwt.easyxf(rh_cell_format + _xs['center'])
        # lines
        aml_cell_format = _xs['borders_all']
        self.aml_cell_style = xlwt.easyxf(aml_cell_format)
        self.aml_cell_style_date = xlwt.easyxf(
            aml_cell_format + _xs['left'],
            num_format_str=report_xls.date_format
        )
        self.aml_cell_style_decimal = xlwt.easyxf(
            aml_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format
        )
        # XLS Template
        self.col_specs_template = {
            'department': {
                'header': [
                    1, 15, 'text', _render("_('Department')"), None,
                    self.rh_cell_style_center
                ],
                'lines': [
                    1, 0, 'text', _render("line['department'] or ''"),
                    None, self.aml_cell_style
                ],
            },
            'team': {
                'header': [
                    1, 20, 'text', _render("_('Team')"), None,
                    self.rh_cell_style_center
                ],
                'lines': [
                    1, 0, 'text', _render("line['team'] or ''"),
                    None, self.aml_cell_style
                ],
            },
            'sub_team': {
                'header': [
                    1, 20, 'text', _render("_('Sub-team')"), None,
                    self.rh_cell_style_center
                ],
                'lines': [
                    1, 0, 'text', _render("line['sub_team'] or ''"),
                    None, self.aml_cell_style
                ],
            },
            'employee': {
                'header': [
                    1, 30, 'text',
                    _render("_('Employee Name')"), None,
                    self.rh_cell_style_center
                ],
                'lines': [
                    1, 0, 'text',
                    _render("line['employee'] or ''"), None,
                    self.aml_cell_style
                ],
            },
            'job': {
                'header': [
                    1, 25, 'text',
                    _render("_('Job Position')"),
                    None, self.rh_cell_style_center
                ],
                'lines': [
                    1, 0, 'text',
                    _render("line['job'] or ''"), None,
                    self.aml_cell_style
                ],
            },
            'contract_type': {
                'header': [
                    1, 15, 'text',
                    _render("_('Contract Type')"), None,
                    self.rh_cell_style_center
                ],
                'lines': [
                    1, 0, 'text',
                    _render("line['contract_type'] or ''"), None,
                    self.aml_cell_style
                ],
            },
            'wage': {
                'header': [
                    1, 15, 'text',
                    _render("_('Wage')"), None,
                    self.rh_cell_style_center
                ],
                'lines': [
                    1, 0, 'number',
                    _render("line['wage'] or ''"), None,
                    self.aml_cell_style_decimal
                ],
            },
            'date_start': {
                'header': [
                    1, 15, 'text',
                    _render("_('Start Date')"), None,
                    self.rh_cell_style_center
                ],
                'lines': [
                    1, 0, 'date',
                    _render("datetime.strptime(line['date_start'],'%Y-%m-%d') \
                    or ''"),
                    None, self.aml_cell_style_date
                ],
            },
            'date_end': {
                'header': [
                    1, 15, 'text',
                    _render("_('End Date')"), None,
                    self.rh_cell_style_center
                ],
                'lines': [
                    1, 0, _render("line.get('date_end','') and 'date'\
                        or 'text'"),
                    _render("line.get('date_end','') \
                        and datetime.strptime(line['date_end'],'%Y-%m-%d')"),
                    None, self.aml_cell_style_date
                ],
            },
            'cost_center': {
                'header': [
                    1, 25, 'text',
                    _render("_('Cost Center')"), None,
                    self.rh_cell_style_center
                ],
                'lines': [
                    1, 0, 'text',
                    _render("line['cost_center'] or ''"), None,
                    self.aml_cell_style
                ],
            },
        }

    def generate_xls_report(self, _p, _xs, data, objects, wb):
        wanted_list = _p.wanted_list
        self.col_specs_template.update(_p.template_changes)

        # Add Contract Status excel sheet
        report_name = _("Contract Status ")
        ws = wb.add_sheet(report_name)
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        # Title
        cell_style = xlwt.easyxf(_xs['xls_title']+_xs['center'])
        c_specs = [
            ('report_name', 10, 0, 'text', report_name),
        ]
        row_data = self.xls_row_template(c_specs, ['report_name'])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style
        )
        row_pos += 1

        # Header of columns
        c_specs = map(
            lambda x: self.render(
                x, self.col_specs_template, 'header'
            ),
            wanted_list
        )
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=self.rh_cell_style_center,
            set_column_size=True
        )

        cr = self.cr
        uid = self.uid
        res = self.prepare_data_for_xls(cr, uid)
        for line in res:
            print line  # avoid warning
            c_specs = map(
                lambda x: self.render(x, self.col_specs_template, 'lines'),
                wanted_list
            )
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, row_style=self.aml_cell_style
            )

    def prepare_data_for_xls(self, cr, uid):
        sql = """
        SELECT
            rdept.name as department,
            tdept.name as team,
            stdept.name as sub_team,
            e.name_related as employee,
            j.name as job,
            ct.name as contract_type,
            c.wage,
            c.date_start,
            c.date_end,
            an.name as cost_center
        FROM hr_contract c
            JOIN hr_employee e ON c.employee_id = e.id
            JOIN hr_department rdept ON e.root_department_id = rdept.id
            JOIN hr_department tdept ON e.team_id = tdept.id
            JOIN hr_department stdept ON e.sub_team_id = stdept.id
            JOIN hr_job j ON e.job_id = j.id
            JOIN hr_contract_type ct ON c.type_id = ct.id
            JOIN account_analytic_account an ON c.analytic_account_id = an.id
        WHERE
            c.date_end IS NULL
            OR c.date_end > CURRENT_DATE
        ORDER BY rdept.id, tdept.id, stdept.id, e.name_related
        """
        cr.execute(sql)
        res = cr.dictfetchall()
        return res

contract_list_report(
    'report.contract.list.report',
    'hr.employee',
    parser=contract_list_report_parser
)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
