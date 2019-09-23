# -*- coding: utf-8 -*-
{
    'name': 'Trobz HR Payroll Vietnam',
    'version': '1.1',
    'category': 'Trobz Internal',
    'description': """
TODO: Need to be refactor, now it is the same source code of V7 but installable on v8
HR Payroll for Vietnam
======================
* Adding fields to calculate Payroll

* Create payroll structure for Vietnam

* Adding a field to handle the computation of thirdteenth salary 
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        # Trobz standard modules
        'trobz_hr_contract',
        'trobz_hr_payroll',
    ],
    'data' : [
              
        #data
        'data/ir_config_parameter_data.xml',
        'data/salary_structure_template_vn_data.xml',
        'data/pit_details_data.xml',
        
        #view
        'view/hr_employee_view.xml',
        'view/hr_contract_view.xml',
        'view/hr_payslip_view.xml',
        'view/hr_payslip_run_view.xml',
        'view/pit_details_view.xml',
        
        #wizard
        'wizard/salary_calculation_wizard.xml',
        
        #security
        'security/ir.model.access.csv',
        
        #menu
        'menu/hr_menu.xml',
        
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'active': False,
    'application': True,
    'post_objects': [],

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
