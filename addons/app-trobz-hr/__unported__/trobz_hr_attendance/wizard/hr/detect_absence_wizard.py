# -*- coding: utf-8 -*-
from openerp.osv import osv,fields

class detect_absence_wizard(osv.osv_memory):
    
    _name = 'detect.absence.wizard'
    
    _columns = {
        #TODO : import time required to get currect date
        'date': fields.date('Date'),
    }
    def submit(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        
        # read data on wizard form
        datas = {}
        form = self.read(cr, uid, ids[0], context=context),
        data_form = form[0]
        if data_form:
            datas['form'] = data_form
        return {
            'type': 'ir.actions.report.xml', 
            'report_name': 'detect_absence_report', 
            'datas': datas,
            'name': 'Detect Absence Report'
        }
        
    def print_employees(self, cr, uid, ids, context=None):
        """
        List all employees under contract who have no attendance, 
        nor leave requests for a given date while they should be here according to the working schedule.
        """
        contract_obj = self.pool.get('hr.contract')
        
        contract_ids = contract_obj.search(cr, uid, [], context=context)
        list_employees = [contract for contract in contract_obj.browse(cr, uid, contract_ids, context=context)]
        return list_employees
    
detect_absence_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
