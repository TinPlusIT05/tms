# -*- encoding: utf-8 -*-
{
    'name': 'Simple Appraisal',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'depends': ['hr'],
    'author': 'Trobz',
    'description': """
    """,
    'website': 'http://trobz.com',
    'init_xml': [],
    'data': [
        # data
        'data/email_template_data.xml',
        'data/ir_cron_data.xml',
        # security
        'security/res_group.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        # Wizards
        'wizards/hr_add_evaluators_wizard_view.xml',
        'wizards/hr_config_settings_wizard_view.xml',
        # views
        'views/hr_appraisal_view.xml',
        'views/hr_appraisal_input_view.xml',
        'views/hr_appraisal_question_group_view.xml',
        'views/hr_appraisal_template_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_menu.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'application': True,
    'certificate': '',
    'post_objects': [],
}
