# -*- coding: utf-8 -*-
{
    "name": 'Web Hide Export',
    "version": "0.1",
    "author": "Trobz",
    'website': 'http://www.trobz.com',
    "category": 'web',
    "description":"""
=====================================================
Hide / Show export button in list view based on group
=====================================================
+ This module allows to hide export button (on the sidebar) from 
  native openerp based on user groups and permission validation.

+ Openerp currently support 4 user access rights (read, write, unlink, delete), 
  can be easily check on "ir.model.access". Now you will have the fifth one 
  called "export" after installing this module.

+ How to use:

  - Just have to add another item in list of access rights in "create_model_access_rights" 
    function that is used to setup user access right for each project (security_set_up.py)

  - If "export" is set to True for a group, the users from that group can see button "Export".
    the setting for "export" is optional, it's True by default incase no permission is set for it.

  - Example:
    def create_model_access_rights(self, cr, uid, context=None):
        MODEL_ACCESS_RIGHTS = {

            ('sale.order'): { (group_name): [1, 1, 1, 1, 0] },

            ('purchase.order'): { (group_name): [1, 1, 1, 1] },
        }

        return super(super, self).create_model_access_rights(cr, uid, MODEL_ACCESS_RIGHTS, context=context)

""",
    "depends": ['web_unleashed', 'trobz_base'],
    "js": [
        # models
        'static/src/js/models/user.js',
        
        # others
        'static/src/js/view_list.js',
    ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
