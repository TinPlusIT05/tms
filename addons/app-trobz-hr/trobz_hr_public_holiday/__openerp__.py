#!/usr/bin/env python
# -*- encoding: utf-8 -*-
{
    "name" : "Trobz HR Public Holiday",
    "version" : "1.0",
    "category": "Generic Modules/Human Resources",
    "depends" : [
        # OpenERP Modules
        'hr',
        # Trobz Standard
    ],
    "author" : "Trobz",
    "description": """
Public Holiday
==============
- The public holiday templates which have Template Holiday field checked will be configured for a specific company.
At the end of each year, the public holidays of next year are automatically created based on the public holidays template by running the scheduler.
And you can select to create Public Holiday for specify year, just put the year into the Arguments in the Scheduler. Example: Arguments = (2015,)
 
 """,
    'website': 'http://trobz.com',
    'data': [        
        #data 
        "data/ir_cron_data.xml",
        #view
        'view/hr_public_holiday_view.xml', 
        #wizard
        #menu
        'menu/hr_menu.xml',
        #security
        "security/ir.model.access.csv",
        
    ],
    'demo_xml': [],  
    'installable': True,
    'active': False,
    'certificate' : '',
}
