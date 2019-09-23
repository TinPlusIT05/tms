# -*- coding: utf-8 -*-
{
    'name': 'Data for Vietnam',
    'version': '1',
    'category': 'Manufacturing',
    'description': """
Overview of OpenERP with data for Vietnam.    
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'product',
        'trobz_base',
        'trobz_country_state_vn'
    ],
    'data' : [
       'data/ir.config_parameter_data.xml',
       'data/product_pricelist_data.xml',
       'data/res_currency_data.xml',
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'active': False,
    'application': True,
    'post_objects': ['post.default.vn.data'],

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
