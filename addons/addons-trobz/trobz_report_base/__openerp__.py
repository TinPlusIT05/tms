# -*- coding: utf-8 -*-

{
    "name" : "Trobz Report Base",
    "version" : "1.1",
    "author" : "Trobz",
    "category": 'Trobz Standard Modules',
    "description": """
Provide common methods used in reports
=======================================

**Partner Information**

- Load the information (name, address info, bank info) of the partner of the printing user.
- Load the information (name, address info, bank info) of the partner of the printing object.

**Language Control**

- Provide various options to control the languages to be printed in the report:
    - Language can be controlled based on the printing user's language or the object partner's language or
      a specific language based on the parameter report_languages.
    - Print report in dual languages. If a report is printed in dual languages, each term will be printed in the form:
      FACTURE (Invoice), HÓA ĐƠN (Invoice), FACTURA (Invoice)...
    - By default, the secondary language is always the language written in report templates.
      However, you can set a custom language in the parameter report_languages.
 
**Currency**

- Get the currency using in the object.
- Get the currency conversion rate.
- Convert an amount from a currency to another currency.
- Display an amount in words.

**Other methods**

- Get the company name and logo.

    - You can choose the company information is the company of printing user or the company of the printing object.
      By default, it takes the company of the printing object.

- Number the rows in a table.
- Get last two digits of a year.

How to Configure
================

**Inherit trobz_report_base**

- Inherit your reports from trobz_report_base.
- Call the function common_init to initialize common variables to be used in report.
- Call the lang_init function to control the languages to be displayed in report.
- See more details below:

::

    # -*- coding: utf-8 -*-
    
    from trobz_report_base.report import trobz_report_base
            
    class Parser(trobz_report_base.Parser):
    
        def __init__(self, cr, uid, name, context):
            super(Parser, self).__init__(cr, uid, name, context=context)
            # Set custom parameters for this report
            #
            # Initialize common variables to be used in report
            self.common_init(context=context)
            self.lang_init()
            # Initialize specific objects for the report
            #
            self.localcontext.update({
                # Add specific variables for the report
            })
            
**Language**

- In report templates, use the t function to translate a term, for example, t('INVOICE').
- In code, calling self.lang_init() function will set the primary language according to printing users' languages.
  For example, a user who has the language reference set to French will have reports in French.

::

    self.lang_init()

- If you want to control language based on other objects, provide options to self.lang_init:

    - Set self.use_user_lang to False to indicate that primary language to be displayed should not base on printing user's language.
    - Set self.obj_model, self.obj_id and self.lang_field to indicate that the primary language to be displayed should be taken from which model.
    
::

        # Specify that the report should be printed in object partner's language.
        if self.obj_partner and self.obj_partner.id:
            self.use_user_lang = False
            self.obj_model = 'res.partner'
            self.obj_id = self.obj_partner.id
            self.lang_field = 'lang'
        # Language
        self.lang_init(self.use_user_lang, self.obj_model, self.obj_id, self.lang_field)

- To set other options to control languages, set them in the report_languages parameter:

    - report_name: is defined in each report (currently, I name the report by its module containing it).
      For each report, we have some options:

        - dual_lang: by default, it is False. If it is True, the report will be printed in two languages with the form primary_lang (secondary_lang).
        - primary_lang: by default, the primary language is chosen by specifying parameters to lang_init function.
          If a primary_lang is given, the report will be forced to be printed in that language.
        - secondary_lang: by default, the secondary lang is controlled by the language input in the report template.
          If a secondary_lang is given, the secondary language of the report will be printed in this language.

- Note, to edit the parameter report_languages, go to Settings > Technical > Parameters > System Parameters.
- Force all Purchase Confirmation / Order reports to be printed in Vietnamese:

::

    {'trobz_report_purchase': {'primary_lang': 'vi_VN'}}

- Force all Invoice reports to be printed in dual languages:

::

    {'trobz_report_account': {'dual_lang': 1}}

- Force all Sale Confirmation / Order reports to be printed in dual languages and the primary language is French:

::

    {'trobz_report_sale': {'dual_lang': 1, 'primary_lang': 'fr_FR'}}

- Force all Packing List reports to be printed in dual languages and the secondary language is Vietnamese:

::

    {'trobz_report_sale': {'dual_lang': 1, 'secondary_lang': 'vi_VN'}}

**Partner Information**

- To get address information of the partner of the printing object, call this function in init:

::

    obj_partner_info = self.addr_get(partner_id=self.obj_partner and self.obj_partner.id or False)

- In the report template, to get full address of the above partner (street, street2, city, country...),
  you can write like this:

::

    obj_partner_info['address']

- You can do the same with bank_get to get the bank information and the same to load the printing user's partner information.

Notes for further development
=============================

- The language printed in a report will be decided based on the "lang" information in localcontext.
- The report get_object_partner_company_info is always called in common_init.
  This function will load the information of the partner of the printing object (for example, an invoice to IDW).
  This information is frequently used in reports so I make it preloaded.
- Add more useful functions to develop reports in the future.

    """,
    'website': 'http://trobz.com',
    'init_xml': [],
    "depends" : [
#         'report_aeroo', 
#         'report_aeroo_ooo',
        'trobz_base',
#         'trobz_currency_rate_update'
    ],
    'data': [
        'data/property_data.xml',
        'security/ir.model.access.csv',
#         'view/ir_actions_report_xml.xml',
    ],
    'installable': True,
    'active': False,
    'application': False,
    'post_objects': [],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
