#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name" : "HR Holiday France",
    "version" : "1.0",
    "category": "Generic Modules/Human Resources",
    "depends" : ['trobz_base', 'trobz_hr_holiday'],
    "author" : "Trobz",
    "description": """
Specific Settings for France
============================

**Public Holidays for France**

- Reference:
    - `Public holidays in France <http://en.wikipedia.org/wiki/Public_holidays_in_France>`_
    - `Fêtes et jours fériés en France <http://fr.wikipedia.org/wiki/F%C3%AAtes_et_jours_f%C3%A9ri%C3%A9s_en_France#Tableau_r.C3.A9capitulatif>`_

""",
    'website': 'http://trobz.com',
    'data': [
        'data/trobz_hr_public_holidays_data.xml',
        'data/ir_config_parameter_data.xml'
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate' : '',
    'post_objects': ['post.object.hr.holiday.fr'],
}
