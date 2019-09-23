#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name": "HR Holiday VN",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "depends": [
        # TODO: remove depend trobz_base
        # when status of 2.5_8.0_no_new_feature id done
        'trobz_base',
        'trobz_hr_holiday'
    ],
    "author": "Trobz",
    "description": """Holiday Data for Vietnam""",
    'website': 'http://trobz.com',
    'data': [
        # Data
        'data/hr_holidays_status_data.xml',
        'data/hr_public_holiday_data.xml',
        'data/ir_config_parameter_data.xml',
        'data/function_data.xml',
        # TODO: move to module trobz_hr_holiday_vietnam
        # 'view/hr_contract_view.xml',
        # 'view/hr_job_view.xml',
        # 'view/hr_employee_view.xml',
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',
    'post_objects': [],
}
