# -*- coding: utf-8 -*-
{
    'name': 'Trobz HR report contract list',
    'version': '1.1',
    'category': 'Trobz Internal',
    'description': """
Contract Status Report
======================
- Export all current contracts
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        # Openerp modules
        'hr_contract',
        'hr_payroll_account',
    ],
    'data': [
        # view
        'view/hr_department_view.xml',
        'view/hr_employee_view.xml',
        'view/hr_contract_view.xml',
        # report
        'report/contract_list_report.xml',
        # wizard
        'wizard/print_contract_list_wizard.xml',
        # menu
        'menu/hr_menu.xml',
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'active': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
