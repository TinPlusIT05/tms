#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name" : "Trobz HR Payslip Parameters",
    "version" : "1.0",
    "category": "Generic Modules/Human Resources",
    "depends" : [
        # OpenERP Modules
        "hr_contract", 
        # Trobz Standard
        'trobz_base',
        'trobz_hr_payroll',
        ],
    "author" : "Trobz",
    "description": """
Payslip Parameter on Contracts
==============================
**Payslip Parameter**

**Payslip Paramter Group**

**Contract**
When select the employee grade, Auto update the payslip parameter group base on the grade which have been defined on the payslip parameter group

**Payslip**
Caculate the salary inputs base on the payslip parameter group that link to the current contract of this payslip.
    """,
    'website': 'http://trobz.com',
    'init_xml': [],
    'data': [ 
        #data
        'data/hr_payslip_parameter_data.xml',
        
        #view
        'view/hr_contract_view.xml',
        'view/hr_employee_level_view.xml',
        'view/hr_employee_grade_view.xml',
        'view/hr_payslip_parameter_view.xml',
        'view/hr_payslip_parameter_group_view.xml', 

        #menu
        'menu/hr_menu.xml',
        
        #security
        "security/ir_rule.xml",    
        "security/ir.model.access.csv",
    ],
    'demo_xml': [],  
    'installable': True,
    'active': False,
    'certificate' : '',
    'post_objects': [],
}
