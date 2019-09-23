#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name": "Trobz HR Employee Hierarchy",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "depends": [
        # OpenERP Modules
        "hr",
    ],
    "author": "Trobz",
    "description": """
Employee Hierarchy
==================
 - Tree view to show employee structure based on manager field.
""",
    'website': 'http://trobz.com',
    'data': [
        'menu/hr_menu.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
