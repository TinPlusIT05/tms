#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name": "Trobz HR Application",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "depends": [
        # OpenERP Modules
        "hr",
        "hr_recruitment"
        # Trobz Standard
    ],
    "author": "Trobz",
    "description": """

TROBZ HR APPLICATION
=================

 - In contract
    + Add field Employee on the application after I create the Employee.
 - In Employee
    + Add field m2o on the Employee to link to the application.
 - And by default don't broadcast the welcome message
    + Add mail_broadcast option to ir_config_parameter: By default, set it 'False'.
""",
    'website': 'http://trobz.com',
    'data': [
        # data
        'data/ir_config_parameter_data.xml',
        # view
        'view/hr_employee_view.xml',
        'view/hr_applicant_view.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
