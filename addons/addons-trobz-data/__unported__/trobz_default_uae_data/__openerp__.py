# -*- coding: utf-8 -*-
{
    'name': 'Data for LPL Group - UAE',
    'version': '1',
    'category': 'Manufacturing',
    'description': """
Overview of OpenERP with data for LPL Group.    
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'product',
        'purchase',
        'trobz_currency_rate_update',
        'trobz_base',
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
    'post_objects': ['post.default.uae.data'],

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
