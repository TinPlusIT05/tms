# -*- coding: utf-8 -*-
##############################################################################

from openerp.osv import fields, osv, expression
from openerp.tools.translate import _
from lxml import etree
from lxml.builder import E
from openerp.addons.base.res.res_users import name_boolean_group
from openerp.addons.base.res.res_users import name_selection_groups
from openerp import SUPERUSER_ID, api


class res_groups(osv.Model):

    def check_recursive(self, cr, uid, ids, path=None, context=None):
        if not context:
            context = {}
        if not path:
            path = []
        res_groups = self.browse(cr, uid, ids, context)
        for res_group in res_groups:
            branch_path = path[:]
            branch_path.append(res_group.id)
            implied_ids = [
                implied_group.id for implied_group in res_group.implied_ids]
            if (set(branch_path).intersection(set(implied_ids))):
                return False
            check_implied_group = self.check_recursive(
                cr, uid, implied_ids, path=branch_path, context=context)
            if not check_implied_group:
                return False
        return True

    _inherit = "res.groups"

    _columns = {
        'is_profile': fields.boolean(
            string='Is Profile Group',
            help='Check this if you want this group become a Profile Group.'),
        'action_id': fields.many2one(
            'ir.actions.actions', 'Default Home Action',
            help="If specified, this action will be opened at log on "
            "for this user, in addition to the standard menu."),
        'test_model_id': fields.many2one('ir.model', 'Test Model'),
        'test_user_id': fields.many2one(
            'res.users', 'Test User',
            domain="[('group_profile_id', '=', id)]"),
        'test_record_id': fields.integer('Test Record ID'),
        'read_access': fields.boolean('Read Access'),
        'create_access': fields.boolean('Create Access'),
        'write_access': fields.boolean('Write Access'),
        'delete_access': fields.boolean('Delete Access'),
        'profile_ids': fields.many2many(
            'res.groups', 'res_groups_implied_rel', 'hid', 'gid')
    }

    _constraints = [
        (check_recursive, 'Cannot have recursive implied groups!',
         ['implied_ids']),
    ]

    _defaults = {
        'is_profile': False
    }

    def write(self, cr, uid, ids, vals, context=None):
        if 'implied_ids' in vals:
            new_implied_ids = []
            tmp_implied_ids = vals.get('implied_ids', [])
            for implied_group_id in tmp_implied_ids:
                if isinstance(implied_group_id, int):
                    new_implied_ids = tmp_implied_ids
                    break
                elif len(implied_group_id) == 3:
                    new_implied_ids.extend(implied_group_id[2])
                elif len(implied_group_id) == 2:
                    new_implied_ids.extend([implied_group_id[1]])
            self.update_user_group_link(cr, uid, ids, new_implied_ids)

        res = super(res_groups, self).write(
            cr, uid, ids, vals, context=context)

        return res

    def update_user_group_link(self, cr, uid, ids, new_implied_ids):
        group_recs = self.browse(cr, uid, ids)
        for group_rec in group_recs:
            # Get all IDs of Old implied_ids
            old_implied_ids = self.get_list_from_list_browse(
                cr, uid, group_rec.implied_ids)
            # Remove inherit Group
            if len(new_implied_ids) < len(old_implied_ids):
                users = self.get_list_from_list_browse(
                            cr, uid, group_rec.users)
                for old_implied_id in old_implied_ids:
                    # Implied group is removed
                    if old_implied_id not in new_implied_ids:
                        # Get all users of old implied group
                        old_gr_rec = self.browse(cr, uid, old_implied_id)
                        old_gr_users = self.get_list_from_list_browse(
                                cr, uid, old_gr_rec.users)

                        # copy new instance of old_group_users
                        new_old_grp_users = old_gr_users[:]
                        # Remove users of implied group is removed

                        for item in old_gr_users:
                            if item != SUPERUSER_ID and item in users:
                                new_old_grp_users.remove(item)
                        # get all implied_ids of current old_implied_id
                        implied_ids = map(int, old_gr_rec.trans_implied_ids)
                        # reset users for all the groups which
                        # were removed the group from list of inherit groups
                        implied_ids.append(old_implied_id)
                        self.write(
                            cr, uid, implied_ids,
                            {'users': [(4, group_id) for group_id in new_old_grp_users]})
        return True

    def get_list_from_list_browse(self, cr, uid, list_browse):
        rs = []
        for item in list_browse:
            rs.append(item.id)

        return rs

    def update_user_groups_view(self, cr, uid, context=None):
        '''
        This function is almost the same with the function in original module,
        except the part that we always set attrs Readonly to True for all
        groups. So that list of groups for a user is always get from Profile
        Group
        '''
        view = self.pool['ir.model.data'].xmlid_to_object(
            cr, SUPERUSER_ID, 'base.user_groups_view', context=context)
        if view and view.exists() and view._name == 'ir.ui.view':
            xml1, xml2 = [], []
            xml1.append(E.separator(string=_('Application'), colspan="4"))
            for app, kind, gs in self.get_groups_by_application(cr, uid,
                                                                context):
                # hide groups in category 'Hidden' (except to group_no_one)
                # Trobz: all groups here should be readonly and based on
                # profile
                attrs = {'readonly': '1'}
                if kind == 'selection':
                    # application name with a selection field
                    field_name = name_selection_groups(map(int, gs))
                    xml1.append(E.field(name=field_name, **attrs))
                    xml1.append(E.newline())
                else:
                    # application separator with boolean fields
                    app_name = app and app.name or _('Other')
                    xml2.append(
                        E.separator(string=app_name, colspan="4", **attrs))
                    for g in gs:
                        field_name = name_boolean_group(g.id)
                        xml2.append(E.field(name=field_name, **attrs))

            xml = E.field(*(xml1 + xml2), name="groups_id", position="replace")
            xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY GROUPS"))
            xml_content = etree.tostring(
                xml, pretty_print=True, xml_declaration=True, encoding="utf-8")
            view.write({'arch': xml_content})
        return True

    @api.model
    def make_default_manager_groups(self,exclude_groups=[],
            profile_group_name='Functional Administrator'):
        except_groups = ['Administration / Settings',
                         'Administration / Access Rights',
                         'Portal', 'Public', 'Anonymous',
                         'Usability / Technical Features',
                         'Technical Settings / View Online Payment Options'
                         ]
        except_groups = except_groups + exclude_groups

        profile_group_rec = None
        manager_group_recs = self.search(
            [('full_name', 'not in', except_groups),
             ('is_profile', '=', False)],
            order='id')
        # Exclude technical groups
        technical_groups = self.search([('category_id.name', '=',
                                         'Technical Settings')])
        manager_group_recs = manager_group_recs - technical_groups
        manager_group_ids = manager_group_recs and manager_group_recs.ids or []
        demo_profile_recs = self.search([('name', '=', profile_group_name),
                                         ('is_profile', '=', True)])
        profile_categ = self.env.ref('trobz_base.module_category_profile')
        if not demo_profile_recs:
            vals = {
                'name': profile_group_name,
                'implied_ids': [(6, 0, manager_group_ids)],
                'is_profile': True,
                'category_id': profile_categ.id,
            }
            profile_group_rec = self.create(vals)
        else:
            for demo_profile_rec in demo_profile_recs:
                if 'implied_ids' in demo_profile_rec:
                    '''
                        Becareful when you select demo_profile.implied_ids.ids
                        In this case, we select (search) groups by name (above)
                        so that we have all of groups and
                        demo_profile.implied_ids.ids will render all of
                        group_ids which we want.
                    '''
                    implied_ids = sorted(demo_profile_rec.implied_ids.ids)
                    if implied_ids != manager_group_ids:
                        vals = {
                            'implied_ids': [(6, 0, manager_group_ids)],
                            'category_id': profile_categ.id
                        }
                        demo_profile_rec.write(vals)
                        profile_group_rec = demo_profile_rec
        return profile_group_rec

    def get_groups(self, cr, uid, ids, context={}):
        """
        8077: Adjust the "Profile" form view to help
        to check access right quickly
        Add more some functions:
         + get_groups.
         + show_related_model_access
         + show_related_rule
        """
        if isinstance(ids, (long, int)):
            ids = [ids]

        sql = '''
            SELECT gid
            FROM res_groups_users_rel
            WHERE uid IN
            (
                SELECT id
                FROM res_users
                WHERE group_profile_id = %s
                Limit 1
            )
        '''
        cr.execute(sql, (ids[0],))
        res = cr.fetchall()
        group_ids = [x[0] for x in res]
        if group_ids:
            return group_ids

        # When there is no user for this profile
        profile_data = self.read(cr, uid, ids[0], context=context)
        group_ids = profile_data['groups_ids'] + [-1, -1]
        sql = '''
             SELECT hid
             FROM res_groups_implied_rel
             WHERE gid IN %s
        '''
        cr.execute(sql, (tuple(group_ids),))
        res = cr.fetchall()
        group_ids2 = [x[0] for x in res]
        return group_ids + group_ids2

    def show_related_model_access(self, cr, uid, ids, context={}):
        context = context or {}
        access_pool = self.pool['ir.model.access']
        group_ids = self.get_groups(cr, uid, ids, context)
        args = [('group_id', 'in', group_ids)]
        if context.get('model_id'):
            args.append(('model_id', '=', context['model_id']))
        access_ids = access_pool.search(cr, uid, args, context=context)

        if context.get('get_ids'):
            return access_ids
        return {
            'domain': [('id', 'in', access_ids)],
            'name': _('Related Model Access'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'ir.model.access',
            'type': 'ir.actions.act_window',
            'context': context,
        }

    # Because check_access_rule function always raise warning when not passing
    # checking, so we need to create another function to return result
    def profile_check_record_rules_result_count(self, cr, check_uid, ids,
                                                result_ids, operation,
                                                model_pooler, context=None):
        """Verify the returned rows after applying record rules matches
           the length of `ids`, and raise an appropriate exception
           if it does not.
        """
        ids, result_ids = set(ids), set(result_ids)
        missing_ids = ids - result_ids
        if missing_ids:
            # Attempt to distinguish record rule restriction vs deleted records
            # to provide a more specific error message - check if the missing
            cr.execute(
                'SELECT id FROM ' + model_pooler._table + ' WHERE id IN %s',
                (tuple(missing_ids),)
            )
            # the missing ids are (at least partially) hidden by access rules
            if not cr.rowcount and operation in ('read', 'unlink'):
                # No need to warn about deleting an already deleted record.
                # And no error when reading a record that was deleted,
                # to prevent spurious
                # errors for non-transactional search/read sequences coming
                # from clients
                return True
            return False
        return True

    def profile_check_access_rule(self, cr, check_uid, ids, operation,
                                  model_pooler, context=None):
        """Verifies that the operation given by ``operation``
            is allowed for the user according to ir.rules.
           :param operation: one of ``write``, ``unlink``
           :raise except_orm: * if current ir.rules do not
               permit this operation.
           :return: rule_name
        """
        if check_uid == SUPERUSER_ID:
            return True

        if model_pooler.is_transient():
            # Only one single implicit access rule for transient models: owner only!
            # This is ok to hardcode because we assert that TransientModels always
            # have log_access enabled so that the create_uid column is always there.
            # And even with _inherits, these fields are always present in the local
            # table too, so no need for JOINs.
            cr.execute("""SELECT distinct create_uid
                          FROM %s
                          WHERE id IN %%s""" % model_pooler._table, (tuple(ids),))
            uids = [x[0] for x in cr.fetchall()]
            if len(uids) != 1 or uids[0] != check_uid:
                return False
        else:
            where_clause, where_params, tables = self.pool.get('ir.rule').domain_get(
                cr, check_uid, model_pooler._name, operation, context=context)

            if where_clause:
                where_clause = ' and ' + ' and '.join(where_clause)
                cr.execute('SELECT ' + model_pooler._table + '.id FROM ' + ','.join(tables) + 
                           ' WHERE ' + model_pooler._table + 
                           '.id IN %s' + where_clause,
                           ([tuple(ids)] + where_params))
                returned_ids = [x['id'] for x in cr.dictfetchall()]
                check_rs = self.profile_check_record_rules_result_count(
                    cr, check_uid, ids, returned_ids, operation, model_pooler, context=context)
                return check_rs

        return True

    def get_rule_ids(self, cr, uid, ids, check_uid, model_name, mode="read"):
        if check_uid == SUPERUSER_ID:
            return []
        res_ids = []
        model_pooler = self.pool[model_name]
        cr.execute("""
                SELECT r.id
                FROM ir_rule r
                JOIN ir_model m ON (r.model_id = m.id)
                WHERE m.model = %s
                AND r.active is True
                AND r.perm_""" + mode + """
                AND (r.id IN (SELECT rule_group_id FROM rule_group_rel g_rel
                            JOIN res_groups_users_rel u_rel ON (g_rel.group_id = u_rel.gid)
                            WHERE u_rel.uid = %s) OR r.global)""", (model_name, check_uid))
        rule_ids = [x[0] for x in cr.fetchall()]
        if rule_ids:
            # browse user as super-admin root to avoid access errors!
            user = self.pool['res.users'].browse(cr, SUPERUSER_ID, check_uid)
            rule_datas = self.pool['ir.rule'].browse(cr, SUPERUSER_ID,
                                                     rule_ids)
            for rule in rule_datas:
                global_domains = []  # list of domains
                # map: group -> list of domains
                group_domains = {}
                # read 'domain' as UID to have the correct eval context for the
                # rule.
                rule_domain = rule.domain
#                rule_domain = rule_domain['domain']
                dom = expression.normalize_domain(rule_domain)
                for group in rule.groups:
                    if group in user.groups_id:
                        group_domains.setdefault(group, []).append(dom)
                if not rule.groups:
                    global_domains.append(dom)
                # combine global domains and group domains
                if group_domains:
                    group_domain = expression.OR(map(expression.OR,
                                                     group_domains.values()))
                else:
                    group_domain = []
                domain = expression.AND(global_domains + [group_domain])
                if domain:
                    # _where_calc is called as superuser. This means that rules can
                    # involve objects on which the real uid has no acces rights.
                    # This means also there is no implicit restriction (e.g. an object
                    # references another object the user can't see).
                    query = self.pool.get(model_name)._where_calc(
                        cr, SUPERUSER_ID, domain, active_test=False)
                    where_clause, where_params, tables = query.where_clause, query.where_clause_params, query.tables
                    if where_clause:
                        where_clause = ' and ' + ' and '.join(where_clause)
                        cr.execute('SELECT ' + model_pooler._table + '.id FROM ' + ','.join(tables) + 
                                   ' WHERE ' + model_pooler._table + 
                                   '.id IN %s' + where_clause,
                                   ([tuple(ids)] + where_params))
                        returned_ids = [x['id'] for x in cr.dictfetchall()]
                        check_rs = self.profile_check_record_rules_result_count(
                            cr, check_uid, ids, returned_ids, mode, model_pooler, context={})
                        if not check_rs:
                            res_ids.append(rule.id)
        return res_ids

    def check_model(self, cr, uid, ids, context={}):
        if isinstance(ids, (long, int)):
            ids = [ids]
        profile_data = self.browse(cr, uid, ids[0])
        msg = []
        if len(profile_data.users) < 2:
            msg.append(_('Only user Administrator belongs to this group.'
                         ' Cannot test.'))
        elif not profile_data.test_model_id:
            msg.append(_('Please set value for "Test Model"!'))
        elif not profile_data.test_record_id and (profile_data.read_access or profile_data.write_access or profile_data.delete_access):
            msg.append(_('Please set value for "Test Record ID"!'))
        else:
            model_pooler = self.pool[profile_data.test_model_id.model]
            check = True

            # check if the test record id is exist or not.
            if (profile_data.read_access or profile_data.write_access or profile_data.delete_access):
                test_record = model_pooler.search(
                    cr, uid, [('id', '=', profile_data.test_record_id)])
                if not test_record:
                    msg.append(_('"Test Record ID" does not exist!'))
                    check = False

            if check:
                access_pool = self.pool['ir.model.access']
                rule_pool = self.pool['ir.rule']
                check_uid = profile_data.users[1].id
                check_username = profile_data.users[1].name
                if profile_data.test_user_id:
                    check_uid = profile_data.test_user_id.id
                    check_username = profile_data.test_user_id.name
                access_ids = self.show_related_model_access(cr, uid, ids, {
                    'get_ids': True,
                    'model_id': profile_data.test_model_id.id
                })
                access_names = access_pool.name_get(
                    cr, uid, access_ids, context=context)
                access_name_arr = [x[1] for x in access_names]
                access_name_str = ', '.join(access_name_arr)

                check_list = []
                # Check Read access
                if profile_data.read_access:
                    check_list.append('read')

                if profile_data.create_access:
                    check_list.append('create')

                if profile_data.write_access:
                    check_list.append('write')

                if profile_data.delete_access:
                    check_list.append('unlink')

                if not check_list:
                    msg.append(_('Please set the access right to check!'))
                else:
                    can_do = []
                    cannot_do_rule = {}
                    cannot_do_access = {}
                    for operation in check_list:
                        check_access = model_pooler.check_access_rights(
                            cr, check_uid, operation, raise_exception=False)
                        if check_access:
                            # Check access rule
                            rule_check = self.profile_check_access_rule(
                                cr, check_uid, [profile_data.test_record_id],
                                operation, model_pooler, context)
                            if rule_check:
                                can_do.append(operation)

                            else:
                                rule_ids = self.get_rule_ids(
                                    cr, uid, [profile_data.test_record_id],
                                    check_uid, profile_data.test_model_id.model,
                                    operation)
                                rule_names = rule_pool.name_get(
                                    cr, uid, rule_ids, context=context)
                                rule_name_arr = [x[1] for x in rule_names]
                                rule_name_str = ', '.join(rule_name_arr)
                                if rule_name_str not in cannot_do_rule:
                                    cannot_do_rule[rule_name_str] = [operation]
                                else:
                                    cannot_do_rule[
                                        rule_name_str].append(operation)

                        else:
                            # Seek for all access right
                            # for this profile on this model
                            if not access_ids:
                                if 'there is no access right defined' not in cannot_do_access:
                                    cannot_do_access[
                                        'there is no access right defined'] = [operation]
                                else:
                                    cannot_do_access[
                                        'there is no access right defined'].append(operation)

                            else:
                                if access_name_str not in cannot_do_access:
                                    cannot_do_access[
                                        access_name_str] = [operation]
                                else:
                                    cannot_do_access[
                                        access_name_str].append(operation)

                    if can_do:
                        msg.append(_('This test user (id=%s, name=%s) can %s record %s of the model %s') % 
                                    (check_uid, check_username,
                                     ', '.join(can_do),
                                     profile_data.test_record_id,
                                     profile_data.test_model_id.name))

                    for rule_str, oper in cannot_do_rule.items():
                        msg.append(_('This test user (id=%s, name=%s) can not %s record %s of the model %s because of Record Rules: %s') % 
                                    (check_uid, check_username,
                                     ', '.join(oper),
                                     profile_data.test_record_id,
                                     profile_data.test_model_id.name,
                                     rule_str))

                    for access_str, oper in cannot_do_access.items():
                        msg.append(_('This test user (id=%s, name=%s) can not %s record %s of the model %s because of Model Access: %s') % 
                                    (check_uid, check_username,
                                     ', '.join(oper),
                                     profile_data.test_record_id,
                                     profile_data.test_model_id.name,
                                     access_str))

        if msg:
            msg = ' - ' + '\n - '.join(msg)
            raise osv.except_osv(_('Announce'), msg)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
