# -*- coding: utf-8 -*-
{
    'name': 'Web HTML in list view',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Add support of HTML field in list (tree) views.

usage:

::

<field name="field_name" widget="html_in_list" />

    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'web_unleashed'
    ],

    'data': [
        'view/web_html_in_list_view.xml',
    ],

    'qweb': [
    ],

    'test': [
    ]
}
