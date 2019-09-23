import xlsxwriter

from trobz.log import logger


class ReportWriter:

    def _set_styles(self):
        self.styleHeader = self.wb.add_format({'bold': True,
                                               'text_wrap': True,
                                               'valign': 'vjustify'})
        self.styleNumber = self.wb.add_format({'num_format': '#,##0'})

        self.styleNumberHigh = self.wb.add_format(
            {'num_format': '#,##0', 'font_color': 'red'})
        self.styleNumberLow = self.wb.add_format(
            {'num_format': '#,##0', 'font_color': 'blue'})

        self.stylePercentage = self.wb.add_format({
            'num_format': '0%'})

        self.styleBoldPercentage = self.wb.add_format({
            'bold': True, 'num_format': '0%'})

        self.styleDate = self.wb.add_format({'num_format': 'yyyy-mm-dd'})
        self.styleDateOld = self.wb.add_format(
            {'num_format': 'yyyy-mm-dd', 'font_color': 'red'})

        self.styleText = self.wb.add_format({})

        self.styleTitle = self.wb.add_format({'bold': True,
                                              'font_color': 'green',
                                              'font_size': '14px'})

    def __init__(self, wb_file_name):
        self.wb = xlsxwriter.Workbook(wb_file_name)
        self.log = logger('ReportWriter')
        self._set_styles()

    def close(self):
        self.wb.close()


class WorkSheetWriter:

    def __init__(self, report_writer, sheetname, column_widths=[]):
        self.report = report_writer
        self.log = self.report.log
        self.ws = report_writer.wb.add_worksheet(sheetname)
        self.last_row = 0

        self.ws.freeze_panes(2, 2)

        if column_widths:
            c = 0
            for cw in column_widths:
                self.ws.set_column(c, c, cw)  # Sets the width of the column
                c += 1

    def write(self, title, header, rows, first_col=0, first_row=-1):

        if first_row == -1:
            first_row = self.last_row + 2

        ws = self.ws

        r = first_row

        if title:
            ws.write(r, first_col, title, self.report.styleTitle)
            ws.set_row(r, 35)
            r += 1

        c = first_col
        ws.set_row(r, 30)
        for h in header:
            ws.write(r, c, h, self.report.styleHeader)
            c += 1
        r += 1

        for row in rows:
            c = first_col
            for e in row:
                try:
                    ws.write(r, c, e[0], e[1])
                except Exception as x:
                    self.log.error('row[0][0]: %s', row[0][0])
                    self.log.error('Label: %s', e[0])
                    self.log.error('Style: %s', e[1])
                    raise x

                c += 1
            r += 1

        self.last_row = r
