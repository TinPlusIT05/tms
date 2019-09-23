# -*- coding: utf-8 -*-


import os
import re
import inspect
import logging
import unittest
from functools import wraps

from openerp import tools, modules
from openerp.tests import common
from openerp import tools
from openerp.osv.orm import browse_record
from openerp import SUPERUSER_ID


def skipIfModule(module_name, reason):
    try:
        modules.load_information_from_description_file(module_name)
        return unittest.skip(reason)
    except Exception:
        return lambda func: func


def load(files=[]):
    def _load_decorator(test_func):
        def wrapper(self, *args, **kwargs):
            self.load_data(self.cr, self.uid, files)
            return test_func(self, *args, **kwargs)
        return wrapper
    return _load_decorator


class ModuleCase(common.TransactionCase):

    # fixtures to load, available in all tests
    #  - can be directly the path to the file, inside your current test module
    #  - a dict object: {'module': '<module name>', 'file': 'path/to/data/file.ext', 'uid': 'xml_id_of_user'}
    #  - uid is optional, by default superuser (base.user_root) is used.
    load = []

    def setUp(self):
        self.case_info = {}
        super(ModuleCase, self).setUp()

        self.log_linebreak()
        self.load_data(self.cr, self.uid, self.load)
        self.initialize(self.cr, self.uid)

    def initialize(self, cr, uid):
        """
        This method can be overwritten
        """
        pass

    def load_data(self, cr, uid, load=[]):
        """
        Load data defined on test case `data` attribute
        """
        module = self.get_current_instance_module()

        for file in load:

            if not isinstance(file, dict):
                data = {
                    'module': module,
                    'file': file
                }
            else:
                data = file

            if not [name for name in ['module', 'file'] if name in data]:
                raise Exception('Test case data entry is not valid: %s', data)

            if data.get('uid', False):
                data.update({'uid': self.full_ref(data['uid'])})
            else:
                data.update({'uid': SUPERUSER_ID})
            self.log.debug("module %s: loading %s (User ID: %s)", data[
                           'module'], data['file'], data['uid'])

            _, ext = os.path.splitext(data['file'])
            pathname = os.path.join(data['module'], data['file'])
            fp = tools.file_open(pathname)

            noupdate = False

            # fake these incomprehensible params...
            idref = {}
            mode = 'update'
            kind = 'data'
            report = None

            # copy from server/openerp/modules/loading.py:66...
            def process_sql_file(cr, fp):
                queries = fp.read().split(';')
                for query in queries:
                    new_query = ' '.join(query.split())
                    if new_query:
                        cr.execute(new_query)

            try:
                ext = ext.lower()
                if ext == '.csv':
                    # TODO: Migrate the feature below to v8
                    # allow to specify a user when importing data. By default,
                    # use the superuser.
                    tools.convert_csv_import(
                        cr, module, pathname, fp.read(), idref, mode, noupdate)
                elif ext == '.sql':
                    process_sql_file(cr, fp)
                elif ext == '.yml':
                    tools.convert_yaml_import(
                        cr, module, fp, kind, idref, mode, noupdate, report)
                elif ext == '.xml':
                    tools.convert_xml_import(
                        cr, module, fp, idref, mode, noupdate, report)
                else:
                    self.log.warning(
                        "Can't load unknown file type %s.", data['file'])
            finally:
                fp.close()

    def ref(self, xmlid):
        """
        Get OpenObject based on xmlid

        if xml_id is not fully qualified (no module specified), try to get it
        from the current case module.
        """

        if '.' not in xmlid:
            module = self.get_current_instance_module()
            xmlid = '%s.%s' % (module, xmlid)

        return super(ModuleCase, self).ref(xmlid)

    def full_ref(self, xmlid):
        """ Returns database ID corresponding to a given identifier.

            :param xid: fully-qualified record identifier, in the form ``module.identifier``
            :raise: ValueError if not found
        """

        if '.' not in xmlid:
            module = self.get_current_instance_module()
        else:
            module, xmlid = xmlid.split('.')

        return self.registry('ir.model.data').get_object_reference(self.cr, self.uid, module, xmlid)

    def get_ref(self, model, id=None):
        """
        Get xml_id for an openerp object
        Can take an openerp object, a model object + id or the model name + id in parameter
        """
        cr, uid = self.cr, self.uid

        if isinstance(model, browse_record):
            id = model.id
            model = model._model

        if isinstance(model, str):
            model = self.registry(model)

        if not id:
            raise Exception(
                'Cannot retrieve xml id without object id parameter.')

        result = model.get_external_id(cr, uid, [id])
        return result[id] if id in result else None

    def create(self, model, data):
        """
        Create an openerp object
        """
        cr, uid, model = self.cr, self.uid, self.registry(model)
        return model.create(cr, uid, data)

    def browse(self, model, ids, fields=None):
        """
        Read openerp objects
        """
        cr, uid, model = self.cr, self.uid, self.registry(model)
        return model.browse(cr, uid, ids, fields)

    def browse_by_ref(self, xmlid, fields=None):
        """
        Read an openerp object based on his xmlid
        """

        model, id = self.full_ref(xmlid)
        return self.browse(model, id, fields=fields)

    def tearDown(self):
        """
        Clear model data cache ids after each test execution
        """

        self.registry('ir.model.data').clear_caches()
        super(ModuleCase, self).tearDown()

    def loadYamlFiles(self, module_name, yamlFiles):
        """
        Import yaml data.

        Depreciated, should use "data" attribute on case instead.
        """

        self.log.warning(
            'Depreciated method, you should use "load" attribute on case class instead.')
        for yaml_file in yamlFiles:
            pathname = os.path.join(module_name, yaml_file)
            fp = tools.file_open(pathname)
            tools.yaml_import(self.cr, module_name, fp, {})

    def get_current_instance_path(self):
        """
        Retrieve case instance file path
        """

        if 'path' not in self.case_info:
            path_pattern = re.compile(r'^(.*)/([^/])+$')
            instance_file = inspect.getfile(self.__class__)
            self.case_info['path'] = path_pattern.search(
                instance_file).group(1)

        return self.case_info['path']

    def get_current_instance_module(self):
        """
        Retrieve case instance module name
        """

        if 'module' not in self.case_info:
            module_pattern = re.compile(r'addons\.([^\.]+)')
            self.case_info['module'] = module_pattern.search(
                self.__module__).group(1)

        return self.case_info['module']

    def log_linebreak(self):
        """
        Output a linebreak on current log streamer
        """
        for handler in self.log.root.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.stream.write("\n")

    @classmethod
    def setUpClass(cls):
        cls.log = logging.getLogger(cls.__name__)
        super(ModuleCase, cls).setUpClass()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
