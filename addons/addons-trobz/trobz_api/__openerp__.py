# -*- coding: utf-8 -*-
{
    'name': 'Trobz API',
    'version': '1',
    'category': 'Hidden',
    'description': """    
Basic features to support the creation of an API:

* Log of all actions done through the API
* Basic functions: save (create,update), delete 

    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'trobz_base',
        'web_serialized',
    ],
    'data': [
             'menu/trobz_api_menu.xml',
             'view/trobz_api_log_view.xml',
             ],
    'qweb' : [],
    'css' : [],       
    'js': [],
    'test': [],

    # monkey patch xmlrpc handler to record logs
    'post_load': 'patch_xmlrpc_handler'
}
