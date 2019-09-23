# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp import SUPERUSER_ID


class ir_ui_menu(models.Model):
    _inherit = 'ir.ui.menu'

    invisible_groups_ids = fields.Many2many(
        'res.groups',
        'ir_ui_menu_invi_group_rel',
        'menu_id', 'gid', 'Invisible Groups',
        help="If you have groups, the invisibility "
             "of this menu will be based on these groups.")

    @api.multi
    @api.returns('self')
    def _filter_visible_menus(self):
        """ Filter `self` to only keep the menu items that should be visible in
            the menu hierarchy of the current user.
            Uses a cache for speeding up the computation.
        """
        with self._menu_cache_lock:
            visible = super(ir_ui_menu, self)._filter_visible_menus()
            groups = self.env.user.groups_id
            if self.env.user.id != SUPERUSER_ID:
                visible = [menu for menu in visible
                           if not any(group in groups
                                      for group in menu.invisible_groups_ids)]
            return self.filtered(lambda menu: menu in visible)