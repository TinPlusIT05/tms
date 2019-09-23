# -*- coding: utf-8 -*-
{
    "name": 'web_o2m_enhanced',
    "version": "0.1",
    "depends": [
        'base',
        'web',
        'trobz_base'
    ],
    "category": 'web',
    "description": '''
    Add option to limit the line for showing in one2many field.
    </br>
    Example:
    <field name="order_lines" options="{'limit': 10 }"/>
    It will limit the line of order_lines is 10 per page.
    ''',
    "js": [
        'static/src/js/form.js',
    ],
    "author": "Chanh Le<chanh@trobz.com>",
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
