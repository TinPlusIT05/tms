# -*- coding: utf-8 -*-
{
    'name': 'Trobz HR Payroll Vietnam Reports',
    'version': '1.1',
    'category': 'Trobz Internal',
    'description': """
Reports for HR Payroll for Vietnam
==================================
* Create standard report: Payslip report 
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        # Trobz standard modules
        'trobz_base',
        'trobz_report_base',
        'trobz_hr_payroll_vietnam'
    ],
    'data' : [
        
        # report      
       'report/pit_report.xml',
       
       # wizard
       'wizard/print_pit_report_wizard.xml',
       
       # menu
       'menu/hr/hr_menu.xml',
       
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'active': False,
    'application': True,
    'post_objects': [],

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
