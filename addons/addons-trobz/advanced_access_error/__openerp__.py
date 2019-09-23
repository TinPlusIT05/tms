# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2009-2015 Trobz (http://trobz.com).
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
    'name': 'Advanced Access Error',
    'version': '8.0.1',
    'category': 'Trobz Standard Modules',
    'description': """
    The error messages about security in Odoo are difficult for users
    to understand what is the problem. This module puts more information
    into the error messages to help users to solve / fix problems faster.
    In this module, we do some adjusments:
        - Custom message about access right by function
            "adjustment_message_error_access" in ir_model
        - Add 1 function "hook_improve_error_message_record_rules"
            inside function "_check_record_rules_result_count" in models.py
            in core, then monkey-patch it to raise a nicer error message
            related to access rule for CRUD action
        - Add 1 function "hook_nicer_error_message"
            inside function _read_from_database in models.py in core.
            Then monkey-patch it to raise a nicer error message related to
            access rule when reading some field from database
    """,
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'depends': ['base'],
    'data': [
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
