# -*- encoding: utf-8 -*-
from openerp.osv import osv, fields
#from openerp.tools.safe_eval import safe_eval

class hr_contract(osv.osv):
    _inherit = 'hr.contract'
    _columns = {
        'grade_id': fields.many2one('hr.employee.grade', 'Grade'), 
        'payslip_parameter_group_id': fields.many2one('hr.payslip.parameter.group', 'Payslip Paramter Group', readonly=1),   
    }
    
    def onchange_grade(self, cr, uid, ids, grade_id, context=None):
        """
        When select a employee grade:
            - Auto compute the basic salary (specific for Mekong)
            - Auto get the payslip parameter group link to this employee grade
        """
        
        if not grade_id:
            return {}
        value = {}
        warning = {}
        group_obj = self.pool.get('hr.payslip.parameter.group')
        param_group_ids = group_obj.search(cr, uid, [('grade_id','=',grade_id)], context=context)
        
        if param_group_ids:
            basicsal = 0
            for line in group_obj.browse(cr, uid, param_group_ids[0], context=context).line_ids:
                if line.payslip_parameter_id.code == 'BasicSal':
                    basicsal = line.value
           
            if basicsal == 0: 
                warning = {
                    'title': _('Warning!'),
                    'message': _('Cannot find the basic salary in the current payslip parameter group!')
                    }
                
            value = {'wage':basicsal,
                     'basic_wage': basicsal,
                     'payslip_parameter_group_id': param_group_ids[0]}
        
        return {'warning': warning, 'value': value}
    
hr_contract()