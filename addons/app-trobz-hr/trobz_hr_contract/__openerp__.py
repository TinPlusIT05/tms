#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name": "Trobz HR Contract",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "depends": [
        # OpenERP Modules
        "hr_contract",
        # Trobz Standard
    ],
    "author": "Trobz",
    "description": """

TROBZ HR CONTRACT
=================
 - In contract
    + Add field Is Trial to separate the trial and official contract.
 - In Employee
    + Add field Hired Date due to store the first official date at work.

""",
    'website': 'http://trobz.com',
    'data': [
        'view/hr_contract_view.xml',
        'view/hr_employee_view.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
