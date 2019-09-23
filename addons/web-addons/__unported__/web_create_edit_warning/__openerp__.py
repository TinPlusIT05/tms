# -*- coding: utf-8 -*-
{
    'name': 'Trobz Web Create Edit Warning',
    'version': '1.0',
    'category': 'Web',
    'description': """
Display warning when create and edit object but can do the action.

Usage:
In Create or Write return {'result': result, 'value': {}, 'warning': {'title': 'Warning', 'message': msg}}

Reference: ~/code/openerp/uma7/addons-uma/uma_modules/model/pos/pos.py
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'base',
        'web',
    ],
    
    'data': [
    ],
    
    'qweb' : [
    ],

    'css' : [
        'static/src/css/base.css',
    ],
       
    'js': [
        'static/src/js/form.js'
    ],
    
    'test': [
    ]
}