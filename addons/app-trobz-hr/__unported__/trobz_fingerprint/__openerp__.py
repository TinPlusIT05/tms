#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 Tu Bui tu@trobz.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name" : "Trobz Fingerprint",
    "version" : "1.0",
    "category": "Generic Modules/Human Resources",
    "depends" : [
        # OpenERP Modules
        'trobz_base',
        'trobz_hr_attendance',
    ],
    "author" : "Trobz",
    "description": """
Fingerprint System Integration with OpenERP
===========================================

See detailed description here:

- https://docs.google.com/a/trobz.com/document/d/1CBI0goTib-4MGQSHPO8dfzG60Aw1GeK9vXcZnBQAy8s/edit#heading=h.gcemudvzgc13
    """,
    'website': 'http://trobz.com',
    'init_xml': [],
    'data': [        
        #data
        'data/scheduler_data.xml',
        'data/configuration_data.xml',
        #security
        'security/ir.model.access.csv',
        #view
        'view/fingerprint_record_view.xml',
        'view/connection_config_view.xml',
        # Menu
        'menu/base/base_menu.xml',
    ],
    'demo_xml': [],  
    'installable': True,
    'active': False,
    'certificate' : '',
    'post_objects': [],
}
