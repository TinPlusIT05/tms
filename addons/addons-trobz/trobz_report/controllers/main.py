# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today Trobz (<http://www.trobz.com>).
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

from openerp.addons.report.controllers.main import\
    ReportController  # @UnresolvedImport
from openerp.addons.web.http import route, request  # @UnresolvedImport
from datetime import datetime
import xlwt
import simplejson
import tempfile
import os
import shutil
import zipfile
from openerp import http
from openerp.osv import fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)


class XlsReportController(ReportController):

    '''
    #------------------------------------------------------
    # add xls report controller
    #------------------------------------------------------
    '''
    @route(
        ['/report/xls/<reportname>/', '/report/xls/<reportname>/<docids>'],
        type='http', auth="user"
    )
    def export_xls(self, reportname, docids=None, **data):
        """
        Generic function to create xls report
            + Create a generic workbook which will be used in specific report.
            + Prepare the response to the browser
            + Save workbook after generating the specific report
        """
        cr, uid, context = request.cr, request.uid, request.context

        if docids:
            docids = [int(i) for i in docids.split(',')]
        options_data = None
        if data.get('options'):
            options_data = simplejson.loads(data['options'])
        if data.get('context'):
            # Ignore 'lang' here, because the context in data is the one from
            # the webclient *but* if the user explicitely wants to change the
            # lang, this mechanism overwrites it.
            data_context = simplejson.loads(data['context'])
            if data_context.get('lang'):
                del data_context['lang']
            context.update(data_context)

        report_model = 'report.%s' % reportname
        report_obj = request.registry.models[report_model]
        if not report_obj:
            raise ('Error!', 'Could not find the model %s' % report_model)

        # initial report name
        default_report_name = "table"

        # find the model that this report is created for
        report_pool = http.request.env["ir.actions.report.xml"]
        reports = report_pool.search([("report_name", "=", reportname)])

        # browse records for target model
        target_model_pool = http.request.env[reports.model]
        _targets = target_model_pool.browse(docids)

        # if the current report use different name
        # to be saved on client machine
        if hasattr(report_obj, "_custom_save_name"):

            # TODO: default name of the report
            current_time = self.to_timezone(
                datetime.now().strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT
                ), DEFAULT_SERVER_DATETIME_FORMAT
            )

            default_report_name = u"{0}.{1}".format(reportname, current_time)

            # adjust the name of report file returned to client
            # if user choose one record to export, then the name should be
            # in the format "product_name (report_name + datetime)"
            # - if there is no 'name' field on the record
            # it will automatically replace product_name by id of the report
            if docids and len(docids) == 1:

                if _targets.exists():

                    if hasattr(report_obj, "_field_for_report_filename"):
                        default_report_name = u"{0} ({1} - {2})".format(
                            getattr(
                                _targets, getattr(
                                    report_obj, "_field_for_report_filename"
                                )
                            ),
                            reportname, current_time
                        )
                    else:
                        default_report_name = u"{0} ({1} - {2})".format(
                            hasattr(_targets, "name")
                                and _targets.name or _targets.id,
                            reportname, current_time
                        )

        # if the report wants to store everything (sub reports)
        # inside a zip file, then create a zip file contains
        # each xls report inside, then write the contents as stream
        # to the response stream and send back to client
        if hasattr(report_obj, "_zip_on_multiple") and len(docids) > 1:

            # temporary folder to store all the workbook generated
            report_temp_folder = tempfile.mkdtemp()

            # compose zip file path
            zip_path = os.path.join(
                report_temp_folder, u"{0}.zip".format(default_report_name)
            )
            # create custom zip file with compression mode
            zip_file = zipfile.ZipFile(
                zip_path, mode="w", compression=zipfile.ZIP_DEFLATED
            )

            # generate a workbook for each record selected
            for _target in _targets:

                # create new workbook for record and new path
                workbook = xlwt.Workbook()
                workbook_path = os.path.join(
                    report_temp_folder, u"{0}.xls".format(_target.id)
                )

                # generate content for workbook of the current record
                report_obj.generate_xls_report(
                    cr, uid, [_target.id], reportname, workbook,
                    data=options_data, context=context
                )

                # save current workbook (report) to temp folder
                workbook.save(workbook_path)

                # store new workbook as content of current zip file
                if hasattr(report_obj, "_field_for_report_filename"):
                    _target_name = u"{0} ({1} - {2})".format(
                        getattr(
                            _target, getattr(
                                report_obj, "_field_for_report_filename"
                            ),
                            _target.name or _target.id
                        ),
                        reportname, current_time
                    )
                else:
                    _target_name = u"{0} ({1} - {2})".format(
                        hasattr(_target, "name")
                            and _target.name or _target.id,
                        reportname, current_time
                    )

                zip_file.write(
                    workbook_path, arcname="{0}.xls".format(_target_name)
                )

            # after included everything in zip file, close it
            # to let the system handle file system creation
            zip_file.close()

            # make a response back to client with custom header says that
            # we are sending a rar file back instead of xls file
            response = request.make_response(
                None, headers=[
                    (
                        'Content-Type',
                        'application/x-rar-compressed, application/octet-stream'
                    ),
                    (
                        'Content-Disposition',
                        'attachment; filename=%s.zip;' % default_report_name
                    )
                ]
            )

            # read zip file and write it to response stream back to client
            with open(zip_path, "rb") as _zip_file:

                # write to response stream directly
                for pieces in self.read_in_chunks(_zip_file):
                    response.stream.write(pieces)

            # Clean up the temp folder
            try:
                shutil.rmtree(report_temp_folder)
            except:
                _logger.warning(
                    u'Can not remove directory: {0}'.format(report_temp_folder)
                )
            finally:
                return response

        # --------------------------------------------------------------------
        # if the control flow reach this point, this is normal xls report
        # prepare the workbook
        workbook = xlwt.Workbook()

        # each specific report will need to create
        # "generate_xls_report" function
        report_obj.generate_xls_report(
            cr, uid, docids, reportname, workbook,
            data=options_data, context=context
        )

        response = request.make_response(
            None, headers=[
                (
                    'Content-Type',
                    'application/vnd.ms-excel'
                ),
                (
                    'Content-Disposition',
                    'attachment; filename=%s.xls;' % default_report_name
                )
            ]
        )

        workbook.save(response.stream)

        return response

    def read_in_chunks(self, _file, chunk_size=102400):
        """
            Lazy function (generator) to read a file piece by piece.
            Default chunk size: 100kbs.
        """
        while True:
            data = _file.read(chunk_size)
            if not data:
                break
            yield data

    def to_timezone(self, timestring, time_format):

        _env = http.request.env

        _cdatetime = datetime.strptime(timestring, time_format)
        _ctime_zoned = fields.datetime.context_timestamp(
            _env.cr, _env.uid, _cdatetime
        )

        return _ctime_zoned.strftime(time_format)
