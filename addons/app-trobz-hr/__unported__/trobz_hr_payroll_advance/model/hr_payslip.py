# -*- coding: utf-8 -*-
from openerp.osv import osv, fields
from openerp import tools
import time
from datetime import datetime
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta 

class hr_payslip(osv.osv):
    _inherit = 'hr.payslip'
    
    _columns = {
        'is_advance': fields.boolean('Advance Payslip'),
        'advance_amount': fields.float('Amount', readonly=True, states={'draft': [('readonly', False)]}),
    }

    def _default_date_from(self, cr, uid, context=None):
        if context.get('default_is_advance'):
            return time.strftime('%Y-%m-%d')
        return time.strftime('%Y-%m-01')
    
    def _default_date_to(self, cr, uid, context=None):
        if context.get('default_is_advance'):
            return time.strftime('%Y-%m-%d')
        return str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10]
    
    _defaults = {
        'date_from': _default_date_from,
        'date_to': _default_date_to,
    }
    
    def check_done(self, cr, uid, ids, context=None):
        """
        Check if exist a advance payslip: NOT done the payslips automatically
        """
        if not ids:
            return False
        payslip = self.read(cr, uid, ids[0], ['is_advance'], context=context)
        if payslip['is_advance']:
            return False
        return True
    
    def onchange_employee_id_advance(self, cr, uid, ids, is_advance, date_from, employee_id=False, contract_id=False, context=None):
        """
        Payslip name: Advance slip of Employee_name For Month-Year
        Date to = Date from 
        """
        empolyee_obj = self.pool.get('hr.employee')
        contract_obj = self.pool.get('hr.contract')
        
        if context is None:
            context = {}
        
        #defaults
        res = {'value':{
                      'name':'',
                      'contract_id': False,
                      'struct_id': False,
                      }
            }
        if (not employee_id) or (not date_from):
            return res
        
        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
        employee_id = empolyee_obj.browse(cr, uid, employee_id, fields_process=['name','company_id.id'], context=context)
        res['value'].update({
                    'name': _('Advance Slip of %s for %s') % (employee_id['name'], tools.ustr(ttyme.strftime('%B-%Y'))),
                    'company_id': employee_id.company_id.id
        })

        if not context.get('contract', False):
            #fill with the first contract of the employee
            contract_ids = self.get_contract(cr, uid, employee_id, date_from, date_from, context=context)
        else:
            if contract_id:
                #set the list of contract for which the input have to be filled
                contract_ids = [contract_id]
            else:
                #if we don't give the contract, then the input to fill should be for all current contracts of the employee
                contract_ids = self.get_contract(cr, uid, employee_id, date_from, date_from, context=context)

        if not contract_ids:
            return res
        contract_record = contract_obj.browse(cr, uid, contract_ids[-1], context=context)
        res['value'].update({
                    'contract_id': contract_record and contract_record.id or False
        })
        
        struct_record = contract_record and contract_record.struct_id or False
        if not struct_record:
            return res
        res['value'].update({
                    'date_to': date_from,
                    'struct_id': struct_record.id,
        })
        return res
    
    def process_sheet(self, cr, uid, ids, context=None):
        """
        Override Function
        Add is_advance in context to prevent the updating of the computed_on_payslip_days on holiday lines
        """
        if context is None:
            context = {}
        #for payslip in self.browse(cr, uid, ids, fields_process=['is_advance'], context=context):
        advance_ids_count = self.search(cr, uid, [('id', 'in', ids),
                                                  ('is_advance', '=', True)],
                                        context=context, count=True)
        if advance_ids_count and advance_ids_count != len(ids):
            raise osv.except_osv(_('Warning'),
                                 _('You cannot approve normal payslips and advance payslips at same time! Please approve the advance payslips first.'))
        if advance_ids_count:
            context.update(is_advance=True)
        return super(hr_payslip, self).process_sheet(cr, uid, ids, context=context)

hr_payslip()
