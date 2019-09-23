# -*- coding: utf-8 -*-
{
    'name': 'Trobz Web Attachment',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Add attachment support on form and list view.

2 new widgets:

- in form: simple_attachment
- in list: attachements
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
        'static/src/js/column_attachments.js',
        'static/src/js/field_attachment.js',
    ],
    
    'test': [
    ]
}