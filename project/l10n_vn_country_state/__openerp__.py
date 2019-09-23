# -*- coding: utf-8 -*-
# Copyright 2016 Trobz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Vietnamese states (Provinces)",
    "summary": "Vietnamese states (Provinces)",
    "version": "8.0.1.0.0",
    "category": "localization",
    "website": "https://trobz.com",
    "author": "Trobz, "
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "contacts",
    ],
    "data": [
        # data
        "data/res_country_state_data.xml",
        "data/res_country_state_district_data.xml",
        "data/res_country_state_district_ward_data.xml",

        # view
        'views/res_country_state_district_view.xml',
        'views/res_country_state_district_ward_view.xml',

        # menu
        'menu/menu_localization_view.xml',

        # security
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
