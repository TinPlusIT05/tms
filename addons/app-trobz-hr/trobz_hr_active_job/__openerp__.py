# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2016 Trobz (<http://trobz.com>).
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
    "name": "Trobz HR Active Job",
    "version": "8.0.0.1.0",
    "category": "Generic Modules/Human Resources",
    "depends": [
        # OpenERP Modules
        "trobz_hr_holiday",
        # Trobz Standard

    ],
    "author": "Trobz",
    "description": "",
    'website': 'http://trobz.com',
    'data': [
        # data
        # view
        'views/hr_job_view.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
