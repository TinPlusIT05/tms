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

from openerp import tools
from openerp.tools.translate import _
from openerp.addons.base_module_quality import base_module_quality


class quality_test(base_module_quality.abstract_quality_check):

    def __init__(self):
        super(quality_test, self).__init__()
        self.name = _("File __openerp__.py Test")
        self.note = _(
            "This test checks if the file __openerp__.py satisfies the "
            "current coding standard used by OpenERP.")
        self.bool_installed_only = False
        self.no_terp = False
        self.ponderation = 1
        return None

    def run_test_terp(self, cr, uid, module_path):
        list_files = os.listdir(module_path)

        for i in list_files:
            path = os.path.join(module_path, i)
            if os.path.isdir(path):
                for j in os.listdir(path):
                    list_files.append(os.path.join(i, j))
        score = 1.0
        feel_good_factor = 0
        feel_bad_factor = 0
        if '__openerp__.py' not in list_files:
            self.no_terp = True
            self.result += _(
                "The module does not contain the __openerp__.py file")
            return None
        result_dict = {}
        result_dict1 = {}
        terp_file = os.path.join(module_path, '__openerp__.py')
        res = eval(tools.file_open(terp_file).read())
        # only list some important tag here....
        # there are other less important tag like: auto_install, qweb, images
        terp_keys = [
            'category', 'name', 'description', 'author', 'website', 'data',
            'depends', 'version', 'installable',
        ]
        optional_keys = [
            'auto_install', 'qweb', 'images', 'test', 'application', 'demo']
        for key in terp_keys:
            if key in res:
                feel_good_factor += 1  # each tag should appear
                if isinstance(res[key], (str, unicode, list)):
                    if not res[key]:
                        data = ''
                        if key == 'data':
                            data = "[OPTIONAL] Data tag is empty. It shows " \
                                   "that you do not have any views, wizard," \
                                   " workflow"
                        elif key == 'demo':
                            data = "[OPTIONAL] Demo tag is empty. It shows " \
                                   "that you do not have any demo data"
                        else:
                            data = "No information about " + key + " tag"
                            feel_bad_factor += 1
                        result_dict1[key] = [key, data]

                    else:
                        flag = False
                        # no. of chars should be >=150
                        if key == 'description' and len(str(res[key])) >= 150:
                            feel_good_factor += 1
                            flag = True
                            # description contains minimum 5 lines
                            if res['description'].count('\n') >= 4:
                                feel_good_factor += 1
                                flag = True
                        if not flag and key == 'description':
                            result_dict[key] = [key, "Description of the "
                                                "module in __openerp__.py may"
                                                "not enough, you should "
                                                "describe your module enough "
                                                "because good description is "
                                                "the beginning of a good "
                                                "documentation. And a good "
                                                "documentation limits the "
                                                "support requests."]
                        if key == 'website':
                            # reg ex matching on temporary basis.Website is
                            # correctly formatted
                            ptrn = re.compile('[https?://]?[\w\.:]+[\w /:]+$')
                            result = ptrn.search(str(res[key]))
                            if result:
                                feel_good_factor += 1
                            else:
                                result_dict[key] = [
                                    key, 'Website tag should be in valid '
                                    'format or it should be lead to valid '
                                    'page (for example: http://trobz.com/']
                                feel_bad_factor += 1

                if isinstance(res[key], bool):
                    # installable tag is provided and False
                    if key == 'installable' and not res[key]:
                        result_dict[key] = [
                            key, 'Installable tag of the __openerp__.py file '
                            'of module should be set to True so that it '
                            'can be installed on client!']
                        feel_bad_factor += 1
            elif key in optional_keys:
                result_dict1[key] = [key, "[OPTIONAL] Tag is missing!"]
            else:
                feel_bad_factor += 1
                result_dict1[key] = [key, "Tag is missing!"]

        if result_dict1 or result_dict1:
            score = round((feel_good_factor) / float(feel_good_factor +
                                                     feel_bad_factor), 2)

        self.result_details += self.get_result_details(result_dict)
        self.result_details += self.get_result_details(result_dict1)
        return [_('__openerp__.py file'), score]

    def run_test(self, cr, uid, module_path):
        terp_score = self.run_test_terp(cr, uid, module_path)
        self.score = terp_score and terp_score[1] or 0.0
        if self.score * 100 < self.min_score:
            self.message = 'Score is below than minimal score(%s%%)'\
                % self.min_score
        if terp_score:
            self.result = self.get_result({'__openerp__.py': terp_score})
        return None

    def get_result(self, dict_terp):
        header = ('{| border="1" cellspacing="0" cellpadding="5" align="left" '
                  '\n! %-40s \n! %-10s \n',
                  [_('Object Name'), _('Result (/1)')])
        if not self.error:
            return self.format_table(header, data_list=dict_terp)
        return ""

    def get_result_details(self, dict_terp):
        if dict_terp:
            str_html = '<html><head>%s</head><body><table class="tablestyle">'\
                % (self.get_style())
            header = ('<tr><th class="tdatastyle">%s</th><th '
                      'class="tdatastyle">%s</th></tr>',
                      [_('Tag Name'),
                       _('Feed back About __openerp__ file of Module')])
            if not self.error:
                res = str_html + \
                    self.format_html_table(header, data_list=dict_terp) + \
                    '</table><newline/></body></html>'
                res = res.replace('''<td''', '''<td class="tdatastyle" ''')
                return res
        return ""

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
