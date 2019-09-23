# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008-2013 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
#                    General contacts <info@alistek.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
{
    "name": "Deferred Processing",
    "version": "1.0",
    "description": """
DEFERRED PROCESSING
===================
Base module enabling processing intensive tasks, that othervise would cause UI-server communication timeouts
Problem:

There are number of cases with CPU or database intensive processing tasks,
that usually causes user interface to server communication timeouts,
which usually block from implementing OpenERP in large enterprises.
Usually long running tasks may be caused by either large number of records or
CPU/DB intensive algorithms.

Solution:

Process is scheduled and started in a background, so it does not depend on
UI-server communication, even if it would run for multiple hours.
User can monitor the requested process by refreshing a dedicated Process object
(Menu: Administration/Customization/Deferred Processing/Processes).
Once finished, results are stored (if applicable) inside the Process object.

The module is a basic foundation, for to start and
manage long running tasks like:

* calculate large number of CDR;
* send batch e-mails;
* generate large number of invoices;
* batch reporting/printing;
* generate tax returns;
* import large datasets;
* reconciliate accounts;
* generate payroll;
* recalculate pricelists;
* MRP scheduling;

To implement this functionality you may incorporate interfaces of the module in
one of two ways:

* changing OpenERP database configuration manually;
* directly referencing in your custom module (preferred);

One of examples of implemented application using the module - Aeroo Reports,
developed by Alistek.
""",
    "author": "Alistek Ltd.",
    "website": "http://www.alistek.com",
    "category": "Generic Modules",
    "url": "http://www.alistek.com",
    "depends": ['base', 'email_template'],
    "data": ['deferred_processing.xml',
                   'deferred_processing_menu.xml',
                   'security/deferred_processing_security.xml',
                   'security/ir.model.access.csv',
                   'data/email_data.xml', ],
    "demo": [],
    'js': [
        'static/src/js/deferred_processing.js',
    ],
    'css': [
        'static/src/css/deferred_processing.css',
    ],
    'qweb': [
        'static/src/xml/deferred_processing.xml',
    ],
    "license": "GPL-3 or any later version",
    "installable": True,
    "active": False,

}
