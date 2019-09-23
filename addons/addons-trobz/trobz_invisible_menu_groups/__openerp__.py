# -*- coding: utf-8 -*-

{
    "name": 'Invisible Menu based on Group',
    "version": "1.0",
    "description":
"""
===================================
Add new options for menu:
===================================

invisible_groups: to invisible menu with specific groups

Example:
--------

<menuitem id="menu_adv_salary"
			action="action_salary_advance_form"
			sequence="1"
			parent="menu_employee_deduction"
			name="Advance on Salary"
			invisible_groups="base.group_user"
			groups="account.group_account_invoice,account.group_account_manager,base.group_hr_user"/>

if there are both option "invisible_groups" and "groups" in a menu, "invisible_groups" has higher priority

""",
    "depends": [
        'base',
        'web',
    ],
    'data': [
        #Views
        'view/ir_ui_menu_view.xml'
    ],
    "js": [
    ],
    'qweb': [
    ],
    "author": "Trobz",
    "website": "<http://trobz.com>",
    "installable": True,
}


