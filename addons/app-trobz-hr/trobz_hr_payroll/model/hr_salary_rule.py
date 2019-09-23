# -*- coding: utf-8 -*-

from openerp.osv import osv, fields

class hr_salary_rule(osv.osv):
    _inherit = 'hr.salary.rule'
    _order = 'sequence'
    _columns = {
        # The ccp salary rule: is_conditional_parameter is true and link to a ccp context
        # Consider that we need to use it or NOT
#         'is_conditional_parameter':fields.boolean('Conditional Parameter'),
#         'ccp_context_id':fields.many2one('conditional.config.parameter.context','Conditional Parameter Context'),
        
        # This field use to the salary rule must be calculated that do not base on a specified valid contract in the payslip period
        'is_unique_on_payslip':fields.boolean('Global Rule'),
    }
    
    def _recursive_search_of_rules_unique(self, cr, uid, rule_ids, context=None):
        """
        Copy Fnct _recursive_search_of_rules_unique, add is_unique_on_payslip in return values
        @param rule_ids: list of browse record
        @return: returns a list of tuple (id, sequence) which are all the children of the passed rule_ids
        """
        children_rules = []
        for rule in rule_ids:
            if rule.child_ids:
                children_rules += self._recursive_search_of_rules_unique(cr, uid, rule.child_ids, context=context)
        return [(r.id, r.sequence, r.is_unique_on_payslip) for r in rule_ids] + children_rules
    
hr_salary_rule()

