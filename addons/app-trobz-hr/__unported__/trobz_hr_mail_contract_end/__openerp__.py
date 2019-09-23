#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name": "Trobz HR mail contract end",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "depends": [
        'hr_contract'
        ],
    "author": "Trobz",
    "description": """
Module features
===============
- On the contract form, add a checkbox field "No renewal".
- Every Monday, the system will check the list of people
    who have a contract ending in the next 30 days
    without a next contract created and
    without the No Renewal checkbox set.
    and send an notification email to users with group HR officer
""",
    'website': 'http://trobz.com',
    'init_xml': [
        # data
        "data/email_template_data.xml",
        "data/ir_cron_data.xml",
        # view
        "view/hr_contract_view.xml",
    ],
    'update_xml': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
