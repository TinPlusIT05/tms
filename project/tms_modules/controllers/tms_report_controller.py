from openerp.addons.web.http import route
from openerp.addons.report.controllers.main import ReportController
import simplejson
import logging


class tms_report_controller(ReportController):

    @route(['/report/download'], type='http', auth="user")
    def report_download(self, data, token):
        logging.info("report_download")
        requestcontent = simplejson.loads(data)
        url, type = requestcontent[0], requestcontent[1]

        logging.info(url)
        logging.info(type)

        response = ReportController().report_download(data, token)

        if len(url.split('/report/pdf/')) > 1 and type == 'qweb-pdf':
            reportname = url.split('/report/pdf/')[1].split('?')[0]
            reportname = reportname.split('/')
            docids = len(reportname) >= 2 and reportname[1] or '0'
            reportname = reportname[0]
            logging.info(reportname)
            assert docids
            logging.info(docids)
            dict_file_name = self.get_dict_file_name()
            filename = reportname
            if reportname in dict_file_name:
                filename = dict_file_name[reportname]

            response.headers.set(
                'Content-Disposition',
                'attachment; filename=%s.pdf;' % filename)

        return response

    def get_dict_file_name(self):
        return {
            'tms_modules.report_customer_support_activity_template':
                'TMS-ERP Project-Activity Report',
        }
