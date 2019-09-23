# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields

class print_pit_report_wizard(osv.osv_memory):
    _name = "print.pit.report.wizard"
    _description = "Print PIT Report Wizard"
    
    _columns = {
        'period_id': fields.many2one('account.period', 'Period', required=True), 
    }
    
    def print_pit_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['form'] = self.read(cr, uid, ids)[0]
        
        return {
            'type': 'ir.actions.report.xml', 
            'report_name': 'pit_report', 
            'datas': datas,
            'name': 'PIT Report',
        }

print_pit_report_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
