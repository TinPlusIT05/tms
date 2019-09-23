# -*- encoding: utf-8 -*-

{
    "name" : "Trobz Overtime Management",
    "version" : "1.1",
    "category": "Generic Modules/Human Resources",
    "depends" : [
        #OpenERP Native Modules
        'hr',
        'hr_attendance',
        # Trobz Standard
        'trobz_base',
        ],
    "author" : "Trobz",
    "description": """
Trobz HR OVERTIME
=================
            
        + Management of overtime and compensations.
         
        """,
    'website': 'http://trobz.com',
    'init_xml': [],
    'data': [
         # Data
        'data/hr_overtime_workflow.xml',
        #security
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        #view
        'view/hr_overtime_view.xml',
        #menu
        'menu/hr_menu.xml',
    ],
    'demo_xml': [],  
    'installable': True,
    'active': False,
    'certificate' : '',
    'post_objects': [],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
