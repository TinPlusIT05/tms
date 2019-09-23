# -*- coding: utf-8 -*-
{
    'name': 'TMS Audit Test Module',
    'version': '1',
    'category': 'Trobz Standard Modules',
    'description': """
TMS Audit Test Module
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'web', 'web_unleashed', 'tms_modules'
    ],
    'data': [

        # data --------------------------------
        'data/ir_config_parameter_data.xml',
        'data/ir_cron_data.xml',
        'data/tms_audit_functions_data.xml',
        # view --------------------------------
        'view/analysis/tms_audit_test_view.xml',
        'view/analysis/tms_audit_result_view.xml',
        'view/analysis/tms_audit_board_view.xml',

        # views -------------------------------
        'views/tms_audit.xml',

        # menu --------------------------------
        'menu/analysis_menu.xml',
    ],
    'qweb': [
        'static/src/xml/base.xml',
        'static/src/xml/audit_view.xml'
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'active': False,
    'application': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
