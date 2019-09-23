# -*- coding: utf-8 -*-
##############################################################################

from openerp.osv import fields, osv
from openerp import api
import openerp
import logging
from openerp.addons.base.res.res_users import name_boolean_group
from openerp.addons.base.res.res_users import name_selection_groups
_logger = logging.getLogger(__name__)


class res_users(osv.Model):

    def _get_default_timezone(self, cr, uid, context=None):
        '''
        Get default timezone for a user
        '''
        configure_parameter_obj = self.pool['ir.config_parameter']
        return configure_parameter_obj.get_param(cr,
                                                 uid,
                                                 'Default Timezone',
                                                 False)

    _inherit = "res.users"
    _columns = {
        'group_profile_id': fields.many2one('res.groups',
                                            string='Profile Group',
                                            domain=[('is_profile', '=', True)],
                                            help='The profile group of a user \
                                            which defines all the required \
                                            groups for a user.')
    }

    _defaults = {
        'tz': _get_default_timezone
    }

    def create(self, cr, uid, vals, context=None):
        '''
        Groups of a user are defined by "group_profile_id"
        '''

        # override the default context not to allow reset
        # password to be sent after new user is created
        context = dict(context)
        context.update({"no_reset_password": True})

        if vals.get('group_profile_id', False):
            vals['groups_id'] = [(6, 0, [vals['group_profile_id']])]
            # Insert Home Action for the user
            res_group_obj = self.pool['res.groups'].browse(
                cr, uid, vals['group_profile_id'], context)
            if res_group_obj and res_group_obj.action_id:
                vals['action_id'] = res_group_obj.action_id.id

            # Insert Home Action for the user
            res_group_obj = self.pool['res.groups'].browse(
                cr, uid, vals['group_profile_id'], context)
            if res_group_obj and res_group_obj.action_id:
                vals['action_id'] = res_group_obj.action_id.id

        return super(res_users, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context={}):
        '''
        If "group_profile_id" is updated, update the list of related groups
        '''
        if vals.get('group_profile_id', False):
            vals['groups_id'] = [(6, 0, [vals['group_profile_id']])]
            # Insert Home Action for the user
            res_group_obj = self.pool['res.groups'].browse(
                cr, uid, vals['group_profile_id'], context)
            if res_group_obj and res_group_obj.action_id:
                vals['action_id'] = res_group_obj.action_id.id

            # Update Home Action of the user
            res_group_obj = self.pool['res.groups'].browse(
                cr, uid, vals['group_profile_id'], context)
            if res_group_obj and res_group_obj.action_id:
                vals['action_id'] = res_group_obj.action_id.id

        return super(res_users, self).write(cr, uid, ids, vals, context)

    def get_company_currency_of_current_user(self, cr, uid, context=None):
        '''
        Get company currency of current logged in user
        '''
        user = self.browse(cr, uid, uid, context)
        return user and user.company_id and user.company_id.currency_id or None

    def get_company_partner_id_of_current_user(self, cr, uid, context=None):
        '''
        Get company partner id from current logged in user
        '''
        current_user = self.browse(cr, uid, uid)
        # no need to check because there is always a link
        # between company and partner
        return current_user.company_id.partner_id.id

    def make_default_manager_user(self, cr, uid, group_profile_id,
                                  login='manager', default_language='en_US'):
        '''
        Generic function to create default manager user
        '''
        res_users_obj = self.pool['res.users']
        user_ids = res_users_obj.search(cr, uid, [('login', '=', login)])
        if not user_ids:
            vals = {
                'name': 'Manager Demo User',
                'login': login,
                'password': 'manager',
                'profile_id': group_profile_id,
                'lang': default_language
            }
            res_users_obj.create(cr, uid, vals)
        return True

    def create_users(self, cr, uid, user_list):
        '''
        Generic function to create users for a project
        '''
        _logger.info("Start creating users...")
        group_obj = self.pool['res.groups']
        user_obj = self.pool['res.users']
        for user in user_list:
            existing_user = self._get_all_users_ids_by_logins(
                cr, uid, [user['login']])

            g_profile_name = user['group_profile_name']
            g_profile_ids = group_obj.search(cr,
                                             uid,
                                             [('name', '=', g_profile_name),
                                              ('is_profile', '=', True)])
            if not g_profile_ids:
                _logger.warning(
                    'The group profile %s does not exist'
                    % user['group_profile_name'])
                continue
            if len(existing_user) == 0:
                user_obj.create(cr, uid, {'name': user['name'],
                                          'login': user['login'],
                                          'password': user['password'],
                                          'group_profile_id': g_profile_ids[0]}
                                )
            else:
                user_obj.write(cr,
                               uid,
                               existing_user,
                               {'group_profile_id': g_profile_ids[0]})
        _logger.info("Finish creating users...")
        return True

    def has_groups(self, cr, uid, group_ext_ids):
        """Checks whether user belongs to given groups.

        :param list group_ext_ids: list of external IDs (XML IDs) of the groups
           Must be provided in fully-qualified form (``module.ext_id``),
           as there is no implicit module to use..
        :return: True if the current user is a member of the groups else False.
        """
        if not group_ext_ids:
            return False
        if not isinstance(group_ext_ids, list):
            group_ext_ids = [group_ext_ids]
        for group_ext_id in group_ext_ids:
            if self.has_group(cr, uid, group_ext_id):
                return True
        return False

    @api.multi
    def _is_admin(self):
        res = self.id == openerp.SUPERUSER_ID or \
            self.sudo(self).has_group('base.group_erp_manager') or \
            self.sudo(self).has_group('trobz_base.group_configure_user')
        return res

    def fields_get(self, cr, uid, allfields=None, context=None,
                   write_access=True, attributes=None):
        res = super(res_users, self).fields_get(
            cr, uid, allfields, context, write_access, attributes)
        # add reified groups fields
        if not self.pool['res.users']._is_admin(cr, uid, [uid]):
            return res
        for app, kind, gs in self.pool['res.groups'].\
                get_groups_by_application(cr, uid, context):
            if kind == 'selection':
                # selection group field
                tips = ['%s: %s' % (g.name, g.comment)
                        for g in gs if g.comment]
                res[name_selection_groups(map(int, gs))] = {
                    'type': 'selection',
                    'string': app and app.name or _('Other'),
                    'selection': [(False, '')] + [(g.id, g.name) for g in gs],
                    'help': '\n'.join(tips),
                    'exportable': False,
                    'selectable': False,
                }
            else:
                # boolean group fields

                for g in gs:
                    res[name_boolean_group(g.id)] = {
                        'type': 'boolean',
                        'string': g.name,
                        'help': g.comment,
                        'exportable': False,
                        'selectable': False,
                    }
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
