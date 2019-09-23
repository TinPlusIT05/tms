#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name": "Trobz Holiday",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "depends": [
        # OpenERP Modules
        "hr_contract",
        "hr_holidays",
        # Trobz Standard
        'trobz_hr_public_holiday',
        'trobz_hr_contract',
        'booking_chart'
    ],
    "author": "Trobz",
    "description": """
FUNCTIONS MIGRATED TO VERSION 8
==============================
""",
    'website': 'http://trobz.com',
    'data': [
        # data
        'data/ir_config_parameter_data.xml',
        'data/ir_cron_data.xml',
        'data/holiday_data.xml',
        # view
        'view/hr_job_view.xml',
        'view/hr_employee_view.xml',
        'view/hr_contract_view.xml',
        'view/hr_holidays_status_view.xml',
        'view/hr_holidays_view.xml',
        'view/hr_holidays_line_chart_view.xml',
        'view/hr_holidays_line_view.xml',
        'view/hr_holidays_workflow.xml',
        # menu
        'menu/hr_menu.xml',
        # security
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
