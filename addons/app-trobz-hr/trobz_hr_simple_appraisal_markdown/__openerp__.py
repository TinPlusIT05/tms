# -*- encoding: utf-8 -*-
{
    "name": "Simple Appraisal Markdown",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "depends": [
        'web_widget_text_markdown',
        'trobz_hr_simple_appraisal',
    ],
    "author": "Trobz",
    "description": """
Add markdown widget to trobz_hr_simple_appraisal module
    """,
    'website': 'http://trobz.com',
    'init_xml': [],
    'data': [
        # data
        # security
        # Wizard
        # view
        'views/hr_appraisal_view.xml',
        'views/hr_appraisal_input_view.xml',

        # meunu
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application': True,
    'certificate': '',
    'post_objects': [],
}
