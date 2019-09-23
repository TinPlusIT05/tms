# -*- coding: utf-8 -*-
{
    'name': 'Trobz HR report contract base',
    'version': '1.1',
    'category': 'Trobz Internal',
    'description': """
Contract report
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'report_webkit',
        'hr_contract',
        'trobz_hr_document',
    ],
    'data': [
        # report
        'report/hr_contract_report.xml',
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'active': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
