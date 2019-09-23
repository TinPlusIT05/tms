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
    'name': 'Trobz Base',
    'version': '1.3',
    'category': 'Trobz Standard Modules',
    'summary': 'General features for all projects',
    'description': """
Features available in all projects at Trobz
===========================================
**User management**
-------------------
* Automatically set the time-zone of the users based on a default time zone\
(see below in configuration)
* Use a new concept "Profile" to create/update users easily

**Modules**
-----------
* Add buttons on the list view of modules to install from the list
* By default, display the list view rather than the kanban view

**ERP Maintenance**
-------------------
* Check the type of the instance running. If not production, all e-mails are\
redirected to a default email  (set in config parameter with the key\
'default_email' or 'poweremail.test@trobz.com').
* Set the UI to Extended mode for admin user.
* Upgrade all installed modules from Trobz automatically when upgrading the\
module trobz_base

Available functions which are often used in projects
====================================================
* update_company_logo
* create_model_access_rights
* load_language
* update_config: Can be used to update the application setting at Settings >\
Configuration > xxx
* unlink_object_by_xml_id
* delete_default_products
* run_post_object_one_time: run functions to create/update data in\
project module
* Create standard library to import CSV file
* Convert number to text: 100 > one hundred (available for Vietnamese and\
English)

Automatic Configuration Functionalities
=======================================
The below configurations can be done automatically when installing the module\
only by creating an ir.config_parameter.

**Set the default time zone of the users**
------------------------------------------
* Default is Asia/Ho_Chi_Minh.

**Update Separator Format for Language**
----------------------------------------
* Default is en_US.UTF-8
""",
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'depends': ['web', 'email_template'],
    'data': [
        # data
        'data/base/ir_cron_data.xml',
        'data/base/ir_config_parameter_data.xml',

        # security
        'security/ir_module_category_data.xml',
        'security/trobz_base_security.xml',
        'security/ir.model.access.csv',

        # Include web module change
        'views/trobz_base.xml',

        # view
        'view/base/ir_module_view.xml',
        'view/base/res_users_view.xml',
        'view/base/res_groups_view.xml',
        'view/base/ir_cron_view.xml',

        # wizard
        'wizard/base_language_export.xml',
        'wizard/trobz_maintenance_connection_view.xml',

        # menu - should always in the end of the list
        'menu/trobz_base_menu.xml',

        # function data to update configuration data
        'data/base/function_data.xml',

    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'active': False,
    'certificate': '',
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: