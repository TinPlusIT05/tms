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

from openerp.models import api
from openerp.models import BaseModel
from openerp.exceptions import AccessError
import logging
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
from openerp.osv import expression
import datetime

_logger = logging.getLogger(__name__)


@api.multi
def improve_error_message_record_rules(self, missing_ids, description,
                                       operation):
    """
    Show message error in friendly way
    Return a Warning with more information
    """
    raise _improve_error_message_record_rules(self, missing_ids, description,
                                              operation)


@api.multi
def _improve_error_message_record_rules(self, missing_ids, description,
                                        operation):
    """
    The main function to show message error in friendly way.
    """
    self._cr.execute('SELECT id FROM ' + self._table + ' WHERE id IN %s',
                     (tuple(missing_ids),))
    forbidden_ids = [x[0] for x in self._cr.fetchall()]
    # only show message if there are missing_ids and they're forbidden
    if missing_ids and forbidden_ids:
        # the missing ids are (at least partially)
        # hidden by access rules
        if self._uid == SUPERUSER_ID:
            return
        # Trobz: 8625, Improve the error message about "Access Right" in
        # the user interface and in the log file
        rule_ids = get_error_rule_ids_with_current_user(self, operation)
        rules = rule_names_with_rule_ids(self, rule_ids)
        rule_names = ', '.join([rule['name'] for rule in rules])

        missing_objs = self.browse(missing_ids)
        missings = missing_objs.sudo().name_get()
        missing_obj = ', '.join(['%s (id=%s)' % (missed[1], missed[0])
                                for missed in missings])

        user = self.env['res.users'].sudo().browse(self._uid)

        # log errors
        _logger.error('Access denied by ir_rules for operation: %s, '
                      'uid: %s (id=%s), model: %s',
                      operation, user.login, self._uid, self._name)
        _logger.error("- user try to access to: %s", missings)
        for rule in rules:
            _logger.error('- ir_rule implied: %s (id=%s) - %s',
                          rule['name'], rule['id'], rule['domain'])

        return AccessError(('Some security rules didn\'t allow you '
                            'to access to some records:\n'
                            '- Server time: %s\n'
                            '- Security rules: %s\n'
                            '- User: %s (id=%s)\n'
                            '- Profile Group: %s\n'
                            '- Operation: %s\n'
                            '- Model: %s\n'
                            '- Document type: %s\n'
                            '- Access Refused to: %s\n') %
                           (str(datetime.datetime.now()),
                            rule_names,
                            user.login, self._uid, user.group_profile_id.name,
                            operation, self._name,
                            description, missing_obj))


@api.model
def rule_names_with_rule_ids(self, rule_ids):
    res = []
    if rule_ids:
        rule_ids += [-1, -1]
        sql = '''
            SELECT id, name, domain_force
            FROM ir_rule
            WHERE id IN %s
        '''
        self._cr.execute(sql, (tuple(rule_ids),))
        rules = self._cr.fetchall()
        res = [{'id': x[0], 'name': x[1], 'domain': x[2]} for x in rules]
    return res


@api.multi
def check_record_rule_cause_error(self, model_name, user, rule, mode="read"):
    """
    Evaluate the rule to check whether it cause the access right error
    or not.
    This function is the combination of 2 functions:
        + domain_get
        + _check_record_rules_result_count
    """
    model_pooler = self.pool[model_name]
    global_domains = []                 # list of domains
    group_domains = {}                  # map: group -> list of domains
    rule_domain = rule.domain
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
            self._cr, SUPERUSER_ID, domain, active_test=False)
        where_clause, where_params, tables = query.where_clause, \
            query.where_clause_params, query.tables
        if where_clause:
            where_clause = ' and ' + ' and '.join(where_clause)
            self._cr.execute('SELECT ' + model_pooler._table + '.id FROM ' +
                             ','.join(tables) +
                             ' WHERE ' + model_pooler._table + '.id IN %s' +
                             where_clause,
                             ([tuple(self._ids)] + where_params))
            result_ids = [x['id'] for x in self._cr.dictfetchall()]

            ids, result_ids = set(self._ids), set(result_ids)
            missing_ids = ids - result_ids
            if missing_ids:
                # Attempt to distinguish record rule
                # restriction vs deleted records,
                # to provide a more specific error message -
                # check if the missinf
                self._cr.execute('SELECT id FROM ' + model_pooler._table +
                                 ' WHERE id IN %s', (tuple(missing_ids),))
                # the missing ids are (at least partially)
                # hidden by access rules
                if self._cr.rowcount or mode not in ('read', 'unlink'):
                    return True
    return False


@api.multi
def get_error_rule_ids_with_current_user(self, mode="read"):
    """
    Return all record rules causing the access right error.
    Loop through each rule and check whether it causes the error or not
    """
    def get_rule_ids(model_name, mode="read"):
        self._cr.execute("""
                SELECT r.id
                FROM ir_rule r
                JOIN ir_model m ON (r.model_id = m.id)
                WHERE m.model = %s
                AND r.active is True
                AND r.perm_""" + mode + """
                AND ((r.id IN (SELECT rule_group_id FROM rule_group_rel g_rel
                            JOIN res_groups_users_rel u_rel
                            ON (g_rel.group_id = u_rel.gid)
                            WHERE u_rel.uid = %s)) OR r.global)""",
                            (model_name, self._uid))

        rule_ids = [x[0] for x in self._cr.fetchall()]
        if rule_ids:
            # browse user as super-admin root to avoid access errors!
            user = self.env['res.users'].sudo().browse(self._uid)
            rule_datas = self.env['ir.rule'].browse(rule_ids)
            for rule in rule_datas:
                rule_cause_error = check_record_rule_cause_error(
                    self, model_name, user, rule, mode)
                if rule_cause_error:
                    res_ids.append(rule.id)

    if self._uid == SUPERUSER_ID:
        return []

    res_ids = []
    get_rule_ids(self._name, mode)
    # get the rules from inherited models
    for inherited_model in self._inherits:
        get_rule_ids(inherited_model, mode)
    return res_ids


@api.multi
def hook_handle_error_message(self, missing_ids, description, operation):
    """
    Hook handle error message help
    to return a Warning object with more infomation
    """
    return _improve_error_message_record_rules(self, missing_ids,
                                               self._description, 'read')


_logger.info("Monkey-patch hook_improve_error_message_record_rules function")
BaseModel.hook_improve_error_message_record_rules = \
    improve_error_message_record_rules

_logger.info("Monkey-patch hook_nicer_error_message function")
BaseModel.hook_nicer_error_message = hook_handle_error_message

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
