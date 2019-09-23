#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name": "Trobz HR mail holiday",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "depends": [
        # Trobz Standard
        'trobz_hr_holiday'
        ],
    "author": "Trobz",
    "description": """
Module features
===============
  - Notification by email for:
       . Approval/refusal of leave requests (email to the employee)

       . Leave requests to approve (email to managers)

       . Send reminding Email to managers for the confirmed leave requests
    """,
    'website': 'http://trobz.com',
    'data': [
        # data
        "data/email_template_data.xml",
        "data/ir_cron_data.xml"
    ],
    'update_xml': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
