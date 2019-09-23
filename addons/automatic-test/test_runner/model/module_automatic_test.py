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

from openerp.osv import osv, fields
import time
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT


class module_automatic_test(osv.osv):

    _name = "module.automatic.test"

    _columns = {
        'name': fields.char('Tested Module', size=64),
        'test_conclusion': fields.selection([('pass','Pass'),('fail', 'Fail')],
                                            string="Test Conclusion"),
        'date_check': fields.datetime('Date Check', readonly=True,
                                      help='Automatically updated with the '
                                      'date of the last test.'),
        'result_detail': fields.html('Detail', help='The results of the '
                                     'automatic test must be recorded '
                                     'automatically after launching the '
                                     'tests in this field'),
        'specific_test_case': fields.char(
            'Specific Test Case',
            help='This field to allow you can put the specific test case '
                 'name to launch a test. For example: '
                 '`openerp.addons.yourModule.tests.yourTestfile'
                 '.yourTestClass.yourTestCase`')
    }

    def _get_result_info(self, result):
        if result.wasSuccessful():
            return "Ran %s test OK" % result.testsRun
        else:
            detail_res = ''
            infos = []
            failed, errored = map(len, (result.failures, result.errors))
            if failed:
                infos.append("failures=%d" % failed)
            if errored:
                infos.append("errors=%d" % errored)
            detail_res += " FAILED (%s) \n" % ", ".join(infos)
            for test_fnct, traceback in result.errors + result.failures:
                detail_res += result.separator1 + '\n'
                detail_res += repr(test_fnct) + '\n'
                detail_res += result.separator2 + '\n'
                detail_res += traceback + '\n'
                detail_res += result.separator2 + '\n'
            return detail_res

    def hook_data(self, cr, uid, ids, data):
        """
        Modify data if need
        """
        return data

    def _run_test(self, cr, uid, ids, module_name, context={}):
        """
        Run automatic test for specific module
        """

        data = {
                 'test_conclusion': 'fail',
                 'date_check': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                 'result_detail': ''
                }

        result = self.pool.get('run.tests').start(cr, uid, module_name,
                                                  console_output=True,
                                                  context=context)
        if result.wasSuccessful():
            data['test_conclusion'] = 'pass'
            data['result_detail'] = \
                '<div class="test-results">%s</div>' % result.stream.data
        else:
            data['test_conclusion'] = 'fail'
            data['result_detail'] = \
                '<div class="test-results">%s</div>' % result.stream.data

        # hook data
        data = self.hook_data(cr, uid, ids, data)

        self.write(cr, uid, ids, data, context=context)

        return data

    def button_test(self, cr, uid, ids, context={}):
        """

        """
        module_name = ''
        specific_test_case = ''
        if ids:
            rows = self.read(cr,uid,ids,['id', 'name', 'specific_test_case'])
            for module_check in rows:
                module_name = module_check['name']
                specific_test_case = module_check['specific_test_case']
                break
        if not module_name and context.get('module_name', False):
            module_name = context.get('module_name', False)
        if not module_name:
            return False
        if specific_test_case:
            context.update({'specific_test_case': specific_test_case})

        return self._run_test(cr, uid, ids, module_name, context)

    def run_scheduler_tests(self, cr, uid, context={}):
        """
        Create a scheduler to run the tests automatically
        for all existing record of module.automatic.test 
        """
        module_auto_test_obj = self.pool.get('module.automatic.test')
        module_test_ids = module_auto_test_obj.search(cr, uid, [])
        for module_test in module_auto_test_obj.read(cr, uid, module_test_ids,
                                                     ['id','name'],
                                                     context=context):
            self._run_test(cr, uid, [module_test['id']], module_test['name'],
                           context)


module_automatic_test()
