# -*- coding: utf-8 -*-
{
    'name': 'Widget: index in many 2 many lists',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Display an index in tree view and many2many widgets

usage:

::

<field name="field_name" indexes="True"  />
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'web_unleashed'
    ],
    
    'data': [
    ],
    
    'qweb' : [
    ],
    
    'css' : [
    ],
       
    'js': [
        'static/src/js/indexed_list.js'
    ],
    
    'test': [
    ]
}