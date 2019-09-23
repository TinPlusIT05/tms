# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2018 Trobz (<http://trobz.com>).
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
#    along with this program.  If not see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import SUPERUSER_ID
from openerp import api, models


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.multi
    @api.returns('self')
    def _filter_visible_menus(self):
        res = super(IrUiMenu, self)._filter_visible_menus()

        # Ignore SUPERUSER
        if not self.env.uid == SUPERUSER_ID:
            res = self.hidden_menu_for_profile(res)

        return res

    @api.model
    def hidden_menu_for_profile(self, menu_ids):
        """
        This function used to hide specific menus from user who has defined
            group
        """
        menu_to_hide_ids = []
# ======= Sample:
#         if current_user.has_group('group_xml_id'):
#             menu_to_hide_ids = [
#                 self.env.ref('menu_xml_id').id,
#             ]
#         elif current_user.\
#                 has_group('other_group_xml_id'):
#             menu_to_hide_ids += [
#                 self.env.ref('other_menu_xml_id').id,
#             ]

        current_user = self.env['res.users'].sudo().browse(self._uid)
        if current_user.has_group('tms_modules.group_profile_crm'):
            menu_to_hide_ids = [
                self.env.ref('trobz_base.admin_menu').id,
            ]

        return menu_ids.filtered(lambda x: x.id not in menu_to_hide_ids)
