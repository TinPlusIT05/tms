#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name": "Trobz HR Report Payslip",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "depends": [
        # OpenERP Modules
        "hr_payroll",
        # Trobz Standard
        "trobz_report",
    ],
    "author": "Trobz",
    "description": """

TROBZ HR REPORT PAYSLIP
=================
 - Add a specific Payslip report using Trobz template

""",
    'website': 'http://trobz.com',
    'data': [
        # report
        'report/report_extent_payslip.xml',

    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
