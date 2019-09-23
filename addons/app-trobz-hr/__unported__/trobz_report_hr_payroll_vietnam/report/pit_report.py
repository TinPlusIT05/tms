from trobz_report_base.report import trobz_report_base
from datetime import datetime
import calendar

class Parser(trobz_report_base.Parser):
    
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.report_name = 'pit_report'
        self.no = 0
        self.localcontext.update({
            'get_period': self.get_period,
            'get_period_name': self.get_period_name,
            'format_date': self.format_date,
            'next_no': self.next_no,
            'get_all_payslips': self.get_all_payslips,
        })
    
    def get_wizard_data(self):
        """
        get data from wizard
        """
        res = {}
        datas = self.localcontext['data']
        if datas:
            res['period_id'] = datas['form']['period_id'] and datas['form']['period_id'][0] or False
        return res
    
    def format_date(self, date, str_format):
        """
        format date with string format
        """
        if not date:
            return ''
        if type(date) != type(datetime.today()):
            date = datetime.strptime(str(date),'%Y-%m-%d')
        if not str_format:
            str_format = '%d-%b-%y'
        return date.strftime(str_format)
    
    def get_period(self):
        """
        get date from wizard
        """
        res = False
        wizard_data = self.get_wizard_data()
        if wizard_data:
            res = wizard_data['period_id']
        if res:
            return self.pool.get('account.period').browse(self.cr, self.uid, res)
        return ''
    
    def get_period_name(self):
        """
        get name period
        """
        period = self.get_period()
        if not period:
            return ''
        return period.name
        
    def next_no(self):
        val =self.no + 1
        self.no = val
        return self.no
    
    def get_all_payslips(self):
        """
        get all info base on period from wizard
        """
        result = []
        
        # get date from, date to of the selected period (month)
        period = self.get_period().name
        period_split = period.split('/') 
        date_from = '%s-%s-%s' % (period_split[1],period_split[0],'01')
        calendar_info = calendar.monthrange(int(period_split[1]),int(period_split[0]))
        date_to = '%s-%s-%s' % (period_split[1],period_split[0],calendar_info[1])
        
        
        hr_payslip_obj = self.pool.get('hr.payslip')
        hr_payslip_ids = hr_payslip_obj.search(self.cr, self.uid, [('date_from','>=', date_from), ('date_to','<=', date_to)], order='employee_id')
        hr_payslip_objs = hr_payslip_obj.browse(self.cr, self.uid, hr_payslip_ids)
        payslip_data = {}
        """
        payslip_data = {'name': 'abd', 'pit_number': '123' ...}
        """
        for hr_payslip_obj in hr_payslip_objs:
            payslip_data = {}
            payslip_data.update({
                'name': hr_payslip_obj.employee_id.name,
                'pit_number': '123', # ???
                'salary': hr_payslip_obj.contract_id and hr_payslip_obj.contract_id.wage or 0,
                'personal_deduction': 'per', # ??? associated with each line on payslip lines
                'dependent_deduction': 'dep', # ???
                'taxable_income': 'tax i', # ???
                'pit_lev_1': '1', # ???
                'pit_lev_1_rate': '1 rate', # ???
                'pit_lev_1_tax_income': '1 i', # ???    
                'pit_lev_2': '2', # ???
                'pit_lev_2_rate': '2 rate', # ???
                'pit_lev_2_tax_income': '2 i', # ???
                'pit_lev_3': '3', # ???
                'pit_lev_3_rate': '3 rate', # ???
                'pit_lev_3_tax_income': '3 i', # ???
                'pit_lev_4': '4', # ???
                'pit_lev_4_rate': '4 rate', # ???
                'pit_lev_4_tax_income': '4 i', # ???
                'pit_lev_5': '5', # ???
                'pit_lev_5_rate': '5 rate', # ???
                'pit_lev_5_tax_income': '5 i', # ???
                'total_tax_income': 'total', # ???
            })
            result.append(payslip_data)
        
        return result
    
