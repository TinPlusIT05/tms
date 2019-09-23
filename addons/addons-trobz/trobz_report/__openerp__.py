# -*- coding: utf-8 -*-

{
    'name': 'Trobz Report',
    'version': '1.0',
    'category': 'Trobz Standard Modules',
    'description': """
Extend the Origin Report Engine from OpenERP
--------------------------------------------
* Add the ability to generate xls report. Here is the steps to
    implement a xls report
    *** This feature is deprecated. Please use the report_xls to create xls reports.
    * Create a report with type "Controller" and a specific "name" and "file".
    Note that the last value in the "file" must be the same with the "name"

        <report id="action_example_xls_report"
                model="sale.order"
                string="Example XLS Report"
                report_type="controller"
                name="example_xls_report"
                file="report/xls/example_xls_report"/>

    * Create a report model inherited from "report_xls" and define the function
     "generate_xls_report" to implement specific part of this report. Note that
     the name of this class must have format "report.{report name in xml}"
        openerp.addons.trobz_report.report_xls import report_xls
        class TestReport(osv.TransientModel):
            _name = "report.example_xls_report"

            def generate_xls_report(self, cr, uid, ids,
                report_name, workbook, data=None, context=None):
                """
                """
                if context is None:
                    context = {}
                # initiate the object report_xls so that we can
                # reuse functions/attributes from it
                report_xls_obj = report_xls()

                # get the report based on report name
                report_obj = self.pool['ir.actions.report.xml']
                report_ids = report_obj.search(cr, uid,
                            [('report_name', '=', report_name)])
                if not report_ids:
                    raise
                report_model = report_obj.browse(cr, uid, report_ids[0]).model
                # browse the record which we need to print report
                sale_order_data = self.pool[report_model].browse(cr, uid, ids)

                # create a new sheet
                worksheet = workbook.add_sheet('Sheet 1')
                # delete external id
                i = 1
                for saleorder in sale_order_data:
                    worksheet.write(0, i, saleorder.name)
                    worksheet.col(i).width = 8000 #
                    i += 1
                return True

        * Note: there are some common attributes/functions in the
        class "report_xls" which can be reused in specific reports
        like "xls_types", "xls_headers", "xls_footers", "xls_styles",
        "xls_write_row". Check the file "report_xls.py" for more information

        * Custom report name and ability to compress all report in one zip file

            - in XLS report parser file you can use the following attriibute:

                - "_custom_save_name": if this attribute is set to True, then the
                file name of the report will be changed in the save popup.

                - "_field_for_report_filename": this field you have to set the name
                of the field whose value will be taken to use as a report file name
                to be saved when user print report.

                - "_zip_on_multiple": is this attribute is set to True, then when
                you select multiple records to export at the same time, each report
                XLS is created for each is in docids (selected records' id) then
                compress in one file and send back to client.

            - Two attributes can be mixed in use.

            more example you can check on *arena* project
    """,
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'depends': [
        'report'
    ],
    'data': [
        'data/function_data.xml'
    ],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
