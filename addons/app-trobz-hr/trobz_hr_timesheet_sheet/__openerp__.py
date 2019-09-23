#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name": "Trobz HR Timesheet Sheet",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "depends": [
        # OpenERP Modules
        "hr_timesheet_sheet",
    ],
    "author": "Trobz",
    "description": """
Fix some bugs in native module hr_timesheet_sheet:
- Create My Current Timesheet and cannot discard it.

""",
    'website': 'http://trobz.com',
    'data': [
        'view/hr_timesheet_sheet_sheet_view.xml',
        
        'menu/hr_menu.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
