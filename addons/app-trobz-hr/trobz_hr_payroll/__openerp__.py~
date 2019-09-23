# -*- encoding: utf-8 -*-

{
    "name" : "Trobz HR Payroll",
    "version" : "1.0",
    "category": "Generic Modules/Human Resources",
    "depends" : [
        # OpenERP Modules
        'hr_payroll',
        'hr_payroll_account',
        # Trobz Standard
        'trobz_hr_contract',
        'trobz_hr_holiday',
        ],
    "author" : "Trobz",
    "description": """
TODO: Need to be refactor, now it is the same source code of V7 but installable on v8
Trobz HR Payroll
================
    
**Salary Rule**
- Add field: Global Rule: checkbox
    + If it's not checked, this rule will be calculated for each contract.
    + Otherwise, this rule will be sum of amount of all contracts
    in the payslip period of time


**Payroll computation**
- Allow to compute payroll in case having many valid contracts
in the payslip period of time
    """,
    'website': 'http://trobz.com',
    'init_xml': [],
    'data': [        
        #data
        'data/trobz_hr_payroll_data.xml',
        #view
        'view/hr_contract_view.xml',
        'view/hr_payslip_view.xml',
        'view/hr_salary_rule_view.xml',
        'view/hr_holidays_line_view.xml',
        'view/hr_payroll_structure_view.xml',
        'view/hr_salary_rule_category_view.xml',
        #security
        "security/ir.model.access.csv",
        "security/ir_rule.xml",    
    ],
    'demo_xml': [],  
    'installable': True,
    'active': False,
    'certificate' : '',
    'post_objects': [],
}
