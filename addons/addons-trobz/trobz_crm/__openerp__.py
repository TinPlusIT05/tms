
{
    "name": "Trobz CRM Management",
    "version": "1.0",
    "depends": ["base", 'fetchmail', 'crm', 'trobz_base', 'calendar'],
    "author": "Trobz",
    "description": """
This module implements a set of improvements on the native openErp module:
==========================================================================
 - Follow Leads and Opportunities
 - Convert Leads to Opportunities
 - New concept “CRM Event” to group all the types of actions like:
 Email, Phone, Meeting, Tasks
 - View the list of CRM Events from the Parter form
 - Add Skype Contact and link to Linkedin Profile on the Partner Contact
 - Track history of events with a partner, a lead or an history
 (Phone Call, Meeting, Tasks...)
 - Improved display for attachment of an event
 - Archive emails in OpenERP
 - Automatically associate emails to Customer, Prospects, Leads or Opportunity
 - Languages: English, French and Vietnamese


    """,
    'category': 'Customer Relationship Management',
    'website': 'http://www.openerp.com',
    'init_xml': [],
    'data': [
        # data
        "data/crm_data.xml",
        "security/ir.model.access.csv",
        'security/res_group.xml',

        # view
        "view/crm_lead_probability_view.xml",
        "view/crm_case_stage_view.xml",
        "view/res_partner_view.xml",
        "view/crm_lead_view.xml",
        "view/crm_lost_reason_view.xml",
        "view/trobz_crm_event_view.xml",
        "view/trobz_crm_business_sector_view.xml",
        "view/base_partner_merge_view.xml",
        # menu
        "menu/crm_menu.xml",

        # wizard
        "wizard/crm_lead_to_opportunity_view.xml",
        # Always place at last
        'data/function_data.xml',
        'data/calendar_alarm_data.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '',

}
