#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) Trobz (<http://www.trobz.com>)
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
    "name" : "Trobz HR Attendance",
    "version" : "1.0",
    "category": "Generic Modules/Human Resources",
    "depends" : [
        # OpenERP Modules
        "hr_attendance",
        # Trobz Standard
        'trobz_base', 
        ],
    "author" : "Trobz",
    "description": """
    
This module inherit from module hr attandance. The module allow:
=======================================================================
        + Import attendance from *.csv.
        + Show the list employees are absence.
    """,
    'website': 'http://trobz.com',
    'init_xml': [],
    'update_xml': [        
        #data
        
        #view
        'view/hr_attendance_view.xml',
        'view/import_attendance_error_view.xml',
        #report
        'report/hr/detect_absence_report.xml',
        # wizard
        'wizard/hr/import_attendance_wizard.xml',
        'wizard/hr/detect_absence_wizard.xml',
        'wizard/hr/check_attendance_consistency_wizard.xml',
        #menu
        'menu/hr_attendance_menu.xml',
        #security
    ],
    'demo_xml': [],  
    'installable': True,
    'active': False,
    'certificate' : '',
    'post_objects': [],
}
