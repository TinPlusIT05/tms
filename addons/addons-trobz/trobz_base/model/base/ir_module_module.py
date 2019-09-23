# -*- coding: utf-8 -*-
##############################################################################
from openerp import models


class ir_module_module(models.Model):
    _inherit = "ir.module.module"

    def button_upgrade(self, cr, uid, ids, context=None):
        '''
        Overwrite this function to upgrade all installed modules from Trobz
        when upgrading the module "trobz_base"
        '''
        # check whether "trobz_base" is in the list
        check_trobz_base_ids = self.search(cr, uid,
                                           [('name', '=', 'trobz_base'),
                                            ('id', 'in', ids)],
                                           context=context)
        if check_trobz_base_ids:
            # get all installed module with author "Trobz"
            all_trobz_installed_ids = self.search(cr, uid,
                                                  [('state', '=', 'installed'),
                                                   ('author', '=', 'Trobz')],
                                                  context=context)
            ids.extend(all_trobz_installed_ids)
            """
            uniquifying the ids to avoid:
                Error: "One of the records you are trying to modify has
                already been deleted (Document type: %s)"
            if exist an duplicate id in ids
            """
            ids = list(set(ids))
        return super(ir_module_module, self).button_upgrade(cr, uid, ids,
                                                            context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
