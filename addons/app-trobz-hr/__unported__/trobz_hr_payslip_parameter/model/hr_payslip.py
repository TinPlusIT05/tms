# -*- encoding: utf-8 -*-
from openerp.osv import osv

class hr_payslip(osv.osv):
    _inherit = 'hr.payslip'
    
    def get_inputs(self, cr, uid, contract_ids, date_from, date_to, context=None):
        """
        Override fnct:
        Get the salary inputs base on the allowance group that set on the contract
        """
        res = super(hr_payslip, self).get_inputs(cr, uid, contract_ids, date_from, date_to, context=context)
        contract_obj = self.pool.get('hr.contract')

        for contract in contract_obj.browse(cr, uid, contract_ids, context=context):
            params = contract.payslip_parameter_group_id and contract.payslip_parameter_group_id.line_ids or []
            for param in params:
                res += [{
                         'name': param.payslip_parameter_id.name,
                         'code': param.payslip_parameter_id.code,
                         'amount': param.value,
                         'contract_id': contract.id,
                        }]
        return res
hr_payslip()