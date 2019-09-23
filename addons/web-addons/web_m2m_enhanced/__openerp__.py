# -*- coding: utf-8 -*-
{
    "name": 'web_m2m_enhanced',
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'description': "",
    "version": "0.1",
    "depends": [
        'web',
        'web_unleashed'
    ],
    "category": 'web',
    "description": '''
    Add option to disable create in search(add) form of many2many field.
    </br>
    Example:
    <field name="line_ids" options="{'create': false }"/>
    It will disable create button in search(add) form of many2many field.
    ''',
    'data': [
        'views/web_m2m_enhanced.xml',
    ],
    'qweb' : [
        'static/src/xml/base.xml',
    ],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: