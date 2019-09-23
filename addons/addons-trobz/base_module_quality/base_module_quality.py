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

from openerp.modules.registry import RegistryManager
from openerp.tools.translate import _
from openerp.osv import osv, fields
import logging
from openerp import modules
from datetime import datetime

import imp
# TODO: Create a scheduler to run those checks once every 2 hours when the
# module is installed


class abstract_quality_check(object):

    '''
        This Class is abstract class for all test
    '''

    def __init__(self):
        '''
        this function should initialize the variables
        '''

        # This float have to store the rating of the module.
        # Used to compute the final score (average of all scores).
        # 0 <= self.score <= 1
        self.score = 0.0

        # This char have to store the name of the test.
        self.name = ""

        # This char have to store the aim of the test and eventually a note.
        self.note = ""

        # This char have to store the result.
        # Used to display the result of the test.
        self.result = ""

        # This char have to store the result with more details.
        # Used to provide more details if necessary.
        self.result_details = ""

        # This boolean variable defines that if you do not want to calculate
        # score and just only need detail
        # or summary report for some test then you will make it False.
        self.bool_count_score = True

        # This bool defines if the test can be run only if the module
        # is installed.
        # True => the module has to be installed.
        # False => the module can be uninstalled.
        self.bool_installed_only = True

        # This variable is used to give result of test more weight,
        # because some tests are more critical than others.
        self.ponderation = 1.0

        # Specify test got an error on module
        self.error = False

        # Specify the minimal score for the test (in percentage(%))
        self.min_score = 50

        # Specify whether test should be consider for Quality checking of the
        # module
        self.active = True

        # This variable used to give message if test result is good or not
        self.message = ''
        self.log = logging.getLogger('module.quality')

        # The tests have to subscribe itselfs in this list, that contains
        # all the test that have to be performed.
        self.tests = []
        module_path = modules.get_module_path('base_module_quality')
        for item in os.listdir(module_path):
            path = module_path + '/' + item
            full_path_file = path + '/' + item + '.py'
            if os.path.isdir(path) and os.path.exists(full_path_file) \
                and item not in ['report',
                                 'wizard',
                                 'security']:
                test_module = imp.load_source(item, full_path_file)
                self.tests.append(test_module)

    def run_test(self, cr, uid, module_path=""):
        '''
        This function should do the test and fill the score, result and
        result_details var
        '''

        raise osv.except_osv(
            _('Programming Error'), _('Test Is Not Implemented'))

    def get_all_installed_model_list(self, cr, uid):
        '''This function returns all object of the given module..
        '''

        registry = RegistryManager.get(cr.dbname)
        ir_model_data_obj = registry['ir.model.data']
        ir_model_obj = registry['ir.model']

        model_ids = []
        ids2 = ir_model_data_obj.search(cr, uid, [('model', '=', 'ir.model')])
        model_datas = ir_model_data_obj.browse(cr, uid, ids2)
        for model_data in model_datas:
            model_ids.append(model_data.res_id)

        obj_list = []
        model_recs = ir_model_obj.browse(cr, uid, model_ids)
        for model_rec in model_recs:
            if model_rec.model not in obj_list:
                obj_list.append(model_rec.model)

        return obj_list

    def get_new_models_of_module(self, cr, uid, module_name):
        """
        Only get models created in this module
        """
        registry = RegistryManager.get(cr.dbname)
        ir_model_obj = registry['ir.model']
        sql = """
            SELECT imd1.res_id
            FROM ir_model_data imd1
            WHERE
                model='ir.model'
                and exists (select 1
                            from ir_model_data imd2
                            where imd1.name=imd2.name and module='%s')
            GROUP BY imd1.res_id
            HAVING count(*)=1
        """
        sql = sql % (module_name)

        cr.execute(sql)
        module_new_modules_ids = []
        if cr.rowcount:
            module_new_modules_ids = [x[0] for x in cr.fetchall()]
        obj_list = []
        model_recs = ir_model_obj.browse(cr, uid, module_new_modules_ids)
        for model_rec in model_recs:
            obj_list.append(model_rec.model)

        return obj_list

    def get_objects(self, cr, uid, module):
        '''This function returns all object of the given module..
        '''
        registry = RegistryManager.get(cr.dbname)
        ir_model_data_obj = registry['ir.model.data']
        ir_model_obj = registry['ir.model']

        ids2 = ir_model_data_obj.search(
            cr, uid, [('module', '=', module), ('model', '=', 'ir.model')])
        # ids2 = ir_model_obj.search(cr, uid, [('osv_memory', '=', False),
        # ('id', 'in', ids2)])
        model_ids = []
        model_datas = ir_model_data_obj.browse(cr, uid, ids2)
        for model_data in model_datas:
            model_ids.append(model_data.res_id)

        obj_list = []
        model_recs = ir_model_obj.browse(cr, uid, model_ids)
        for model_rec in model_recs:
            # AbstractModel will have _auto = False
            if registry[model_rec.model]._auto:
                obj_list.append(model_rec.model)

        return obj_list

    def get_model_ids(self, cr, uid, models=[]):
        '''This function returns all ids of the given objects..
        '''

        if not models:
            return []
        registry = RegistryManager.get(cr.dbname)
        return registry['ir.model'].search(cr, uid, [('model', 'in', models)])

    def get_ids(self, cr, uid, object_list):
        '''
        This function return dictionary with ids of records of object
        for module
        '''
        registry = RegistryManager.get(cr.dbname)
        result_ids = {}
        for obj in object_list:
            # do not test Transient Model
            if registry[obj].is_transient():
                continue

            ids = registry[obj].search(cr, uid, [])
            ids = filter(lambda obj_id: obj_id is None, ids or [])
            result_ids[obj] = ids

        return result_ids

    # This function can work forwidget="text_wiki"
    def format_table(self, header=[], data_list={}):
        detail = ""
        detail += (header[0]) % tuple(header[1])
        frow = '\n|-'
        for i in header[1]:  # @UnusedVariable
            frow += '\n| %s'
        for value in data_list.itervalues():
            detail += (frow) % tuple(value)
        detail = detail + '\n|}'
        return detail

    # This function can work for widget="html_tag"
    def format_html_table(self, header=[], data_list=[]):
        '''This function create html table....
        '''

        detail = ""
        detail += (header[0]) % tuple(header[1])
        frow = '<tr>'
        for i in header[1]:  # @UnusedVariable
            frow += '<td>%s</td>'
        frow += '</tr>'
        for value in data_list.values():
            detail += (frow) % tuple(value)
        return detail

    def add_quatation(self, x_no, y_no):
        return x_no / y_no

    def get_style(self):
        '''This function return style tag with specified styles for html pages
        '''

        style = '''
            <style>
                .divstyle {
                border:1px solid #aaaaaa;
                background-color:#f9f9f9;
                padding:5px;
                }
                .tablestyle
                {
                border:1px dashed gray;
                }
                .tdatastyle
                {
                border:0.5px solid gray;
                }
                .head
                {
                color: black;
                background: none;
                font-weight: normal;
                margin: 0;
                padding-top: .5em;
                padding-bottom: .17em;
                border-bottom: 1px solid #aaa;
                }
                }
          </style> '''
        return style


class module_quality_check(osv.osv):
    _name = 'module.quality.check'
    _order = 'date_check desc'

    _columns = {
        'name': fields.char('Rated Module', size=64, ),
        'final_score': fields.char('Final Score (%)', size=10,),
        'check_detail_ids': fields.one2many('module.quality.detail',
                                            'quality_check_id', 'Tests'),
        'date_check': fields.datetime('Date Check', readonly=True),
    }

    def run_recheck_quality_all_modules_scheduler(self, cr, uid, context=None):
        check_ids = self.search(cr, uid, [])
        for check in self.read(cr, uid, check_ids, ['id', 'name']):
            self.button_check_quality(
                cr, uid, [check['id']], {'module_name': check['name']})
        return True

    def button_check_quality(self, cr, uid, ids, context):

        module_name = ''

        if ids:
            rows = self.read(cr, uid, ids, ['id', 'name'])
            for check in rows:
                module_name = check['name']
                break

        if not module_name and context.get('module_name', False):
            module_name = context.get('module_name', False)
        if not module_name:
            return False

        data = self.check_quality(cr, uid, module_name)
        detail_obj = self.pool['module.quality.detail']
        old_detail_ids = detail_obj.search(
            cr, uid, [('quality_check_id', 'in', ids)])
        # delete old details
        if old_detail_ids:
            detail_obj.unlink(cr, uid, old_detail_ids)
        # rewrite
        return self.write(cr, uid, ids, data, context=context)

    def check_quality(self, cr, uid, module_name, module_state=None):
        '''
        This function will calculate score of openerp module
        It will return data in below format:
            Format: {'final_score':'80.50', 'name': 'sale',
                    'check_detail_ids':
                        [(0,0,{'name':'workflow_test',
                                'score':'100', 'ponderation':'0',
                                'summary': text_wiki format data,
                                'detail': html format data,
                                'state':'done', 'note':'XXXX'}),
                        ((0,0,{'name':'terp_test',
                                'score':'60',
                                'ponderation':'1',
                                'summary': text_wiki format data,
                                'detail': html format data,
                                'state':'done',
                                'note':'terp desctioption'}),
                         ..........]}
        So here the detail result is in html format and summary will be in
        text_wiki format.
        '''

        registry = RegistryManager.get(cr.dbname)
        obj_module = registry['ir.module.module']
        if not module_state:
            module_id = obj_module.search(
                cr, uid, [('name', '=', module_name)])
            if module_id:
                module_state = obj_module.browse(cr, uid, module_id[0]).state

        abstract_obj = abstract_quality_check()
        score_sum = 0.0
        ponderation_sum = 0.0
        create_ids = []
        module_path = modules.get_module_path(module_name)
        logging.info('Performing quality tests for %s' % module_name)
        for test in abstract_obj.tests:
            val = test.quality_test()
            if not val.active:
                logging.info(
                    'Skipping inactive step %s for %s', val.name, module_name)
                continue

            logging.info('Performing step %s for %s', val.name, module_name)
            # Get a separate cursor per test, so that an SQL error in one
            # will not block the others.
            cr2 = RegistryManager.get(cr.dbname).cursor()

            try:
                if not val.bool_installed_only or module_state == "installed":
                    val.run_test(cr2, uid, str(module_path))
                    if not val.error:
                        data = {
                            'name': val.name,
                            'score': val.score * 100,
                            'ponderation': val.ponderation,
                            'summary': val.result,
                            'detail': val.result_details,
                            'state': 'done',
                            'note': val.note,
                            'message': val.message,
                        }
                        if val.bool_count_score:
                            score_sum += val.score * val.ponderation
                            ponderation_sum += val.ponderation
                    else:
                        data = {
                            'name': val.name,
                            'score': 0,
                            'summary': val.result,
                            'state': 'skipped',
                            'note': val.note,
                        }
                else:
                    data = {
                        'name': val.name,
                        'note': val.note,
                        'score': 0,
                        'state': 'skipped',
                        'summary': _("The module has to be installed before \
                                        running this test.")
                    }
                create_ids.append((0, 0, data))
                logging.info('Finished quality test step')
            except Exception, e:
                logging.exception(
                    "Could not finish test step %s due to %s", val.name, e)
            finally:
                cr2.rollback()
                cr2.close()
        final_score = ponderation_sum and '%.2f' % (
            score_sum / ponderation_sum * 100) or 0
        data = {
            'name': module_name,
            'final_score': final_score,
            'check_detail_ids': create_ids,
            'date_check': datetime.now(),
        }
        return data


class module_quality_detail(osv.Model):
    _name = 'module.quality.detail'
    _columns = {
        'quality_check_id': fields.many2one('module.quality.check',
                                            'Quality', ondelete='cascade'),
        'name': fields.char('Name', size=128),
        'score': fields.float('Score (%)'),
        'ponderation': fields.float('Ponderation',
                                    help='Some tests are more critical than\
                                     others, so they have a bigger weight in\
                                     the computation of final rating'),
        'note': fields.text('Note'),
        'summary': fields.text('Summary'),
        'detail': fields.html('Details'),
        'message': fields.char('Message', size=64),
        'state': fields.selection([('done', 'Done'), ('skipped', 'Skipped')],
                                  'State', size=24,
                                  help='The test will be completed only if the\
                                  module is installed or if the test may be\
                                  processed on uninstalled module.'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
