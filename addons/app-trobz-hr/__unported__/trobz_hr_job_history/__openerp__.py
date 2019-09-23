# -*- coding: utf-8 -*-

{
    'name': 'Trobz HR Job Position History',
    'version': '1.0',
    'category': 'Trobz Standard Modules',
    'description': """
Job Position History
====================

This module is created to keep track changing of job title on his Contract.
After changing the contract Job Position (create, update)

**Job Position History**

 - Employee Name
 - Contract
 - Department
 - Previous Job
 - Current Job
 - Effective Date: Date of change.
 - Responsible User: The one who update the Job Position.

**Employee**

 - Add button Job History to show the job position history of this employee

    """,
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'depends': [
        'hr_contract',
    ],
    'data': [
        # view
        'view/hr_job_history_view.xml',
        'view/hr_employee_view.xml',
        # menu
        'menu/hr_menu.xml',
        # security
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
