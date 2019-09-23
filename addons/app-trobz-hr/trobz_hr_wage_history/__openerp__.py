# -*- coding: utf-8 -*-

{
    'name': 'Trobz HR Wage History',
    'version': '1.0',
    'category': 'Trobz Standard Modules',
    'description': """
WAGE HISTORY
=============

This module is created to keep track the Wage of Employee in his Contract.
After changing the contract wage (create, update),
this will create a readonly wage history record

**Wage History**

 - Employee Name
 - Contract
 - Department
 - Job
 - Current Wage
 - New Wage
 - Difference: New Wage - Current Wage
 - Percentage: (New Wage - Current Wage) / Current Wage * 100
 - Effective Date: Date of change.
 - Responsible User: The one who update the wage.

**Employee**

 - Add button Wage History:

   + Show the number of Wage History records on this button.
   + Click the button to see more information about Wage History of Employee

    """,
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'depends': [
        'hr_contract',
        'trobz_base',
    ],
    'data': [
        # view
        'view/wage_history_view.xml',
        'view/hr_employee_view.xml',
        # menu
        'menu/wage_history_menu.xml',
        # security
        'security/ir.model.access.csv',
        # Function
        'data/function_data.xml'
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
