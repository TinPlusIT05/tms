# -*- coding: utf-8 -*-

{
    'name': 'Trobz HR Documents',
    'version': '1.0',
    'category': 'Trobz Standard Modules',
    'description': """
HR Document Management
======================
Purpose is to track all official documents of employees.\n
By default, the module will allow you to track
Passport, Visa, Identification Card and Driving License.
You can add extra documents types through
the menu HR > HR > Document.\n
This module will allow you configuring 2 weekly reminders
sent to the users with the group HR Manager
through the menu Setting > Configuration > Human Resources:\n
\t- Send weekly reminder to HR Manager for Documents expiring in 30 days\n
\t- Send weekly reminder to HR Manager for Documents expired

    """,
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'depends': [
        'hr',
    ],
    'data': [
        # data
        'data/hr_document_type_data.xml',
        'data/hr_config_parameter_data.xml',
        'data/hr_document_email_template_data.xml',
        'data/scheduler_data.xml',

        # wizard
        'wizard/hr_config_settings_wizard_view.xml',

        # view
        'view/hr_document_type_view.xml',
        'view/hr_document_view.xml',
        'view/hr_employee_view.xml',

        # menu
        'menu/hr_menu.xml',

        # security
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
