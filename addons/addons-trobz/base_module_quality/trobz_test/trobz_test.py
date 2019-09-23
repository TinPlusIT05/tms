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

    ERP_SECTIONS = (
        'account', 'base', 'hr', 'mail', 'mrp', 'pos', 'product',
        'purchase', 'reporting', 'sale', 'stock', 'setting')
    TROBZ_MODULE_STRUCTURE_FOLDERS = (
        'data', 'data_test', 'i18n', 'menu', 'security', 'controllers',
        'model', 'view', 'wizard', 'workflow', 'report', 'views')
    IGNORED_FILES = ('static', '__init__.py', '__init__.pyc')

    def __init__(self):
        super(quality_test, self).__init__()
        self.name = _("Trobz Test")
        self.note = _("This test checks if the module satisfies the current\
                        coding standards at Trobz.")
        self.bool_installed_only = False
        self.ponderation = 1
        self.result_dict = {}
        self.feel_good_factor = 0
        self.feel_bad_factor = 0
        return None

    def get_module_new_views(self, cr, module_name):
        sql = """
            SELECT imd.name, iuv.model, iuv.inherit_id, iuv.type
            from ir_model_data imd
            join ir_ui_view iuv on iuv.id = imd.res_id
            where imd.module='%s'
             and imd.model='ir.ui.view';
        """
        sql = sql % (module_name)

        cr.execute(sql)
        module_new_views = []
        if cr.rowcount:
            module_new_views = [
                {'name': x[0], 'model':x[1], 'inherit_id':x[2], 'type':x[3]}
                for x in cr.fetchall()]
        return module_new_views

    def _set_project_sections(self, cr, uid):
        project_specific_sections = eval(self.registry['ir.config_parameter'].
                                         get_param(cr, uid,
                                                   'project_specific_sections',
                                                   '[]'))
        self.ERP_SECTIONS = self.ERP_SECTIONS + \
            tuple(project_specific_sections)

    def _report_issue(self, message):
        self.feel_bad_factor += 1
        self.result_dict[self.feel_bad_factor] = [
            self.feel_bad_factor, message]

    def _get_code_files(self, module_path, list_files):

        # TODO: Give the possibility to include custom section per module:
        # What I have in mind is to create a ir.config_parameter
        # key=bmq_module_name
        # value={$custom_config_1 :aaa,$custom_config_2:bbbb}
        code_files = {}
        for filename in list_files:
            if filename in self.IGNORED_FILES:
                continue
            path = os.path.join(module_path, filename)
            if os.path.isdir(path):
                if filename in self.TROBZ_MODULE_STRUCTURE_FOLDERS:
                    self.feel_good_factor += 1
                    for filename2 in os.listdir(path):
                        if filename2 in self.IGNORED_FILES:
                            continue
                        path2 = os.path.join(module_path, filename, filename2)
                        if os.path.isdir(path2):
                            if filename2 in self.ERP_SECTIONS:
                                self.feel_good_factor += 1
                            else:
                                self.feel_bad_factor += 1
                                key = '%s - section name' %\
                                    self.feel_bad_factor
                                self.result_dict[key] = [key, 'The folder %s \
                                has an unexpected name for a section, only one\
                                of those should be present: "%s".' % (
                                    path2, ', '.join(self.ERP_SECTIONS))]
                            for filename3 in os.listdir(path2):
                                if filename3 in self.IGNORED_FILES:
                                    continue
                                path3 = os.path.join(path2, filename3)
                                if filename3[-4:] not in ['.pyc', '.~1~']:
                                    code_files[filename3] = {
                                        'type': filename, 'path': path3}
                        else:
                            if filename2[-4:] != '.pyc':
                                code_files[filename2] = {
                                    'type': filename, 'path': path2}
                else:
                    err_msg = 'The folder %s has an unexpected name, only one '
                    'of those should be present: "%s"'\
                        % (filename,
                           ', '.join(self.TROBZ_MODULE_STRUCTURE_FOLDERS))
                    self._report_issue(err_msg)

            elif filename not in ('__openerp__.py', '__init__.py',
                                  '__openerp__.pyc', '__init__.pyc'):
                self._report_issue(
                    "The module root should contain only the __openerp__.py "
                    "and __init__.py files, Found: %s" % (filename))

        return code_files

    def _check_file_names_and_content(self, code_files,
                                      all_installed_model_list):
        '''CHECK FILE NAMES AND CONTENT
        '''
        DATA_FILE_EXCEPTION = (
            'company.xml', '__init__.py', 'amount_to_text_en.py',
            'amount_to_text_vn.py', 'object_proxy.py')
        for filename in code_files:
            if code_files[filename]['type'] in ('data', 'data_test')\
                    and filename not in DATA_FILE_EXCEPTION\
                    and filename.find('.png') == -1:
                if filename[-9:] in ('_data.xml', '_data.csv') or\
                        filename[:11] == 'post_object':
                    self.feel_good_factor += 1
                else:
                    self._report_issue('A data file name should end with '
                                       '_data.xml (exception: %s). Found: %s'
                                       % (', '.join(DATA_FILE_EXCEPTION),
                                          code_files[filename]['path']))

            elif code_files[filename]['type'] in ('menu'):
                if filename[-9:] == '_menu.xml':
                    self.feel_good_factor += 1
                else:
                    self._report_issue('A menu file name should end with '
                                       '_menu.xml. Found: %s' %
                                       (code_files[filename]['path']))

                include_section = False
                for section in self.ERP_SECTIONS:
                    if filename.find(section) > -1:
                        include_section = True
                        break
                if include_section:
                    self.feel_good_factor += 1
                else:
                    self._report_issue('A menu file name should contain a '
                                       'section name (%s). Found: %s'
                                       % (', '.join(self.ERP_SECTIONS),
                                          code_files[filename]['path']))

            elif code_files[filename]['type'] in ('model'):
                model_name = filename[0:-3]
                model_dot_name = model_name.replace('_', '.')
                if model_dot_name in all_installed_model_list:
                    self.feel_good_factor += 1
                    model_file = open(code_files[filename]['path'], 'r')
                    for line in model_file:
                        if line.find('class ') > -1 and (line.find(
                                'osv.osv') > -1 or line.find(
                                'models.Model') > -1 or line.find(
                                    'models.TransientModel') > -1):
                            # class trobz_maintenance_contract(osv.osv):
                            class_name = line[6:line.find('(')].strip()
                            if class_name == model_name:
                                self.feel_good_factor += 1
                            else:
                                self._report_issue('class name (found: %s) and\
                                 file name (found: %s) should be the same.\
                                 Found: %s' % (class_name,
                                               model_name,
                                               code_files[filename]['path']))

                        if line.find('    _name') > -1:
                            if line.find('\''):
                                line = line.replace('\'', '')
                            if line.find('\"'):
                                line = line.replace('\"', '')
                            real_model_name = line[line.find('=') + 2:].strip()
                            if real_model_name == model_dot_name:
                                self.feel_good_factor += 1
                            else:
                                self._report_issue('model name (found: %s) and\
                                file name (found: %s) should be the same.\
                                Found: %s' % (real_model_name,
                                              model_dot_name,
                                              code_files[filename]['path']))
                elif filename not in DATA_FILE_EXCEPTION:
                    self._report_issue(
                        'A model file name should have a name of the form\
                         model_name.py. No model found with the name\
                          "%s"' % model_dot_name)

            elif code_files[filename]['type'] in ('view'):
                if filename[-9:] == '_view.xml':
                    self.feel_good_factor += 1
                else:
                    self._report_issue('A view file name should end with\
                     _view.xml. Found: %s' % (code_files[filename]['path']))

    def _check_view_ids(self, cr, uid, module_name):
        '''CHECK VIEW IDS
        '''

        module_new_models = self.get_new_models_of_module(cr, uid, module_name)
        module_new_views = self.get_module_new_views(cr, module_name)

        view_dict = {}
        model_views = 0
        view_obj = self.registry['ir.ui.view']

        view_ids = view_obj.search(cr, uid, [(
            'model', 'in', module_new_models), ('type', 'in', ['tree',
                                                               'form',
                                                               'search'])])
        view_data = view_obj.browse(cr, uid, view_ids)
        for view in view_data:
            if view.model in view_dict:
                view_dict[view.model].append(
                    {'type': view.type, 'name': view.name})
            else:
                view_dict[view.model] = []
                view_dict[view.model].append(
                    {'type': view.type, 'name': view.name})
            model_views += 1

        for model in view_dict:
            # TODO: we should handle the models of type wizard in the future
            if model not in ('trobz.update.all.groups')\
                    and model.find('wizard') == -1:

                model_name = model.replace('.', '_')
                if model_name in module_new_models:

                    if len(view_dict[model]) >= 3:
                        self.feel_good_factor += 1
                    else:
                        self._report_issue('You should have at least a\
                        form/tree/search view for each model, missing views\
                        for model %s' % model)

                    has_default_search = False
                    has_default_tree = False
                    has_default_form = False
                    default_search_view_name = '%s_%s_search' % (
                        'view', model_name)
                    default_tree_view_name = '%s_%s_tree' % (
                        'view', model_name)
                    default_form_view_name = '%s_%s_form' % (
                        'view', model_name)

                    for view in module_new_views:
                        view_name = view['name']
                        if view['model'] != model:
                            continue
                        if view_name == default_search_view_name:
                            self.feel_good_factor += 1
                            has_default_search = True
                        elif view_name == default_tree_view_name:
                            self.feel_good_factor += 1
                            has_default_tree = True
                        elif view_name == default_form_view_name:
                            self.feel_good_factor += 1
                            has_default_form = True
                        elif view_name.find(default_search_view_name) > -1 \
                            or view_name.find(default_tree_view_name) > -1 \
                                or view_name.find(default_form_view_name) > -1:
                            self.feel_good_factor += 1
                        else:
                            self._report_issue(
                                'The view name "%s" does not respect Trobz\
                                standard naming convention.' % view_name)

                    if not has_default_search:
                        self._report_issue(
                            'You should have at least a search view with the\
                            name: %s' % default_search_view_name)

                    if not has_default_tree:
                        self._report_issue(
                            'You should have at least a tree view with the\
                            name: %s' % default_tree_view_name)

                    if not has_default_form:
                        self._report_issue(
                            'You should have at least a form view with the\
                            name: %s' % default_form_view_name)

    def run_test_trobz(self, cr, uid, module_path):
        self.registry = RegistryManager.get(cr.dbname)
        self._set_project_sections(cr, uid)
        score = 1.0
        list_files = os.listdir(module_path)
        module_name = module_path.split('/')[-1]
        all_installed_model_list = self.get_all_installed_model_list(cr, uid)
        # evaluate the source code structure
        code_files = self._get_code_files(module_path, list_files)
        # make sure that
        #    + there is only 1 class in a python file
        #    +
        self._check_file_names_and_content(code_files,
                                           all_installed_model_list)
        # make sure there are at least 3 view types
        self._check_view_ids(cr, uid, module_name)
        '''
            SCORE CALCULATION
        '''
        if self.result_dict:
            total = float(self.feel_good_factor + self.feel_bad_factor)
            score = round((self.feel_good_factor) / total, 2)

        self.result_details = self.get_result_details(self.result_dict)
        return [_('Trobz Test'), score]

    def run_test(self, cr, uid, module_path):
        trobz_score = self.run_test_trobz(cr, uid, module_path)
        self.score = trobz_score and trobz_score[1] or 0.0
        if self.score * 100 < self.min_score:
            self.message = 'Score is lower than minimal score(%s%%)'\
                % self.min_score
        if trobz_score:
            self.result = self.get_result({'__openerp__.py': trobz_score})
        return None

    def get_result(self, dict_terp):
        # header = ('{| border="1" cellspacing="0" cellpadding="5" align="left"
        # \n! %-40s \n! %-10s \n', [_('Object Name'), _('Result (/1)')])
        header = ('{| border="1px solid black" cellspacing="0" cellpadding="5"\
                   align="left" \n! %-40s \n! %-10s \n',
                  [_('Object Name'), _('Result (/1)')])
        if not self.error:
            return self.format_table(header, data_list=dict_terp)
        return ""

    def get_result_details(self, dict_terp):
        if dict_terp:
            str_html = '''<html><head>%s</head><body><table\
             class="tablestyle">''' % (
                self.get_style())
            header = ('<tr><th class="tdatastyle">%s</th><th\
             class="tdatastyle">%s</th></tr>',
                      [_('Tag Name'), _('Module Analysis with\
                       Trobz standards')])
            if not self.error:
                res = str_html + \
                    self.format_html_table(
                        header, data_list=dict_terp) + '</table><newline/>\
                        </body></html>'
                res = res.replace('''<td''', '''<td class="tdatastyle" ''')
                return res
        return ""

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
