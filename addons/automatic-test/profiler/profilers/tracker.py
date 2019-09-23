
import os
import re
import json
import sys
import time
import threading

from openerp.tools.safe_eval import safe_eval
from openerp.modules.registry import RegistryManager
from openerp import SUPERUSER_ID
from csv_profiler import CSVProfiler

import logging
logger = logging.getLogger('tracker')


class TrackerProfiler(CSVProfiler):
        """
        Track method calls on OpenERP model
        """

        def __init__(self):

            self.registry = None
            self.enabled = False
            self.csv_path = ''
            self.tracked = {}
            self.planned = []
            self.start = None
            self.id = 1

            self.configure()

            columns = [
                'exec_time', 'embedment', 'module', 'model', 'method',
                'object name', 'arguments', 'timestamp', 'file'
            ]

            super(TrackerProfiler, self).__init__(
                self.csv_path, columns
            )

            if self.enabled:
                self.init()


        def model(self, target, methods, options=None):
            """
            Watch methods on a specific model
            """

            self.planned.append([target, methods, options])

            if self.enabled:
                self.track(target, methods, options=options)

        def track(self, target, methods, options=None):
            """
            Track methods.
            """

            if target not in self.tracked:
                openerp_model = self._get_model(target)
                self.tracked[target] = {
                    'model': openerp_model,
                    'methods': {}
                }

            else:
                openerp_model = self.tracked[target]['model']


            for method in methods:
                self._apply_tracker(method, openerp_model, self.tracked[target]['methods'], options)

        def enable(self):
            """
            Enabling all trackers
            """
            logging.info('Enabling profiling...')

            self.enabled = True
            for track_info in self.planned:
                self.track(*track_info)

        def disable(self):
            """
            Revert all methods to there initial state
            """
            logging.info('Disabling profiling...')

            self.enabled = False
            for target, tracked in self.tracked.items():
                model = tracked['model']
                for methodname, method in tracked['methods'].items():
                    logging.info('Revert tracking on model %s for method %s', model._name, methodname)
                    setattr(model, methodname, method)


        def _apply_tracker(self, method, model, origin_methods, options=None):
            """
            Track a method on a model.
            """

            options = options or {}
            options.setdefault('object_name', False)
            options.setdefault('arguments', False)


            if not hasattr(model, method):
                raise Exception(
                    'Failed to track method "%s" on model "%s", method not found.' %
                    (method, model._name)
                )

            origin_methods[method] = origin_method = getattr(model, method)

            global embedment
            embedment = []

            def tracking_method(*args, **kwargs):
                """
                Embed the method to track.
                """

                # get frame info

                try:
                    frame_index = 1
                    s1 = sys._getframe(frame_index)

                    excluded_methods = ['orm_unknown_field_exception', 'tracking_method', method]
                    while s1.f_code.co_name in excluded_methods:
                        frame_index += 1
                        s1 = sys._getframe(frame_index)

                except ValueError:
                    logger.error('Failed to inspect stacktrace for caller method.')
                    s1 = None

                module = 'undefined'
                filesource = 'undefined'

                if s1 and hasattr(s1, 'f_code') and hasattr(s1.f_code, 'co_filename'):

                    getaddons = re.compile(r"""^openerp\.(?:addons\.)?([^\.]*)""")
                    match = getaddons.search(s1.f_globals['__name__'])

                    module = match.group(1) if match else 'undefined'
                    filesource = '%s:%s' % (s1.f_code.co_filename, s1.f_lineno)


                # process options

                obj_name, arguments = '', ''

                if options['object_name'] and len(args) >= 3:
                    cr, uid, ids = args[0], args[1], args[2]
                    obj_name = ', '.join([obj.name for obj in model.browse(cr, uid, ids, fields_process=['name'])])

                if options['arguments']:
                    arguments = json.dumps(args[2:], separators=(',', ': '))

                global embedment

                embedment.append(method)

                debugstart = time.time()
                ret = origin_method(*args, **kwargs)
                current = time.time()
                exec_time = round(current - debugstart, 4)

                self.write(*[
                    exec_time, ' > '.join(embedment), module, model._name, method,
                    obj_name, arguments, debugstart, filesource
                ])

                embedment = filter(lambda a: a != method, embedment)

                return ret


            logger.info('Track method "%s" on model "%s"', method, model._name)
            setattr(model, method, tracking_method)


        def configure(self):
            """
            Get configuration parameters from database
            """

            dbname = threading.current_thread().dbname
            self.registry = RegistryManager.get(dbname)

            with self.registry.cursor() as cr:

                icp = self._get_model('ir.config_parameter')
                self.enabled = safe_eval(icp.get_param(cr, SUPERUSER_ID, 'profiler.enabled', 'False'))
                self.csv_path = icp.get_param(cr, SUPERUSER_ID, 'profiler.csv_file', '')

                csv_dir = os.path.dirname(self.csv_path)
                if self.enabled and not os.path.exists(csv_dir):
                    raise Exception('Failed to start profiling in CSV file. Directory %s not found on host.' % csv_dir)

        def _get_model(self, model_name):
            """
            Retrieve the model from his name
            """

            return self.registry.get(model_name)


tracker = TrackerProfiler()