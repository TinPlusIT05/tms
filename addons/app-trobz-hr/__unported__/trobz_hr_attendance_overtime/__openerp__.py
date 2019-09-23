#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name": "Trobz HR Attendance Overtime",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "depends": [
        # OpenERP Modules
        "hr_attendance",
        "trobz_hr_overtime",
        "trobz_hr_holiday",
        # Trobz modules
        "trobz_base"
        ],
    "author": "Trobz",
    "description": """
Attendance report
=================
    """,
    'website': 'http://trobz.com',
    'init_xml': [],
    'update_xml': [
        # data
        # view
        # report
        'report/hr_attendance_overtime_report.xml',
        # wizard
        'wizard/hr_attendance_overtime_report_wizard_view.xml',
        # menu
        'menu/hr_attendance_overtime_menu.xml',
        # security
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
    'post_objects': [],
}
