# -*- encoding: utf-8 -*-
from openerp.osv import osv


class print_contract_list_wizard(osv.osv_memory):
    _name = "print.contract.list.wizard"
    _description = "Wizard print contract list report"

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'contract.list.report',
            'datas': datas,
            'name': 'Contracts Status',
        }

print_contract_list_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
