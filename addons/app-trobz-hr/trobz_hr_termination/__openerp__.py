#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name" : "Trobz HR Termination",
    "version" : "1.0",
    "category": "Generic Modules/Human Resources",
    "depends" : [
        # OpenERP Modules
        "hr_contract", 
        "hr_holidays",
        # Trobz Standard
    ],
    "author" : "Trobz",
    "description": """
    
TROBZ HR TERMINATION
====================
Termination of employee wizard:
- On wizard: 
    + Select the termination date
    + Select list of employees
- Actions:    
    + Inactivate the selected employees
    + End all active contracts of selected employees
    + Cancel all allocation requests and leave requests, including approved leave requests, of selected employees
 
""",
    'website': 'http://trobz.com',
    'data': [        
        #wizard
        'wizard/termination_of_employment_wizard.xml',
        #menu
        'menu/hr_menu.xml',
        #security
        "security/ir.model.access.csv",
        
    ],
    'demo_xml': [],  
    'installable': True,
    'active': False,
    'certificate' : '',
}
