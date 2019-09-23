from openerp.osv import fields, osv
from openerp.tools.translate import _

class salary_calculation_wizard(osv.osv_memory):
    _name = 'salary.calculation.wizard'
    _description = 'Detail PIT In Year'
    
    def _get_default_max_salary_social_insurance(self, cr, uid, ids, context=None):
        if context is None:
            context={}
        ir_config_parameter_pool = self.pool['ir.config_parameter']
        max_salary_social_insurance = int(ir_config_parameter_pool.get_param(cr, uid, 'max_salary_social_insurance')) or 0
        return max_salary_social_insurance
    
    _columns = {
        'salary': fields.float('Salary'),
        'is_on_official_salaries': fields.boolean('On Official Salaries'),
        'is_other': fields.boolean('Other'),
        'other_salary': fields.float('VND'),
        'minimum_wage': fields.float('Minimum Wage'),
        'social_per': fields.float('Social'),
        'health_per': fields.float('Health'),
        'unemployment_per': fields.float('Unemployment'),
        'individuals': fields.float('Individuals'),
        'depend': fields.float('Depend'),
        'nb_of_dependents': fields.integer('Nb of dependent(s)'),
        'gross': fields.float('GROSS'),
        'net': fields.float('NET'),
        'social_insurance': fields.float('Social Insurance'),
        'health_insurance': fields.float('Health Insurance'),
        'unemployment_insurance': fields.float('Unemployment Insurance'),
        'income_before_tax': fields.float('Income Before Tax'),
        'reductions_for_individuals': fields.float('Reductions For Individuals'),
        'reductions_for_dependents': fields.float('Reductions For Dependents'),
        'taxable_income': fields.float('Taxable Income'),
        'personal_income_tax': fields.float('Personal Income Tax (*)'),
        'details_pit': fields.text('Detail Of Personal Income Tax'),
        'max_salary_social_insurance': fields.float('Maximum salary social insurance')
    }
    _defaults = {
        'is_on_official_salaries': True,
        'social_per': 8,
        'health_per': 1.5,
        'unemployment_per': 1,
        'individuals': 9000000,
        'depend': 3600000,
        'max_salary_social_insurance': _get_default_max_salary_social_insurance,
        'salary': 80000000
    }
    
    def on_change_is_other(self, cr, uid, ids, is_other, context=None):
        value = {'is_on_official_salaries': True}
        if is_other:
            value.update({'is_on_official_salaries': False})
        return {'value': value}
    
    def on_change_is_on_official_salaries(self, cr, uid, ids, is_on_official_salaries, context=None):
        value = {'is_other': True, 'other_salary': 0}
        if is_on_official_salaries:
            value.update({'is_other': False, 'other_salary': 0})
        return {'value': value}
    
    def gross_2_net(self, cr, uid, ids, context=None):
        """
        Convert gross salary to net salary
        """
        if context is None: 
            context = {}
            
        datas =  self.read(cr, uid, ids, [],context)[0]
        salary = datas['salary']
        social_per = datas['social_per']
        health_per = datas['health_per']
        unemployment_per = datas['unemployment_per']
        nb_of_dependents = datas['nb_of_dependents']
        max_salary_social_insurance = datas['max_salary_social_insurance']
        individuals = datas['individuals']
        depend = datas['depend']
        
        salary_calc = salary
        if datas.get('is_other', False):
            salary_calc = datas['other_salary']
            
        if max_salary_social_insurance <= salary and not datas.get('is_other', False):
            salary_calc = max_salary_social_insurance
        
        social_insurance = salary_calc * social_per /100
        health_insurance = salary_calc * health_per/100
        unemployment_insurance = salary_calc * unemployment_per/100
        
        income_before_tax = salary - social_insurance - health_insurance - unemployment_insurance
        if income_before_tax < 0:
            income_before_tax = 0
        reductions_for_individuals = individuals
        reductions_for_dependents = depend * nb_of_dependents
        
        taxable_income = income_before_tax - reductions_for_dependents - reductions_for_individuals
        if taxable_income < 0:
            taxable_income = 0
        personal_income_tax_datas = self.get_personal_income_tax_datas(cr, uid, taxable_income)
        personal_income_tax = 0
        details_pit = ''
        
        for personal_income_tax_data in personal_income_tax_datas:
            price_x_tax = personal_income_tax_data['price_x_tax']
            price_to_calc = personal_income_tax_data['price_to_calc']
            tax = personal_income_tax_data['tax']
            name = personal_income_tax_data['name']
            personal_income_tax += price_x_tax
            details_pit += '%s Price: %s Tax: %s Total: %s \n'%(name,price_to_calc,tax,price_x_tax) 
            
        net = income_before_tax - personal_income_tax
        
        vals = {
                'gross': salary,
                'social_insurance': social_insurance,
                'health_insurance': health_insurance,
                'unemployment_insurance': unemployment_insurance,
                'income_before_tax': income_before_tax,
                'reductions_for_dependents': reductions_for_dependents,
                'reductions_for_individuals': reductions_for_individuals,
                'taxable_income': taxable_income,
                'personal_income_tax': personal_income_tax,
                'net': net,
                'details_pit':details_pit
                }
        
        self.write(cr, uid, ids, vals, context)
        
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','view_salary_calculation_result_form')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        
        return {
            'name': 'Salary Calculation GROSS TO NET Result',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'salary.calculation.wizard',
            'type': 'ir.actions.act_window',
            'res_id': ids[0],
            'views': [(resource_id, 'form')],
            'target': 'new',
            'context': context
            }

    def net_2_gross(self, cr, uid, ids, context=None):
        """
        Convert gross salary to net salary
        """
        
        if context is None: 
            context = {}
        
        datas =  self.read(cr, uid, ids, [],context)[0]
        net_salary = datas['salary']
        social_per = datas['social_per']
        health_per = datas['health_per']
        unemployment_per = datas['unemployment_per']
        nb_of_dependents = datas['nb_of_dependents']
        max_salary_social_insurance = datas['max_salary_social_insurance']
        individuals = datas['individuals']
        depend = datas['depend']
        
        reductions_for_individuals = individuals
        reductions_for_dependents = depend * nb_of_dependents
        
        income_after_tax = net_salary - reductions_for_dependents - reductions_for_individuals
        if income_after_tax < 0:
            income_after_tax = 0
        taxable_income = self.get_taxable_income(cr, uid, income_after_tax)
        personal_income_tax = 0
        personal_income_tax_datas = self.get_personal_income_tax_datas(cr, uid, taxable_income)
        
        details_pit = ''
        for personal_income_tax_data in personal_income_tax_datas:
            price_x_tax = personal_income_tax_data['price_x_tax']
            price_to_calc = personal_income_tax_data['price_to_calc']
            tax = personal_income_tax_data['tax']
            name = personal_income_tax_data['name']
            personal_income_tax += price_x_tax
            details_pit += '%s Price: %s Tax: %s Total: %s \n'%(name,price_to_calc,tax,price_x_tax) 
        
        income_before_tax = net_salary + personal_income_tax
        
        salary_calc = 0
        if datas.get('is_on_official_salaries', False):
            gross_calc = income_before_tax*100/(100-(social_per + health_per + unemployment_per))
            if max_salary_social_insurance <= gross_calc:
                salary_calc = max_salary_social_insurance
            else:
                salary_calc = gross_calc
                
        if datas.get('is_other', False):
            salary_calc = datas['other_salary']
             
        social_insurance = salary_calc * social_per /100
        health_insurance = salary_calc * health_per/100
        unemployment_insurance = salary_calc * unemployment_per/100
        
        gross = income_before_tax + social_insurance + health_insurance + unemployment_insurance

        vals = {
                'gross': gross,
                'social_insurance': social_insurance,
                'health_insurance': health_insurance,
                'unemployment_insurance': unemployment_insurance,
                'income_before_tax': income_before_tax,
                'reductions_for_dependents': reductions_for_dependents,
                'reductions_for_individuals': reductions_for_individuals,
                'taxable_income': taxable_income,
                'personal_income_tax': personal_income_tax,
                'net': net_salary,
                'details_pit':details_pit
                }
        
        
        self.write(cr, uid, ids, vals, context)
        
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','view_salary_calculation_result_form')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        
        return {
            'name': 'Salary Calculation NET TO GROSS Result',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'salary.calculation.wizard',
            'type': 'ir.actions.act_window',
            'res_id': ids[0],
            'views': [(resource_id, 'form')],
            'target': 'new',
            'context': context
            }

    def get_taxable_income(self, cr, uid,income_after_tax):
        taxable_income = 0
        formula = ''
        if income_after_tax:
            sql_max = \
            """
            select price,income_before_tax
            from pit_details
            where( price = (select max(price) from pit_details))
            order by sequence desc
            """
            cr.execute(sql_max)
            max_prices = cr.fetchall()
            max_price = max_prices and max_prices[0] and max_prices[0][0] or False
            if max_price and income_after_tax > max_price:
                formula = max_prices and max_prices[0] and max_prices[0][1] or False
                    
            else:
                sql_price = \
                """
                select price, income_before_tax
                from pit_details
                where( price = (select min(price) from pit_details  where price >= %s))
                order by sequence asc
                """ %income_after_tax
                cr.execute(sql_price)
                prices = cr.fetchall()
                formula = prices and prices[0] and prices[0][1] or False
            if formula and 'NET' in formula:
                NET = income_after_tax/1000000  # @UnusedVariable
                taxable_income = eval(formula)*1000000
        return round(taxable_income)

    def get_personal_income_tax_datas(self, cr, uid, taxable_income):
        res = []
        
        if taxable_income:
            pit_pool = self.pool.get('pit.details')
            pit_ids = pit_pool.search(cr, uid, [])
            if not pit_ids:
                raise osv.except_osv(_('Error!'), _('You need to configuration PIT on menu Human Resource > Payroll > Details PIT Config'))
            pit_datas = pit_pool.read(cr, uid, pit_ids, [])
            pit_datas = sorted(pit_datas, key=lambda sort_by_sequence: sort_by_sequence['sequence'])
            if pit_datas:
                used_amount = 0
                pre_level = 0
                current_level = pit_datas and pit_datas[0] and pit_datas[0]['price']
                current_index_pit_datas = 0
                for pit in pit_datas:
                    if used_amount <= taxable_income:
                        remaining_amount = taxable_income - used_amount
                        diff_pre_cur = current_level - pre_level
                        val_to_calc = 0
                        if remaining_amount >= diff_pre_cur:
                            val_to_calc = diff_pre_cur
                        else:
                            val_to_calc = remaining_amount
                        
                        if pre_level == current_level:
                            val_to_calc = remaining_amount
                            
                        used_amount += val_to_calc
                        
                        tax = pit['tax']
                        calculated_val = val_to_calc * tax/100
                        if used_amount < 0:
                            calculated_val = 0
                            val_to_calc = 0
                        res.append({'name': pit['name'],
                                    'price_to_calc': val_to_calc,
                                    'tax': tax,
                                    'price_x_tax': calculated_val})
                        
                        pre_level = current_level
                        if current_index_pit_datas < len(pit_datas)-1:
                            current_level = pit_datas[current_index_pit_datas+1]['price']
                            current_index_pit_datas += 1
        return res

salary_calculation_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
