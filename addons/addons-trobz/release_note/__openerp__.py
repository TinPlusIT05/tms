# -*- coding: utf-8 -*-

#####################################################################
#                © 2016 Trobz http://www.trobz.com                  #
#                                                                   #
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).#
#####################################################################

{
    'name': 'Trobz Release Notes',
    'version': '1',
    'category': 'Hidden',
    'description': """
        Basic features to support showing the release notes:
            * It will contain all tickets which are related to
            * the milestone is deployed

    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
    ],
    'data': [
        'views/webclient_templates.xml'
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
}
