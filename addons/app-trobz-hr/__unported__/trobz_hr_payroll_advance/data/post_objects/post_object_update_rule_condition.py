# -*- encoding: utf-8 -*-

from openerp.osv import osv
import logging

class post_object_update_salary_rule_condition(osv.osv_memory):
    _name = 'post.object.update.salary.rule.condition'
    _auto = False
    _log_access = True
    
    def start(self, cr, uid):
        logging.info('----------START UPDATE SALARY RULE CONDITION ------------')
        self.update_salary_rule_condition(cr, uid)
        logging.info('----------DONE UPDATE SALARY RULE CONDITION------------- ')
        
    def update_salary_rule_condition(self, cr, uid):
        select_sql = """
                    UPDATE hr_salary_rule rule
                    SET condition_select = 'python', 
                    condition_python = 
                        (
                        SELECT
                        CASE
                        WHEN condition_python is not null AND condition_select = 'python'
                        THEN condition_python || ' and not payslip.is_advance' 
                        ELSE 'result = not payslip.is_advance' 
                        END
                        FROM hr_salary_rule
                        WHERE id = rule.id
                        )
                    WHERE  
                    name != 'Advance'
                    and id NOT IN 
                        (
                        SELECT id
                        FROM hr_salary_rule
                        WHERE condition_select = 'python' 
                        AND condition_python LIKE '% not payslip.is_advance%'
                        )                                                                                
        """ 
        cr.execute(select_sql)
        return True    
post_object_update_salary_rule_condition()
