# -*- encoding: utf-8 -*-

{
    "name" : "Trobz HR Payroll Advance",
    "version" : "1.0",
    "category": "Generic Modules/Human Resources",
    "depends" : [
        # OpenERP Modules
        'hr_payroll_account',
        # Trobz Standard
        'trobz_base',
        'trobz_hr_payroll', 
        ],
    "author" : "Trobz",
    "description": """
Trobz HR Payroll Advance 
================

**New features**

- Use Payslip to record the Advance

- The payroll accounts should be specified on each project.
    """,
    'website': 'http://trobz.com',
    'init_xml': [],
    'update_xml': [        
        #data
        'data/hr_salary_rule_data.xml',
        #view
        'view/hr_payslip_view.xml',
        #menu  
        'menu/hr_menu.xml',
    ],
    'demo_xml': [],  
    'installable': True,
    'active': False,
    'certificate' : '',
    'post_objects': [],
    'post_objects_run_one_time': [
        'post.object.update.salary.rule.condition',
    ]
}
