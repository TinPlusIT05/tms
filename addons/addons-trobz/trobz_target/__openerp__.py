# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
    'name': 'Trobz Target',
    'version': '1.0',
    'category': 'Trobz Standard Modules',
    'description': """
    """,
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'depends': ['trobz_base'],
    'init_xml': [],
    'data': [
        'security/ir.model.access.csv',
          #View
        'view/target_type_view.xml',
        'view/target_view.xml',
        #Menu
        'menu/target_menu.xml',        
    ],    
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
