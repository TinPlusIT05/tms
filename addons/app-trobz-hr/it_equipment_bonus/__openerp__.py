#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name": "HR IT Equipment Request",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "depends": [
        'trobz_base',
        'trobz_hr_contract',
        'hr_contract'
    ],
    "author": "Trobz",
    "description": """

HR Equipment Request
====================

""",
    'website': 'http://trobz.com',
    'data': [
        # Data
        'data/ir_config_parameter_data.xml',
        'data/ir_cron_data.xml',
        # Security
        'security/ir_rule.xml',
        # View
        'views/hr_equipment_category_view.xml',
        'views/hr_equipment_request_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_contract_view.xml',
        # Menu
        'menu/hr_equipment_category_menu.xml',
        # ============================================================
        # FUNCTION USED TO UPDATE DATA LIKE POST OBJECT
        # ============================================================
        "data/functions_data.xml",
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
