# -*- coding: utf-8 -*-
{
    'name': 'Web many2one no quick create',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Disabke quick create and create/edit options on many2one widgets by default, can be overrided by using options attribute
on the field.
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
        'static/src/js/m2o_no_quick_create.js'
    ],
    
    'test': [
    ]
}