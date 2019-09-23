#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name": "Trobz HR mail payslip",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "depends": [
        'hr_payroll'
        ],
    "author": "Trobz",
    "description": """
## Module features

Send email automatically when approving payslip.
""",
    'website': 'http://trobz.com',
    'init_xml': [
        # data
        "data/email_template_data.xml",
        'data/ir_config_parameter_data.xml',
        # wizard
        "wizard/human_resource_config_settings_wizard_view.xml"
    ],
    'update_xml': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
