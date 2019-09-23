# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for Odoo
#   Copyright (C) 2015 Trobz (http://www.trobz.com).
#   @author Tran Quang Tri <tri@trobz.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

{
    'name': 'Field Secure',
    'version': '1.1',
    'category': 'Core, ORM',
    'description': """
This module add a new field type into Odoo System for storing
information in secure way by encrypting them using AES algorithm.

To use this kind of field, user have to inherit from `SecureModel`
which came from this module instead of `Model` and then use `fields.Secure`
to define the secure field, the full example can be found in README file.
    """,
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'depends': [
        'base', 'web'
    ],
    'data': [
        'views/field_secure.xml',
    ],
    'qweb': [
        'static/src/xml/base.xml'
    ],
    'test': [],
    'demo': [],
    'application': True,
    'sequence': -99,
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
