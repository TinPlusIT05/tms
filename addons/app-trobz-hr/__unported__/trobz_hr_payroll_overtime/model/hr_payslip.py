# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp import netsvc

class hr_payslip(osv.osv):
    _inherit = 'hr.payslip'
    
    
    def compute_overtime(self, cr, uid, ids, context=None):
        """
        This function:
        -    Done all confirm overtime of employee in the period
        -    Cancel all draft overtime of employee in the period 
        """
        overtime_obj = self.pool.get('hr.overtime')
        wf_service = netsvc.LocalService("workflow")
        for payslip in self.browse(cr, uid, ids, context):
            # cancel draft overtime
            overtime_cancel_ids = overtime_obj.search(cr, uid, [
                                          ('mode', '=', 'by_employee'),
                                          ('employee_id', '=', payslip.employee_id.id),
                                          ('name', '>=', payslip.date_from),
                                          ('name', '<=', payslip.date_to),
                                          ('state', '=', 'draft')
                                          ])
            if overtime_cancel_ids:
                overtime_obj.write(cr, uid, overtime_cancel_ids, {'state': 'cancel'}, context=context)
            # done confirmed overtime 
            overtime_ids = overtime_obj.search(cr, uid, [
                                          ('mode', '=', 'by_employee'),
                                          ('employee_id', '=', payslip.employee_id.id),
                                          ('name', '>=', payslip.date_from),
                                          ('name', '<=', payslip.date_to),
                                          ('state', '=', 'confirmed')
                                          ])
            
            for overtime_id in overtime_ids:
                wf_service.trg_validate(uid, 'hr.overtime', overtime_id, 'button_done', cr)
            return True
        
    def hr_verify_sheet(self, cr, uid, ids, context=None):
        """
        Override Fnct 
        """
        self.compute_sheet(cr, uid, ids, context)
        self.compute_overtime(cr, uid, ids, context)
        return self.write(cr, uid, ids, {'state': 'verify'}, context=context)
    
