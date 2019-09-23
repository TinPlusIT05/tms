# -*- coding: utf-8 -*-
{
    'name': 'Deferred Processing Examples',
    'version': '1.0',
    'category': 'Trobz Standard Modules',
    'description': """
This module will install all module dependencies of rock.
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'deferred_processing',
    ],
    'data': [
        # ============================================================
        # SECURITY SETTING - GROUP - PROFILE
        # ============================================================
        # 'security/',

        # ============================================================
        # DATA
        # ============================================================
        # 'data/',

        # ============================================================
        # VIEWS
        # ============================================================
        'view/deferred_processing_example_view.xml',
        'view/deferred_processing_example_workflow.xml',

        # ============================================================
        # MENU
        # ============================================================
        # 'menu/',

        # ============================================================
        # FUNCTION USED TO UPDATE DATA LIKE POST OBJECT
        # ============================================================
        # "data/rock_update_functions_data.xml",
    ],

    'test': [],
    'demo': [],

    'installable': True,
    'active': True,
    'application': False,
}
