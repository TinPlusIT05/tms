# -*- coding: utf-8 -*-

{
    'name': 'Trobz Security Password',
    'version': '1.0',
    'category': 'Trobz',
    'description': """
    Validate Password with some requirement:
     - at least 7 characters: 7 is a config parameter
     - at least one letter in lower case
     - at least one letter in upper case
     - at least one number
    """,
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'depends': [
        'trobz_base'
    ],
    'init_xml': [],
    'data': [
        'data/property_data.xml',
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
