# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import os
import re

from openerp.tools.translate import _
from openerp.addons.base_module_quality import base_module_quality
from openerp.modules.registry import RegistryManager


class quality_test(base_module_quality.abstract_quality_check):

    def __init__(self):
        super(quality_test, self).__init__()
        self.name = _("Object Test")
        self.note = _("""
            Test checks for fields, views, security rules, dependancy level
        """)
        self.bool_installed_only = True
        self.min_score = 40
        self.ponderation = 1
        return None

    def run_test(self, cr, uid, module_path):
        registry = RegistryManager.get(cr.dbname)
        module_name = module_path.split('/')[-1]
        obj_list = self.get_objects(cr, uid, module_name)
        model_list = self.get_new_models_of_module(cr, uid, module_name)
        new_obj_list = []
        # we should not care about Transient Model and Abstract model
        for model in model_list:
            if not registry[model].is_transient() and registry[model]._auto:
                new_obj_list.append(model)
        model_ids = self.get_model_ids(cr, uid, new_obj_list)
        result_security = {}

        # if module has no new created classes skipp fields, views, security
        # tests
        if obj_list:
            fields_obj = registry['ir.model.fields']
            view_obj = registry['ir.ui.view']
            model_access_obj = registry['ir.model.access']

            sql = "select name, substring(name from 7), module, model\
             from ir_model_data where module='%s'\
             and model='ir.model.fields';" % (module_name)
            cr.execute(sql)
            if cr.rowcount:
                module_fields = [x[0] for x in cr.fetchall()]

            field_ids = fields_obj.search(cr, uid, [('model', 'in', obj_list)])
            view_ids = view_obj.search(
                cr, uid, [('model', 'in', new_obj_list),
                          ('type', 'in', ['tree', 'form', 'search'])])
            model_access_ids = model_access_obj.search(
                cr, uid, [('model_id', 'in', model_ids)])

            fields_datas = fields_obj.browse(cr, uid, field_ids)
            view_datas = view_obj.browse(cr, uid, view_ids)
            model_access_datas = model_access_obj.browse(
                cr, uid, model_access_ids)

            result_dict = {}
            result_view = {}
            good_field = 0
            total_field = 0

            # field test .....
            for field in fields_datas:
                result_dict[field.model] = []
            for field in fields_datas:
                ttype = field.ttype
                name = field.name
                total_field += 1
                # re.compile('[a-z]+[_]?[a-z]+$')
                check_str = re.compile('[a-z]+[\w_]*$')

                if name not in module_fields:
                    continue

                if ttype == 'many2one':
                    if name.split('_')[-1] == 'id':
                        good_field += 1
                    else:
                        data = 'many2one field should end with _id'
                        result_dict[field.model].append(
                            [field.model, name, data])
                elif ttype in ['many2many', 'one2many']:
                    if name.split('_')[-1] == 'ids':
                        good_field += 1
                    else:
                        data = '%s field should end with _ids' % (ttype)
                        result_dict[field.model].append(
                            [field.model, name, data])
                elif check_str.match(name):
                    good_field += 1
                else:
                    data = 'Field name should be in lower case or it should\
                        follow python standard'
                    result_dict[field.model].append([field.model, name, data])

            # views tests
            for res in result_dict.keys():
                if not result_dict[res]:
                    del result_dict[res]

            view_dict = {}
            for new_obj in new_obj_list:
                view_dict[new_obj] = []
            total_views = len(new_obj_list) * 3
            model_views = 0

            for view in view_datas:
                ttype = view.type
                if view.model in view_dict:
                    view_dict[view.model].append(ttype)
                else:
                    view_dict[view.model] = []
                    view_dict[view.model].append(ttype)

                model_views += 1

            for model in view_dict:
                if len(view_dict[model]) < 3:
                    model_views -= 1
                    result_view[model] = [
                        model, "You should have at least form/tree/search "
                        "view of an object"]
            if model_views > total_views:
                model_views = total_views

            # security rules test...
            list_files = os.listdir(module_path)
            security_folder = False
            for file_sec in list_files:
                if file_sec == 'security':
                    path = os.path.join(module_path, file_sec)
                    if os.path.isdir(path):
                        security_folder = True
            if not security_folder:
                result_security[module_name] = [
                    module_name, "Security folder is not available (All "
                    "security rules and groups should define in "
                    "security folder)"]

            access_list = []
            good_sec = len(new_obj_list)
            bad_sec = 0
            for access in model_access_datas:
                access_list.append(access.model_id.model)

            for obj in new_obj_list:
                if obj not in access_list and not registry[obj].is_transient():
                    bad_sec += 1
                    result_security[obj] = [
                        obj, " should have at least one security "
                        "rule defined on it"]

        #  Dependency test of module
        module_obj = registry['ir.module.module']
        module_ids = module_obj.search(cr, uid, [('name', '=', module_name)])
        module_datas = module_obj.browse(cr, uid, module_ids)
        depend_list = []
        depend_check = []
        for depend in module_datas[0].dependencies_id:
            depend_list.append(depend.name)
        module_ids = module_obj.search(cr, uid, [('name', 'in', depend_list)])
        module_datas = module_obj.browse(cr, uid, module_ids)
        for module_data in module_datas:
            for check in module_data.dependencies_id:
                depend_check.append(check.name)

        bad_depend = 0  # len(remove_list)
        if not obj_list:
            # note : score is calculated based on if you have for e.g. two
            # module extra in dependancy it will score -10 out of 100
            score_depend = (100 - (bad_depend * 5)) / 100.0
            self.score = score_depend
            self.result = self.get_result({module_name: [
                                          'No object found', 'No object found',
                                          'No object found',
                                          int(score_depend * 100)]})
            self.result_details += self.get_result_general(
                result_security, name="General")
            return None

        if total_views:
            score_view = total_views and float(model_views) / float(total_views)
        else:
            # If all of new models is Transient Model or Abstract Model,
            #    set score_view = 1
            score_view = 1
        score_field = total_field and float(
            good_field) / float(total_field) or 1
        # note : score is calculated based on if you have for e.g. two module
        # extra in dependancy it will score -10 out of 100
        score_depend = (100 - (bad_depend * 5)) / 100.0
        if good_sec:
            score_security = good_sec and float(
                good_sec - bad_sec) / float(good_sec)
        else:
            # If all of new models is Transient Model or Abstract Model,
            #    set score_security = 1
            score_security = 1
        self.score = (
            score_view + score_field + score_security + score_depend) / 4
        if self.score * 100 < self.min_score:
            self.message = 'Score is below than minimal score(%s%%)'\
                % self.min_score
        self.result = self.get_result({
            module_name: [int(score_field * 100), int(score_view * 100),
                          int(score_security * 100), int(score_depend * 100)]})
        self.result_details += self.get_result_details(result_dict)
        self.result_details += self.get_result_general(
            result_view, name="View")
        self.result_details += self.get_result_general(
            result_security, name="General")
        return None

    def get_result(self, dict_obj):
        header = ('{| border="1" cellspacing="0" cellpadding="5" align="left" '
                  '\n! %-40s \n! %-40s \n! %-40s \n! %-10s \n',
                  [_('Result of fields in %'), _('Result of views in %'),
                   _('Result of Security in %'),
                   _('Result of dependancy in %')])
        if not self.error:
            return self.format_table(header, data_list=dict_obj)
        return ""

    def get_result_details(self, dict_obj):
        res = ""
        if dict_obj != {}:
            str_html = "<html><strong> Fields Result</strong><head>%s"
            "</head><body>" % (self.get_style())
            res += str_html
            header = ('<tr><th class="tdatastyle">%s</th><th '
                      'class="tdatastyle">%s</th><th class="tdatastyle">%s'
                      '</th></tr>',
                      [_('Object Name'), _('Field name'), _('Suggestion')])
            if not self.error:
                for key in dict_obj.keys():
                    data_list = []
                    final_dict = {}
                    data_list = dict_obj[key]
                    count = 0
                    for i in data_list:
                        count += 1
                        final_dict[key + str(count)] = i
                    res_str = '<table class="tablestyle">' + \
                        self.format_html_table(
                            header, data_list=final_dict) + '</table><br>'
                    res += res_str.replace('''<td''',
                                           '''<td class="tdatastyle" ''')
            return res + '</body></html>'
        return ""

    def get_result_general(self, dict_obj, name=''):
        str_html = '<html><strong> %s Result</strong><head>%s</head><body>' \
                   '<table class="tablestyle">' % (name, self.get_style())
        header = ('<tr><th class="tdatastyle">%s</th><th class="tdatastyle">'
                  '%s</th></tr>', [_('Object Name'), _('Suggestion')])
        if not self.error:
            res = str_html + \
                self.format_html_table(
                    header, data_list=dict_obj) + '</table></body></html>'
            res = res.replace('''<td''', '''<td class="tdatastyle" ''')
            return res
        return ""

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
