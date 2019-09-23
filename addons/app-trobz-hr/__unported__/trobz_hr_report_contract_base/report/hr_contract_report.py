# -*- coding: utf-8 -*-

from openerp.addons.trobz_report_base.report import trobz_report_base
from openerp.addons.report_webkit.webkit_report import WebKitParser
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class Parser(trobz_report_base.Parser):

    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.report_name = 'hr_contract_report'
        self.lang_init(
            self.use_user_lang, self.obj_model, self.obj_id, self.lang_field)
        self.localcontext.update({
            'get_contract': self.get_contract,
            'date_format': self.date_format
        })

    def date_format(self, str_date):
        """
         Convert to date format 'DD/MM/YYY'
        """
        return datetime.strptime(str_date, DF).strftime('%d/%m/%Y')

    def get_documents(self, employee_id):
        """
        Get document of given employee
        """
        doc_obj = self.pool['hr.document']
        cr = self.cr
        uid = self.uid
        doc_ids = doc_obj.search(
            cr, uid, [('emp_id', '=', employee_id)], order='issue_date')
        docs = {}
        for doc in doc_obj.browse(cr, uid, doc_ids):
            doc_type = doc.type_id.name
            if doc_type not in docs:
                docs[doc_type] = False
            docs[doc_type] = doc
        return docs

    def get_contract(self):
        """
        Get information from contract
        @return: list of (contract record, {'document type': document record}
        """
        active_ids = self.context.get('active_ids')
        contract_obj = self.pool['hr.contract']
        contracts = contract_obj.browse(self.cr, self.uid, active_ids)
        res = []
        for contract in contracts:
            docs = self.get_documents(contract.employee_id.id)
            res.append((contract, docs))
        return res

WebKitParser(
    'report.hr_contract_report_webkit',
    'hr.contract',
    'trobz_hr_report_contract_base/report/hr_contract_report.mako',
    parser=Parser
)
