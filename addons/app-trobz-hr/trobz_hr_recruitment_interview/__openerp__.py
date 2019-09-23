#!/usr/bin/env python
# -*- coding:utf-8 -*-

{
    "name": "Trobz HR Recruitment Interview",
    "version": "1.0",
    "depends": [
        "hr_recruitment"],
    "author": "Trobz",
    "description": """
Allow to many users add the interview feedbacks on application form
    """,
    'website': 'http://www.openerp.com',
    'init_xml': [],
    'data': [
        # data
        # security
        'security/ir.model.access.csv',
        # view
        "view/hr_applicant_view.xml",
        # menu
        # wizard
        # Always place at last
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
