# -*- encoding: utf-8 -*-
##############################################################################

from openerp.osv import osv
from openerp.modules import module
from openerp.netsvc import ColoredFormatter

import sys
import re
import unittest2
import logging

from openerp.addons.test_runner.lib import suite as module_suite

_logger = logging.getLogger(__name__)


class StreamLogger(object):

    def __init__(self, stream, prefix=''):
        self.stream = stream
        self.data = ''

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

        # output with HTML colors
        data = re.sub(r"\033\[0m", '</span>', data)
        data = re.sub(r"\033\[1;32m\033\[1;49m", '<span class="info">', data)
        data = re.sub(r"\033\[1;31m\033\[1;49m", '<span class="error">', data)
        data = re.sub(
            r"\033\[1;33m\033\[1;49m", '<span class="warning">', data)
        data = re.sub(r"\n", '<br />', data)

        self.data += '<span class="unit-test">%s</span>' % data

    def flush(self):
        self.stream.flush()


class RemoteLogger(object):

    def __init__(self):
        self.data = ''

    def write(self, data):
        self.data += re.sub(r"\033[(?:;)?[0-9]+(?:m)?", '', data)

    def flush(self):
        pass


class run_tests(osv.TransientModel):
    _name = 'run.tests'
    _description = 'Run Tests'
    _log_access = True

    def remote_start(self, cr, uid, module_name):

        output = RemoteLogger()

        self._setup_test_logger(output=output)
        self.execute(cr, uid, module_name, output=output)
        self._reset_test_logger()

        from xml.sax.saxutils import escape
        return escape(output.data)

    def start(self, cr, uid, module_name, console_output=False, context={}):
        output = None
        if console_output:
            output = StreamLogger(sys.stderr)

        self._setup_test_logger(output=output)
        result = self.execute(cr, uid, module_name, output=output,
                              context=context)
        self._reset_test_logger()
        return result

    def execute(self, cr, uid, module_name, output=None, context={}):

        # force DB configuration
        from openerp.tests import common
        common.DB = cr.dbname

        _logger = logging.getLogger(__name__)

        # logging.TEST have no TEST attribute
        # TEST_LOG_LEVEL = logging.TEST
        TEST_LOG_LEVEL = logging.DEBUG  # @UndefinedVariable
#         ms = module.get_test_modules(
#             module_name, '__fast_suite__', explode=False)
#
#         ms.extend(module.get_test_modules(
#             module_name, '__sanity_checks__', explode=False))

        suite = module_suite.ModuleSuite()
        
        # Specific test case: In case we need to run with only one test case
        specific_test_case = context.get('specific_test_case')
        if specific_test_case:
            tests = \
                [unittest2.TestLoader().loadTestsFromName(specific_test_case)]
            suite.addTests(tests)
        else:
            
            ms = module.get_test_modules(module_name)
            for m in ms:
                suite.addTests(unittest2.TestLoader().loadTestsFromModule(m))
    
            if ms:
                _logger.log(TEST_LOG_LEVEL,
                            'module %s: executing %s `fast_suite` and/or '
                            '`checks` sub-modules', module_name, len(ms))
        
        output = output or sys.stderr

        result = unittest2.TextTestRunner(
            verbosity=2, stream=output, buffer=False).run(suite)

        if not result.wasSuccessful():
            _logger.error(
                'module %s: at least one error occurred in a test', module_name)

        return result

    def _setup_test_logger(self, output=None):
        self._tmp_log = {}

        logger = self._tmp_log['logger'] = logging.getLogger()

        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                tmp_handler = self._tmp_log['handler'] = handler
                tmp_stream = self._tmp_log['stream'] = handler.stream
                self._tmp_log['formatter'] = tmp_handler.formatter

        logger.setLevel(logging.INFO)
        tmp_handler.setFormatter(
            ColoredFormatter('%(levelname)s: %(message)s'))

        if output:
            tmp_handler.stream = output

        return self._tmp_log

    def _reset_test_logger(self):
        handler = self._tmp_log['handler']
        handler.setFormatter(self._tmp_log['formatter'])
        handler.stream = self._tmp_log['stream']
        
    def get_test_case(self, module, specific_test_case):
        """ Return a list of module for the addons potentially containing tests to
            feed unittest2.TestLoader.loadTestsFromModule() 
        """
        # Try to import the module
        modpath = 'openerp.addons.' + module
        try:
            mod = importlib.import_module('.tests', modpath)
        except Exception, e:
            # If module has no `tests` sub-module, no problem.
            if str(e) != 'No module named tests':
                _logger.exception('Can not `import %s`.', module)
            return []
    
        if hasattr(mod, 'fast_suite') or hasattr(mod, 'checks'):
            _logger.warn(
                "Found deprecated fast_suite or checks attribute in test module "
                "%s. These have no effect in or after version 8.0.",
                mod.__name__)
    
        result = [mod_obj for name, mod_obj in inspect.getmembers(mod, inspect.ismodule)
                  if name == specific_test_case]
        return result

run_tests()
