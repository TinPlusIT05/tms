# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010 OpenERP s.a. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Test Runner',
    'version': '1.0',
    'category': 'Automatic Test',
    'summary': 'Run module tests',
    'description': """
Run automatic tests on modules by RPC or in user interface.

    """,
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'depends': [],
    # 'depends': [ 'web_html_in_list' ],
    'data': [
        'view/module_automatic_test_view.xml',
        'menu/module_automatic_test_menu.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'js': [
    ],
    'css': [
        'static/src/css/unit-test.css',
    ],
    'qweb': [
    ],
    'installable': True,
    'active': False,
    'certificate': '',
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
