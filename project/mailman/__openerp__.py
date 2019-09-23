# -*- coding: utf-8 -*-
{
    'name': 'Mailman Mailing List Manager',
    'version': '1.0',
    'category': 'Mail',
    'description': """
Manage your mailman 2 mailing list.

This module is based on the mailman-api:
http://mailman-api.readthedocs.org/en/stable/index.html

**Notable behaviors**

- Does not delete "dangling" emails from Mailman unless
  explicitly deleted in odoo.

::

    ex: john@mail.com is subscribed in mailman, but not in odoo.
        John will remain subscribed in Mailman.
        In order to unsubscribe John from Mailman you can either:
            - Remove manually from mailman
            - Create a partner for John, add him to the odoo
              mailing list, then remove him from the mailing list.

- "Dangling" emails will be listed in the field "Mailman response".
- Deleting from Mailman will be overwritten by next update in odoo.

**Limitations**

This module will not let you create/delete mailing list due to current
limitations of mailman-api.

    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'base',
    ],
    'init_xml': [],
    'data': [
        # Security
        'security/res_group.xml',
        'security/ir.model.access.csv',

        # Data
        'data/ir_config_parameter_data.xml',

        # Views
        'view/mailman_list_view.xml',
        'view/res_partner_view.xml',

        # Wizard
        'wizard/quick_subscription_wizard_view.xml',

        # Menu
        "menu/mailman_menu.xml",

    ],
    'js': [
    ],
    'css': [
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'active': False,
    'application': False,
}
