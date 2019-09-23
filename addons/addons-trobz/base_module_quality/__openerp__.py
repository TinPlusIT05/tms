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
    'name': 'Analyse Module Quality',
    'version': '1.0',
    'category': 'Tools',
    'description': """
The aim of this module is to check the quality of other modules.
================================================================

It defines a wizard on the list of modules in OpenERP, which allows you to
evaluate them on different criteria such as: the respect of OpenERP coding
standards, the speed efficiency...

This module also provides generic framework to define your own quality test.
For further info, coders may take a look into base_module_quality\README.txt

WARNING: This module cannot work as a ZIP file, you must unzip it before
using it, otherwise it may crash.

Current criteria
================

* Trobz Test
    + Make sure source code follow Trobz structure: wizard, view, data,
model,...
    + Make sure one python file contains 1 class
    + Files are stored in the correct folders "menu", "data", "view"
    + New model (not Transient) has at least 3 views (form, tree, search)
    + Views name have correct naming convention
* Structure Test
    + Check the source code structure for all files "report", "wizard",
"security"
    + Make sure there is a file "__openerp__.py" in the module
* Pep8
    + Check import
    + There should be one space after , : ;
    + Does the module avoid unecessary queries like when we put a
browse into a loop?
    + More than one space around an assignment (or other) operator to align
it with another.
    + For sequences (strings, lists, tuples) use the fact that empty
sequences are false
    + Don't compare boolean values to True or False using == and !=
* Method
    + Make sure all methods (search, field_view_get, read) are run without
any errors
* File __openerp__.py:
    + Make sure all required "tags" have information
    + Raise warnings for missing "optional" tags
* Object Test
    + Test checks for fields, views, security rules, dependency level
* Workflow:
    + Trobz specific: just use for reference, do not calculate score
* Pylint:
    + Trobz specific: just use for reference, do not calculate score
* Speed Test:
    + Trobz specific: just use for reference, do not calculate score
* Unit Test:
    + Run unit test (unit_test/test.py) file of the module
    + Do not calculate score
""",
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'depends': [],
    'data': [
        'wizard/module_quality_check_view.xml',
        'wizard/quality_save_report_view.xml',
        'base_module_quality_view.xml',
        'security/ir.model.access.csv',
        'menu/menu.xml',
        'data/ir_cron.xml'
    ],
    'demo_xml': [],
    'installable': True,
    'auto_install': False,
    'certificate': '0175119475677',
    'images': [
        'images/base_module_quality1.jpeg',
        'images/base_module_quality2.jpeg',
        'images/base_module_quality3.jpeg'
    ]
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
