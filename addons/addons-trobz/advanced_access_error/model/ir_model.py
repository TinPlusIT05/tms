# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2009-2015 Trobz (http://trobz.com).
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
# -*- coding: utf-8 -*-

from openerp import models, api, tools
from openerp.models import BaseModel
from openerp.exceptions import AccessError
import logging
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)


class ir_model_access(models.Model):
    _inherit = 'ir.model.access'

    @api.model
    def adjustment_message_error_access(self, model_name, message):
        model_accesses = self.get_model_accesses(model_name)
        if model_accesses:
            message += '\n (Model Access of This Users: %s)' % \
                (', '.join(model_accesses))
            raise AccessError(message)
        return True

    @api.model
    def get_uid_groups(self):
        sql = '''
            SELECT gid
            FROM res_groups_users_rel
            WHERE uid = %s
        '''
        self._cr.execute(sql, (self._uid,))
        res = self._cr.fetchall()
        group_ids = [x[0] for x in res]
        return group_ids

    @api.model
    def get_model_accesses(self, model_name):
        group_ids = self.get_uid_groups()
        group_ids += [-1, -1]
        sql = '''
            SELECT a.name
            FROM ir_model_access a
            JOIN ir_model m ON a.model_id = m.id
            WHERE m.model = %s
            AND group_id IN %s
        '''
        self._cr.execute(sql, (model_name, tuple(group_ids)))
        exe_res = self._cr.fetchall()
        res = [x[0] for x in exe_res]
        return res

    # The context parameter is useful when the
    # method translates error messages.
    # But as the method raises an exception in that case,  the key 'lang' might
    # not be really necessary as a cache key, unless the `ormcache_context`
    # decorator catches the exception (it does not at the moment.)
    @tools.ormcache_context(accepted_keys=('lang',))
    def check(self, cr, uid, model, mode='read',
              raise_exception=True, context=None):
        if uid == 1:
            # User root have all accesses
            # TODO: exclude xml-rpc requests
            return True

        assert mode in ['read', 'write', 'create', 'unlink'], 'Invalid '
        'access mode'

        if isinstance(model, BaseModel):
            assert model._name == 'ir.model', 'Invalid model object'
            model_name = model.model
        else:
            model_name = model

        # TransientModel records have no access rights,
        # only an implicit access rule
        if model_name not in self.pool:
            _logger.error('Missing model %s' % (model_name, ))
        elif self.pool[model_name].is_transient():
            return True

        # We check if a specific rule exists
        cr.execute('SELECT MAX(CASE WHEN perm_' + mode + ' THEN 1 ELSE 0 END) '
                   '  FROM ir_model_access a '
                   '  JOIN ir_model m ON (m.id = a.model_id) '
                   '  JOIN res_groups_users_rel gu ON (gu.gid = a.group_id) '
                   ' WHERE m.model = %s '
                   '   AND gu.uid = %s '
                   '   AND a.active IS True ', (model_name, uid,)
                   )
        r = cr.fetchone()[0]

        if r is None:
            # there is no specific rule. We check the generic rule
            cr.execute('SELECT MAX(CASE WHEN perm_' + mode +
                       ' THEN 1 ELSE 0 END) '
                       '  FROM ir_model_access a '
                       '  JOIN ir_model m ON (m.id = a.model_id) '
                       ' WHERE a.group_id IS NULL '
                       '   AND m.model = %s '
                       '   AND a.active IS True ', (model_name,)
                       )
            r = cr.fetchone()[0]

        if not r and raise_exception:
            groups = '\n\t'.join('- %s' % g for g in
                                 self.group_names_with_access(cr,
                                                              model_name,
                                                              mode))
            msg_heads = {
                # Messages are declared in extenso so they are
                # properly exported in translation terms
                'read': _("Sorry, you are not allowed "
                          "to access this document."),
                'write':  _("Sorry, you are not allowed "
                            "to modify this document."),
                'create': _("Sorry, you are not allowed "
                            "to create this kind of document."),
                'unlink': _("Sorry, you are not allowed "
                            "to delete this document."),
            }
            if groups:
                msg_tail = _("Only users with the following access level "
                             "are currently allowed to do that") + \
                             ":\n%s\n\n(" + _("Document model") + ": %s)"
                msg_params = (groups, model_name)
            else:
                msg_tail = _("Please contact your system administrator "
                             "if you think this is an error.") + "\n\n(" + \
                             _("Document model") + ": %s)"
                msg_params = (model_name,)
            _logger.warning('Access Denied by ACLs for operation: %s, '
                            'uid: %s, model: %s', mode, uid, model_name)
            msg = '%s %s' % (msg_heads[mode], msg_tail)

            self.adjustment_message_error_access(cr, uid, model_name,
                                                 msg % msg_params, context)

        return bool(r)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
