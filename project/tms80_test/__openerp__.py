# -*- coding: utf-8 -*-
{
    'name': 'TMS Automatic Test',
    'version': '1',
    'category': 'Trobz Standard Modules',
    'description': """
Automatic Tests of features in TMS
==================================

**Project Configuration**

- Check the creation of following objects
 - Partners
 - Users (Technical Project Manager, Trobz Default Supporter, Tester)
 - OpenERP Version
 - Project
 - Milestone
 - Repository
 - Project Repository
 - Operating System
 - Virtualization
 - Host
 - Instance
 - Sprint

**Forge and Support Tickets**

- Check the creation of following objects
 - Forge ticket (all Trobz users should be able to create one)
 - Support ticket (only FC, TPM and Customer Editor)
- Workflow
 - Forge ticket workflow
 - Support workflow

**Delivery Status**

- Create deliveries and check related tickets' statuses

**Access Rights**

- Profiles to check:
    Technical Consultant, TPM, QC, FC, Admin, Customer Editor,
    Customer (readonly), Partner

**Working Hour and KPIs**

- Check the creation of following objects
 - Analytic Second Axis
 - Analytic Account
 - Activity
 - Employee
- Define Employee Capacity
- Input working hours on forge tickets and support tickets
- Reopen tickets
- Calculate the KPIs

    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'test_runner',
        'tms_modules',
    ],
    'data': [
        'data/module_automatic_test_data.xml'
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'active': False,
    'application': True,

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
