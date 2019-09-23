# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import amount_to_text_vn
import ir_cron
import trobz_base
import res_users
import res_groups
import ir_module_module

############################################
# Trobz Upgrade module Monkey-Pack Section #
############################################
from openerp.addons.base.module import module
from openerp.tools.config import config
import logging
_logger = logging.getLogger(__name__)


def trobz_button_upgrade(self, cr, uid, ids, context=None):
    '''
    Overwrite this function to upgrade all installed modules from Trobz
    when upgrading the module "trobz_base"
    '''
    _logger.info("Trobz_button_upgrade is proccessing.........")
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

    _logger.info("Trobz_button_upgrade ids of modules "
                 "that need to upgrade: %s" % ids)

    _logger.info("Trobz_button_upgrade call native "
                 "native_button_upgrade...")
    # call super
    native_button_upgrade(self, cr, uid, ids, context)

"""
# if exist trobz_base in update of config, override native button_upgrade
# by trobz_button_upgrade to upgrade all trobz_modules
"""
if 'trobz_base' in config['update']:
    _logger.info("Override button_upgrade by trobz_button_upgrade")
    # get native button_upgrade from Odoo
    native_button_upgrade = getattr(module.module, 'button_upgrade')
    # set trobz_button_upgrade as default upgrade function of base
    setattr(module.module, 'button_upgrade', trobz_button_upgrade)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
