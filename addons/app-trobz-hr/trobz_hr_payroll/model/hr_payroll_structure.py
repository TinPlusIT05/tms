# -*- coding: utf-8 -*-
from openerp.osv import osv, fields

class hr_payroll_structure(osv.osv):
    _inherit = 'hr.payroll.structure'
    
    _columns = {
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the analytic journal without removing it."),
    }
    
    _defaults = {
        'active': True,
    }
    
    def get_all_rules_unique(self, cr, uid, structure_ids, context=None):
        """
        Copy fnt get_all_rules, using _recursive_search_of_rules_unique
         
        @param structure_ids: list of structure
        @return: returns a list of tuple (id, sequence) of rules that are maybe to apply
        """

        all_rules = []
        for struct in self.browse(cr, uid, structure_ids, context=context):
            all_rules += self.pool.get('hr.salary.rule')._recursive_search_of_rules_unique(cr, uid, struct.rule_ids, context=context)
        return all_rules   
    
hr_payroll_structure()

