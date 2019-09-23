#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name" : "Trobz HR Payroll Working Hour VN",
    "version" : "1.0",
    "category": "Vietnmese Localization",
    "depends" : [
        'trobz_base',
        'trobz_hr_payroll_working_hour',
        'trobz_hr_holiday_vn',
    ],
    "author" : "Trobz",
    "description": """Working Activities and Leave types link to a specific working activity""",
    'website': 'http://trobz.com',
    'init_xml': [],
    'data': [
        'data/hr_working_activity_data.xml',
        'data/hr_holidays_status_data.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate' : '',
    'post_objects': [],
}
