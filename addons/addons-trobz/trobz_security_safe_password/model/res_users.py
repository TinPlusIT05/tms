# -*- coding: utf-8 -*-
import re
from openerp.osv import osv
from openerp.osv.osv import except_osv
from openerp.tools.translate import _
try:
    import cracklib
except ImportError:
    import crack as cracklib

from openerp.tools.safe_eval import safe_eval


class res_users(osv.osv):
    _inherit = "res.users"

    def change_password(self, cr, uid, old_passwd, new_passwd, context=None):
        """
        """
        if new_passwd:
            self.validate_pw(cr, uid, new_passwd)
            return super(res_users, self).change_password(
                cr, uid, old_passwd, new_passwd, context=context)

    def validate_pw(self, cr, uid, value):
        length_pw = self.pool.get('ir.config_parameter').get_param(
            cr, uid, 'length_password', 'False')
        length_pw = int(length_pw)
        if value:
            if len(value) < length_pw:
                raise except_osv(
                    _("Change Password"),
                    _("Password must have at least %s characters.") %
                    (length_pw,))
            if not (re.search(r'[A-Z]', value) and
                    re.search(r'[a-z]', value) and
                    re.search(r'\d', value)):
                raise except_osv(_("Change Password"),
                                 _("Password must have: <br/>"
                                   "- At least one letter in lower case,<br/>"
                                   "- At least one letter in upper case,<br/>"
                                   "- At least one number."))

        use_cracklib = self.pool.get('ir.config_parameter').get_param(
            cr, uid, 'password_check_cracklib', 'False')
        if safe_eval(use_cracklib):
            try:
                cracklib.VeryFascistCheck(value)
            except ValueError, ve:
                # TODO: Get translations from
                # https://translations.launchpad.net/ubuntu/precise/+source/cracklib2/+pots/cracklib

                raise except_osv(_(" "), _(ve))
        return True

res_users()
