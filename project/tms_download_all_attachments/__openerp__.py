# -*- coding: utf-8 -*-
{
    'name': 'TMS Dowload All Attachments',
    'version': '1',
    'category': 'Trobz Standard Modules',
    'description': """
This module is intended to be used for One Click dowlad all attachments on form
and tree view of model
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'base'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/dowload_all_attachments_view.xml',
        'views/dowload_all_attachments_wizard_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
