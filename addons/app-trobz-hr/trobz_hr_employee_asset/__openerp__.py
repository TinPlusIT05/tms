# -*- coding: utf-8 -*-

{
    'name': 'Trobz HR Employee Asset',
    'version': '1.0',
    'category': 'Trobz Standard Modules',
    'description': """
Module features
===============

    """,
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'depends': [
        'hr',
    ],
    'data': [
        # view
        'view/hr_employee_asset_view.xml',
        'view/hr_employee_view.xml',
        # menu
        'menu/hr_menu.xml',
        # security
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
