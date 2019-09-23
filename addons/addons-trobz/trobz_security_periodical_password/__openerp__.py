# -*- coding: utf-8 -*-

{
    'name': 'Trobz Changing Password Policy',
    'version': '1.0',
    'category': 'Trobz',
    'description': """
    Force users to change their password periodically or on a specified date.
    """,
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'depends': [
        'trobz_base',
        'web'
    ],
    'init_xml': [],
    'data': [
        'data/ir_config_parameter_data.xml',
        'view/base_config_settings.xml'
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
