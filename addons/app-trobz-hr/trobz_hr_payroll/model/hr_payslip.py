# -*- coding: utf-8 -*-

from openerp.osv import osv
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _
import time
from openerp import tools

class hr_payslip(osv.osv):
    _inherit = 'hr.payslip'
    
#     def get_contract(self, cr, uid, employee, date_from, date_to, context=None):
#         """
#         This function has been rewrote because this native function is incorrect 
#         """
#         contract_obj = self.pool.get('hr.contract')
#         contract_ids = contract_obj.get_contract(cr, uid, employee.id, date_from, date_to, context=context)
#         return contract_ids
    
    def get_inputs(self, cr, uid, contract_ids, date_from, date_to, context=None):
        """
        Override function
        The native function is incorrect in case multi-contract
        """
        res = []
        contract_obj = self.pool.get('hr.contract')
        rule_obj = self.pool.get('hr.salary.rule')

        for contract in contract_obj.browse(cr, uid, contract_ids, context=context):
            structure_ids = contract_obj.get_all_structures(cr, uid, [contract.id], context=context)
            rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
            sorted_rule_ids = [x[0] for x in sorted(rule_ids, key=lambda x:x[1])]
            for rule in rule_obj.browse(cr, uid, sorted_rule_ids, context=context):
                if rule.input_ids:
                    for s_input in rule.input_ids:
                        inputs = {
                             'name': s_input.name,
                             'code': s_input.code,
                             'contract_id': contract.id,
                        }
                        res += [inputs]
        return res
    
#     def onchange_employee_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
#         """
#         Override fnct:
#         @return: 
#             name: Salary Slip of <Employee name> for <Month-Year>
#             contract_id: 
#                 Return the latest contract if exist only one contract valid in the indicated period of time on payslip
#                 Return False If exist many contracts valid 
#             struct_id: salary structure of contract
#             input_line_ids: input lines for each contract
#             worked_days_line_ids: Worked days lines for each contract
#             journal_id: Get the journal_id of the first contract
#         """
#         
#         employee_obj = self.pool.get('hr.employee')
#         contract_obj = self.pool.get('hr.contract')
#         worked_days_obj = self.pool.get('hr.payslip.worked_days')
#         input_obj = self.pool.get('hr.payslip.input')
# 
#         if context is None:
#             context = {}
#         #delete old worked days lines
#         old_worked_days_ids = ids and worked_days_obj.search(cr, uid, [('payslip_id', '=', ids[0])], context=context) or False
#         if old_worked_days_ids:
#             worked_days_obj.unlink(cr, uid, old_worked_days_ids, context=context)
# 
#         #delete old input lines
#         old_input_ids = ids and input_obj.search(cr, uid, [('payslip_id', '=', ids[0])], context=context) or False
#         if old_input_ids:
#             input_obj.unlink(cr, uid, old_input_ids, context=context)
#         
#         res = {'value':{
#                       'line_ids':[],
#                       'input_line_ids': [],
#                       'worked_days_line_ids': [],
#                       'name':'',
#                       'contract_id': False,
#                       'struct_id': False,
#                       }
#               }
#         
#         if (not employee_id) or (not date_from) or (not date_to):
#             return res
#         ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
#         employee_id = employee_obj.browse(cr, uid, employee_id, context=context)
#         res['value'].update({
#                     'name': _('Salary Slip of %s for %s') % (employee_id.name, tools.ustr(ttyme.strftime('%B-%Y'))),
#                     'company_id': employee_id.company_id.id
#         })
# 
#         # Get all current contracts
#         contract_ids = self.get_contract(cr, uid, employee_id, date_from, date_to, context=context)
#         if not contract_ids:
#             return res
# 
#         contract_record = contract_obj.browse(cr, uid, contract_ids[0], context=context)
#         # If employee have many contracts in this period, Get journal_id of the first contract
#         res['value'].update({'journal_id': contract_record.journal_id and contract_record.journal_id.id or False})
#         if len(contract_ids)==1:
#             # If employee have only one contract in this period, Return contract_id, struct_id
#             res['value'].update({
#                                  'contract_id': contract_record.id,
#                                  'struct_id': contract_record.struct_id and contract_record.struct_id.id or False,
#                                 })
#         
#         #computation of the salary inputs
#         worked_days_line_ids = self.get_worked_day_lines(cr, uid, contract_ids, date_from, date_to, context=context)
#         input_line_ids = self.get_inputs(cr, uid, contract_ids, date_from, date_to, context=context)
#         res['value'].update({
#                              'worked_days_line_ids': worked_days_line_ids,
#                              'input_line_ids': input_line_ids,
#                             })
#         return res
    
    def onchange_employee_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
        # TODO: this is temporary fix for this error
        # (add date_from, date_to, employee in res)
        # ValueError: "name 'date_from' is not defined" while evaluating
        # '[date_from, date_to, employee, contract_id]'
        res = super(hr_payslip, self).onchange_employee_id(cr, uid, ids, date_from, date_to, employee_id, contract_id, context)
        employee = self.pool['hr.employee'].browse(cr, uid, employee_id, context=context)
        contract_ids = self.get_contract(cr, uid, employee, date_from, date_to, context=context)
        worked_days_line_ids = self.get_worked_day_lines(cr, uid, contract_ids, date_from, date_to, context=context)
        input_line_ids = self.get_inputs(cr, uid, contract_ids, date_from, date_to, context=context)
        res['value'].update({
                    'date_from': date_from,
                    'date_to': date_to,
                    'employee_id': employee_id,
                    'worked_days_line_ids': worked_days_line_ids,
                    'input_line_ids': input_line_ids,
        })
        if ids:
            payslip_obj = self.browse(cr, uid, ids[0], context=context)
            res['value'].update({
                'state': payslip_obj.state,
                'journal_id': payslip_obj.journal_id and payslip_obj.journal_id.id or False,
                'number': payslip_obj.number,
            })
        return res
    
    def line_data(self, cr, uid, rule, contract):
        """
        Prepare datas for a payslip line to create a new one 
        """
        res = {
            'slip_id':False, 
#             'is_conditional_parameter': False,
#             'ccp_param_type_id': False,
            'name': rule.name,
            'code': rule.code,
            'sequence': rule.sequence,
            'category_id': rule.category_id.id,
            'salary_rule_id': rule.id,
            'contract_id': contract.id,
            'appears_on_payslip': rule.appears_on_payslip,
            'condition_select': rule.condition_select,
            'condition_python': rule.condition_python,
            'condition_range': rule.condition_range,
            'condition_range_min': rule.condition_range_min,
            'condition_range_max': rule.condition_range_max,
            'amount_select': rule.amount_select,
            'amount_fix': rule.amount_fix,
            'amount_python_compute': rule.amount_python_compute,
            'amount_percentage': rule.amount_percentage,
            'amount_percentage_base': rule.amount_percentage_base,
            'register_id': rule.register_id.id,
            'amount': 0,
            'employee_id': contract.employee_id.id,
            'quantity': 1,
            'rate': 100,
        }
        return res

    def sumdict(self, listdicts):
        if not listdicts:
            return {}
        """
        @return: A new dictionary has the values that sum of values by the same key of a list dictionaries
        Just good for dicts have the same format that means:
        listdict = [{'a':1, 'b':2, 'c': 10}, {'b':10, 'a':20, 'd': 100}] 
        --> result = {'a':21, 'b':12, 'c': 10}, Not appear 'd' in result  
        """
        res = listdicts[0]
        for i in range(1,len(listdicts)):
            res = dict((key, value + res.get(key,0)) for key, value in listdicts[i].iteritems())
        return res
    
    def create_payslip_lines(self, cr, uid, contract_ids, payslip_id, context=None):
        """  
        Override fnct:
        For payslip have many contracts valid on the payslip perid of time 
        Create payslip lines for each contract base on: 
            List of rules are unique on payslip
        Calculate a salary formula base on:
            globaldict: using compute the rules that unique on payslip
                contract_qty
                remaining_leaves
                payslip
                employee
                Sum of rules of all contracts
            localdict: specified for contract
                payslip
                employee
                contract
                inputs
                workdays
                rules
        """
        
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, pool, cr, uid, employee_id, input_dict):
                self.pool = pool
                self.cr = cr
                self.uid = uid
                self.employee_id = employee_id
                self.dict = input_dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                self.cr.execute("SELECT sum(amount) as sum\
                            FROM hr_payslip as hp, hr_payslip_input as pi \
                            WHERE hp.employee_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                           (self.employee_id, from_date, to_date, code))
                res = self.cr.fetchone()[0]
                return res or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                self.cr.execute("SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours\
                            FROM hr_payslip as hp, hr_payslip_worked_days as pi \
                            WHERE hp.employee_id = %s AND hp.state = 'done'\
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                           (self.employee_id, from_date, to_date, code))
                return self.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def sum(self, code, from_date, to_date=None, official_contract=None):
                """
                The offical_contract = Fasle means sum of amount of payslip line of all contract
                The offical_contract = True means sum of amount of payslip line of official contract
                """
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                sql = """SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)\
                            FROM hr_payslip as hp, hr_payslip_line as pl
                            WHERE hp.employee_id = %s AND hp.state = 'done' 
                            AND hp.date_from >= '%s' AND hp.date_to <= '%s'
                            AND hp.id = pl.slip_id AND pl.code = '%s'"""%(self.employee_id, from_date, to_date, code)
                if official_contract:
                    sql += """AND pl.id IN (SELECT pl.id 
                                            FROM hr_payslip_line pl, hr_contract c
                                            WHERE pl.contract_id = c.id
                                            AND c.is_trial = False)"""
                self.cr.execute(sql)
                res = self.cr.fetchone()
                return res and res[0] or 0.0

        #We keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules = {}
        categories_dict = {}
        blacklist = []
        payslip_obj = self.pool.get('hr.payslip')
        structure_obj = self.pool.get('hr.payroll.structure')
        payslip_line_obj = self.pool.get('hr.payslip.line')
        obj_rule = self.pool.get('hr.salary.rule')
        sequence_obj = self.pool.get('ir.sequence')
        hol_obj = self.pool.get('hr.holidays')
        hol_status_obj = self.pool.get('hr.holidays.status')
        
        #Calculate globaldict
        payslip = payslip_obj.browse(cr, uid, payslip_id, context=context)
        employee = payslip.employee_id
        payslip_obj = Payslips(self.pool, cr, uid, employee.id, payslip) 
        
        # Ticket #7225: Calculate remaining leaves = Total allocation request - Total leave days (with leave type casual leave)
        param_obj = self.pool.get('ir.config_parameter')
        param = param_obj.get_param(cr, uid, 'default_remaining_leave_type') or None
        hol_status_ids = hol_status_obj.search(cr, uid, [('name', 'in', eval(param))], context=context)
        allo_days = hol_obj.compute_allo_days(cr, uid, employee.id, hol_status_ids, context=context)
        leave_days = hol_obj.compute_leave_days(cr, uid, employee.id, hol_status_ids, context=context)
        remaining_leaves=allo_days-leave_days
        
        globaldict = {'employee': employee,
                      'payslip': payslip_obj,
                      'remaining_leaves': remaining_leaves, 
                      }
       
#        print 'START AT RULES FOR EACH CONTRACT ----------------------'
        
        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            """
            For each contract
                - Compute localdict
                - Get all structure
                - Get all rules fo structure
                    + CCP Rules
                    + Normal Rules
                ** Compute <globaldict> is sum of value of all localdicts
            """
            # Reset backlist 
            blacklist = []
            # Salary inputs specify for each contract
            worked_days = {}
            for worked_days_line in payslip.worked_days_line_ids:
                if contract.id == worked_days_line.contract_id.id:
                    worked_days[worked_days_line.code] = worked_days_line
            
            inputs = {}
            for input_line in payslip.input_line_ids:
                if contract.id == input_line.contract_id.id:
                    inputs[input_line.code] = input_line

            input_obj = InputLine(self.pool, cr, uid, payslip.employee_id.id, inputs)
            worked_days_obj = WorkedDays(self.pool, cr, uid, payslip.employee_id.id, worked_days)
            rules_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, rules)
            categories_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, {})
            localdict = {
                         'contract_qty': len(contract_ids),
                         'payslip': payslip_obj,
                         'employee': employee, 
                         'contract': contract,
                         'categories': categories_obj,
                         'rules': rules_obj, 
                         'payslip': payslip_obj, 
                         'worked_days': worked_days_obj, 
                         'inputs': input_obj
                         }
            
            #get the ids of the structures on the contracts and their parent id as well
            structure_ids = self.pool.get('hr.contract').get_all_structures(cr, uid, [contract.id], context=context)
            
            #get the rules of the structure and thier children
            rule_ids = structure_obj.get_all_rules_unique(cr, uid, structure_ids, context=context)
            
            #run the rules by sequence
            sorted_rule_ids = [rule[0] for rule in sorted(rule_ids, key=lambda x:x[1]) if not rule[2]]
            
            for rule in obj_rule.browse(cr, uid, sorted_rule_ids, context=context):
                line_data = self.line_data(cr, uid, rule, contract)
                """
                For the normal rules
                Use the original OpenERP source code 
                """
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                #check if the rule can be applied
                if obj_rule.satisfy_condition(cr, uid, rule.id, localdict, context=context) and rule.id not in blacklist:
#                        print 'RULE satisfy_condition',rule.name 
                    #compute the amount of the rule
                    amount, qty, rate = obj_rule.compute_rule(cr, uid, rule.id, localdict, context=context)
                    
                    """Compute rule that using localdict """
                    #check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    #set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules[rule.code] = rule
                    #sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    #create/overwrite the rule in the temporary results
                    line_data.update({
                        'amount': amount,
                        'quantity': qty,
                        'rate': rate,
                        })
                    result_dict[key] = line_data
                    
                    """Compute globaldict: sum of amount of rule that has the same code """
                    globaldict[rule.code] = globaldict.get(rule.code, 0) + tot_rule      
                else:
                    #blacklist this rule and its children
                    blacklist += [obj[0] for obj in self.pool.get('hr.salary.rule')._recursive_search_of_rules(cr, uid, [rule], context=context)]
            
            # Write localdict['categories'].dict of all contracts
            categories_dict[contract.id] = localdict['categories'].dict
            
        #Compute globaldict['categories']
        globaldict.update({'categories': BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, self.sumdict(categories_dict.values()))})
        
#        print '------------START COMPUTE UNIQUE RULE---------------'
        #get the ids of the structures on the contracts and their parent id as well
        structure_ids = self.pool.get('hr.contract').get_all_structures(cr, uid, contract_ids, context=context)
        
        #get the rules of the structure and thier children
        rule_ids = structure_obj.get_all_rules_unique(cr, uid, structure_ids, context=context)
        
        #get rules unique on payslip, run the rules by sequence
        sorted_unique_rule_ids = [rule[0] for rule in sorted(rule_ids, key=lambda x:x[1]) if rule[2]]
                    
        for rule in obj_rule.browse(cr, uid, sorted_unique_rule_ids, context=context):
            """
            Using <globaldict> instead of <localdict>
            Compute:
                - CCP Rules
                - Normal Rules 
            """
            line_data = self.line_data(cr, uid, rule, contract)
            """
            For the normal rules
            Use the orginal OpenERP source code 
            """
            key = rule.code + '-' + str(contract.id)
            globaldict['result'] = None
            globaldict['result_qty'] = 1.0
            #check if the rule can be applied
            if obj_rule.satisfy_condition(cr, uid, rule.id, globaldict, context=context) and rule.id not in blacklist:
                #compute the amount of the rule
                amount, qty, rate = obj_rule.compute_rule(cr, uid, rule.id, globaldict, context=context)
                
                """Compute rules that using globaldict """
                #check if there is already a rule computed with that code
                previous_amount = rule.code in globaldict and globaldict[rule.code] or 0.0
                #set/overwrite the amount computed for this rule in the globaldict
                tot_rule = amount * qty * rate / 100.0
                globaldict[rule.code] = tot_rule
                rules[rule.code] = rule
                #sum the amount for its salary category
                globaldict = _sum_salary_rule_category(globaldict, rule.category_id, tot_rule - previous_amount)
                #create/overwrite the rule in the temporary results
                line_data.update({
                    'amount': amount,
                    'quantity': qty,
                    'rate': rate,
                    })
                result_dict[key] = line_data
            else:
                #blacklist this rule and its children
                blacklist += [obj[0] for obj in self.pool.get('hr.salary.rule')._recursive_search_of_rules(cr, uid, [rule], context=context)]

        number = payslip.number or sequence_obj.get(cr, uid, 'salary.slip')
        lines = [(0,0,line) for line in result_dict.values()]
        self.write(cr, uid, [payslip_id], {'line_ids': lines, 'number': number,}, context=context)
        return True
        
    def compute_sheet(self, cr, uid, ids, context=None):
        """
        Override Function:
        - Add constraint to check the contract and working schedule before compute payslip
        - The payslip lines have been created by using fnct create_payslip_lines 
        instead of using OpenERP function get_payslip_lines 
        """
        slip_line_pool = self.pool.get('hr.payslip.line')
        for payslip in self.browse(cr, uid, ids, context=context):
            if payslip.contract_id:
                #Set the list of contract for which the rules have to be applied
                contract_ids = [payslip.contract_id.id]
            else:
                #If we don't give the contract, then the rules to apply should be for all current contracts of the employee
                contract_ids = self.get_contract(cr, uid, payslip.employee_id, payslip.date_from, payslip.date_to, context=context)
            
            #Check exist working schedule 
            if payslip.contract_id and not payslip.contract_id.working_hours:
                #Exists a contract in this period
                raise osv.except_osv(_('Warning !'), 
                                     _("Please input the working schedule for contract (%s) before computing this payslip."%(payslip.contract_id.name)))
            elif len(contract_ids)>=2:
                #Exists many contracts in this period 
                check_schedule = False
                contract_name = ''
                for con in self.pool.get('hr.contract').read(cr, uid, contract_ids, ['working_hours', 'name'], context=context):
                    contract_name += con['name'] +', '
                    if con['working_hours']:
                        check_schedule = True
                if not check_schedule:
                    raise osv.except_osv(_('Warning !'), 
                                         _("Please input the working schedule for one of contracts (%s) before computing this payslip."%(contract_name.rstrip(', '))))
            elif not contract_ids:
                #Employee have no contract in this period
                raise osv.except_osv(_('Warning !'), 
                                     _("Please define contract of employee (%s) before computing payslip."%(payslip.employee_id.name)))
            
            #Delete old payslip lines
            old_slipline_ids = slip_line_pool.search(cr, uid, [('slip_id', '=', payslip.id)], context=context)
            if old_slipline_ids:
                slip_line_pool.unlink(cr, uid, old_slipline_ids, context=context)
            
            #Create new payslip lines 
            self.pool.get('hr.payslip').create_payslip_lines(cr, uid, contract_ids, payslip.id, context=context)
        return True
    
    def compute_unpaid_leaves(self, cr, uid, employee_id, date_from, date_to, context=None):
        """
        The remaining unpaid leaves = leaves in the indicated period of time - computed leave days on leave request lines
        Date from=False for the first contract
        Date from for the next contract 
        """
        
        hol_status_ids = self.pool.get('hr.holidays.status').search(cr, uid, [('payment_type','=','unpaid')], context=context)
        if not hol_status_ids:
            return 0
        
        condition = """
            FROM
                hr_holidays h
                join hr_holidays_line hl on (h.id=hl.holiday_id)
            WHERE
                h.type='remove' AND
                h.state='validate' AND
                h.employee_id = %s AND 
                (hl.computed_on_payslip_days IS NULL
                OR hl.computed_on_payslip_days < hl.number_of_days) AND
                hl.holiday_status_id in (%s)"""%(employee_id, ','.join(map(str, hol_status_ids))) 
        
        sql = """SELECT SUM(hl.number_of_days - 
                                CASE WHEN hl.computed_on_payslip_days IS NOT NULL
                                THEN hl.computed_on_payslip_days
                                ELSE 0
                                END)""" + condition
        other_sql = """SELECT hl.first_date, hl.last_date, hl.first_date_type, hl.last_date_type, 
                        CASE WHEN hl.computed_on_payslip_days IS NOT NULl 
                        THEN hl.computed_on_payslip_days
                        ELSE 0
                        END """ + condition
        
        if date_from and date_to:
            # first date > date from and last date < date to
            sql += "AND hl.last_date < '%s' AND hl.first_date > '%s'"%(date_to, date_from)
            cr.execute(sql)
            res = cr.fetchone()
            # first date <= date from and last date >= date from
            # OR first date <= date to and last date >= date to 
            other_sql += """AND (( hl.first_date <= '%s' AND hl.last_date >= '%s')
                            OR (hl.first_date <= '%s' AND hl.last_date >= '%s'))""" %(date_from, date_from, date_to, date_to)
            cr.execute(other_sql)
            other_res = cr.fetchall()
        else:
            # NOT date from and last date < date to
            sql += "AND hl.last_date < '%s'"%(date_to)
            cr.execute(sql)
            res = cr.fetchone()
            
            # OR first date <= date to and last date >= date to 
            other_sql += "AND (hl.first_date <= '%s' AND hl.last_date >= '%s')" %(date_to, date_to)
            cr.execute(other_sql)
            other_res = cr.fetchall()
            
        number_of_days = res and res[0] or 0
            
        employee = self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context)
        country_id = employee.company_id and employee.company_id.country_id and employee.company_id.country_id.id or False
        for line in other_res:
            start_date = datetime.strptime(date_from and max(date_from, line[0]) or line[0], '%Y-%m-%d').date()
            end_date = datetime.strptime(date_to and min(line[1], date_to) or line[1], '%Y-%m-%d').date()
            has_working_hours = False
            contract_obj = self.pool.get('hr.contract')
            contract_ids = contract_obj.get_contract(cr, uid, employee.id, start_date, end_date, context=context)
            if contract_ids:
                contract = contract_obj.browse(cr, uid, contract_ids[-1], context=context)
                has_working_hours = contract.working_hours and contract.working_hours.id or False
            line_days = 0
            while start_date <= end_date:
                dayofweek = start_date.weekday()
                date_type = 'full'
                if start_date == datetime.strptime(line[0], '%Y-%m-%d').date():
                    date_type = line[2]
                if start_date == datetime.strptime(line[1], '%Y-%m-%d').date():
                    date_type = line[3]
                line_days += self.pool.get('hr.holidays.line').plus_day(cr, uid, has_working_hours, start_date, dayofweek, date_type, country_id, context=context)
                start_date = start_date + timedelta(1)
            number_of_days += max(line_days - line[4], 0)
        return number_of_days
    
    def update_computed_leaves(self, cr, uid, employee_id, date_to, context=None):
        """
        When payslip is approved,
        Update computed_on_payslip_days of the leave lines
        """
        if context is None:
            context = {}
        
        # last date < date to
        sql = """
            UPDATE hr_holidays_line 
            SET computed_on_payslip_days = number_of_days
            WHERE 
            id IN (SELECT hl.id 
                    FROM
                    hr_holidays h
                    join hr_holidays_line hl on (h.id=hl.holiday_id)
                    WHERE
                    h.type='remove' AND
                    h.state='validate' AND
                    h.employee_id = %s AND 
                    (hl.computed_on_payslip_days IS NULL OR 
                    hl.computed_on_payslip_days < hl.number_of_days) AND 
                    hl.last_date < '%s'
               )"""%(employee_id, date_to) 
        cr.execute(sql)
        
        line_obj = self.pool.get('hr.holidays.line')
       
        # first date <= date to and last date >= date to 
        other_sql = """
            SELECT hl.first_date, hl.last_date, hl.first_date_type, hl.last_date_type, hl.id
            FROM
            hr_holidays h
            join hr_holidays_line hl on (h.id=hl.holiday_id)
            WHERE
            h.type='remove' AND
            h.state='validate' AND
            h.employee_id = %s AND 
            (hl.computed_on_payslip_days IS NULL 
            OR hl.computed_on_payslip_days < hl.number_of_days) AND
            (hl.first_date <= '%s' AND hl.last_date >= '%s')  
        """%(employee_id, date_to, date_to)
        cr.execute(other_sql)
        other_res = cr.fetchall()
        
        employee = self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context)
        country_id = employee.company_id and employee.company_id.country_id and employee.company_id.country_id.id or False
        
        for line in other_res:
            start_date = datetime.strptime(line[0], '%Y-%m-%d').date()
            end_date = datetime.strptime(date_to and min(line[1], date_to) or line[1], '%Y-%m-%d').date()
            has_working_hours = False
            contract_obj = self.pool.get('hr.contract')
            contract_ids = contract_obj.get_contract(cr, uid, employee.id, start_date, end_date, context=context)
            if contract_ids:
                contract = contract_obj.browse(cr, uid, contract_ids[0], context=context)
                has_working_hours = contract.working_hours and contract.working_hours.id or False
                
            computed_on_payslip_days = 0
            while start_date <= end_date:
                dayofweek = start_date.weekday()
                date_type = 'full'
                if start_date == datetime.strptime(line[0], '%Y-%m-%d').date():
                    date_type = line[2]
                if start_date == datetime.strptime(line[1], '%Y-%m-%d').date():
                    date_type = line[3]
                computed_on_payslip_days += line_obj.plus_day(cr, uid, has_working_hours, start_date, dayofweek, date_type, country_id, context=context)
                start_date = start_date + timedelta(1)
            line_obj.write(cr, uid, [line[4]], {'computed_on_payslip_days': computed_on_payslip_days})
        return True
    
    
    def get_worked_day_lines(self, cr, uid, contract_ids, date_from, date_to, context=None):
        """ 
        Ticket #1411, #1414(Remove public holidays), #4655
        Override function
        @param contract_ids: list of contract id
        @return: 
        - Working Days in Month (base on the working calendar)
        - Worked days in the indicated period of time 
        - Unpaid leaves
        returns a list of dictionary which containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        order_of_contract = 1 
        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            if not contract.working_hours:
                #fill only if the contract as a working schedule linked
                continue
        
            calendar = {
                 'name': _("Working Days in Month"),
                 'sequence': 0,
                 'code': 'ScheduleDays',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            attendances = {
                 'name': "",
                 'code': 'WorkedDays',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            leaves = {
                  'name': 'Unpaid Leaves',
                  'sequence': 2,
                  'code': 'UnpaidL',
                  'number_of_days': 0,
                  'number_of_hours': 0,
                  'contract_id': contract.id,
            }
            
            contract_date_start = contract.date_start
            contract_date_end = contract.date_end
            
            day_from = datetime.strptime(max(contract_date_start,date_from),"%Y-%m-%d")
            day_to = datetime.strptime(date_to,"%Y-%m-%d")
            if contract_date_end and contract_date_end <= date_to:
                day_to =  datetime.strptime(contract_date_end,"%Y-%m-%d")
            
            date_start_month = day_from + relativedelta(day=1)
            date_end_month = day_to + relativedelta(months=1, day=1, days=-1)
             
            nb_of_days_in_month = (date_end_month - date_start_month).days + 1
            nb_of_days = (day_to - day_from).days + 1
            
            # Working days in month is sum of working schedule lines (1 line = 0.5 day)
            for day in range(0, nb_of_days_in_month):
                working_hours_on_day = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract.working_hours, date_start_month + relativedelta(days=day), context)
                if working_hours_on_day:   
                    schedule_day = self.pool.get('resource.calendar.attendance').type_working_calendar(cr, uid, contract.working_hours, date_start_month + relativedelta(days=day), context) 
                    calendar['number_of_days'] += schedule_day
                    calendar['number_of_hours'] += working_hours_on_day
                    
            # Worked days from day_from to day_to is sum of working schedule lines (1 line = 0.5 day)
            for day in range(0, nb_of_days):
                working_hours_on_day = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract.working_hours, day_from + relativedelta(days=day), context)
                if working_hours_on_day:   
                    schedule_day = self.pool.get('resource.calendar.attendance').type_working_calendar(cr, uid, contract.working_hours, day_from + relativedelta(days=day), context) 
                    attendances['number_of_days'] += schedule_day
                    attendances['number_of_hours'] += working_hours_on_day
            attendances.update({'name':_("Worked Days from %s to %s"%(day_from.strftime('%d/%m/%Y'), day_to.strftime('%d/%m/%Y')))}),
                    
            # Unpaid leaves
            # If there are 2 contracts, unpaid leave of 
            #    The 1st contract will be computed until the contract date end 
            #    The 2nd contract will be computed from contract date start to payslip date end
            valid_date_from = order_of_contract > 1 and day_from.strftime('%Y-%m-%d') or False
            ldays = self.compute_unpaid_leaves(cr, uid, contract.employee_id.id, valid_date_from, day_to.strftime('%Y-%m-%d'), context=context)                
            leaves['number_of_days'] = ldays 
            leaves['number_of_hours'] += ldays * 8
            res += [attendances, calendar, leaves]
            order_of_contract +=1
            
        return res

    def process_sheet(self, cr, uid, ids, context=None):
        """
        Override fnct 
        Update the leave days have been computed on the payslip
        """
        if context is None:
            context = {}
        
        if not context.get('is_advance', False):
            for payslip in self.browse(cr, uid, ids, context=context):
                self.update_computed_leaves(cr, uid, payslip.employee_id.id, payslip.date_to, context=context)                
        return super(hr_payslip, self).process_sheet(cr, uid, ids, context=context)
    
hr_payslip()
