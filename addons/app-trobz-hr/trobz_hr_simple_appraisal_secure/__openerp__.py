# -*- encoding: utf-8 -*-
{
    "name": "Simple Appraisal Secure",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "depends": ['trobz_hr_simple_appraisal', ],
    "author": "Trobz",
    "description": """
Change to secured field for the important information on appraisal.
    """,
    'website': 'http://trobz.com',
    'init_xml': [],
    'data': [
        'view/hr_appraisal_view.xml',
        'view/hr_appraisal_input_view.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application': True,
    'certificate': '',
    'post_objects': [],
}
