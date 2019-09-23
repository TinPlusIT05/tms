# -*- encoding: utf-8 -*-

{
    "name" : "Trobz HR Payroll Overtime",
    "version" : "1.1",
    "category": "Generic Modules/Human Resources",
    "depends" : [
        #OpenERP Native Modules
        # Trobz Standard
        'trobz_base',
        'trobz_hr_overtime',
        'trobz_hr_payroll',
        'trobz_hr_payroll_working_hour'
        ],
    "author" : "Trobz",
    "description": """
Trobz HR PAYROLL OVERTIME
=========================
        + Add working activity such as Working days, OT on regular days, OT on weekend in Overtime.
        + After approving the payslips, the overtime records on this period also change to state "done"
""",
    'website': 'http://trobz.com',
    'init_xml': [],
    'data': [
        # Data
        #security
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        #view
        'view/hr_overtime_view.xml',
        #menu
    ],
    'demo_xml': [],  
    'installable': True,
    'active': False,
    'certificate' : '',
    'post_objects': [],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
