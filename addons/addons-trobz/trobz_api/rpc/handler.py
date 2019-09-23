# -*- coding: utf-8 -*-

from datetime import datetime
from time import time

import os
import xmlrpclib

from openerp.service import wsgi_server
from openerp.tools import config

import logging
_logger = logging.getLogger('log-xmlrpc')

class RPCLogHandler(object):

    def __init__(self, models, path):
        self.models = models
        self.path = path

    def log(self, request, response, method, params, environ):
        ip = environ['REMOTE_ADDR']
        pathinfo = environ['PATH_INFO']
        db, user_id, pwd, model, action = tuple(params[:5])
        params = params[5:]


        milliseconds =  str(int(round(time() * 1000)))
        now = datetime.utcnow()
        rdatetime = now.strftime("%Y-%m-%d %H-%M-%S")


        filename = '%s_%s_%s_%s.log' % (milliseconds, method, action, model)
        filepath = os.path.join(self.get_path(), filename)

        _logger.info(
            'Log XML-RPC call from ip:%s db:%s, user_id:%s model:%s method:%s,%s, params:%s in %s',
            ip, db, user_id, model, method, action, params, filename
        )

        envelope = [
            'Request received at %s from IP %s on path %s' % (rdatetime, ip, pathinfo),
            'method: %s' % method,
            'action: %s' % action,
            'user id: %s' % user_id,
            'model: %s' % model,
            'parameters: %s' % params,
            '',
            '--------------- REQUEST -------------',
            request,
            '',
            '--------------- RESPONSE -------------',
            response
        ]

        with open(filepath, 'w+') as logfile:
            logfile.write("\n".join(envelope))


    def path_xml_handler(self):
        """
        Monkey patching OpenERP xmlrpc handler
        """

        origin_xmlrpc_handler = wsgi_server.wsgi_xmlrpc
        this = self

        def wsgi_xmlrpc_logging_legacy(environ, start_response):
            if environ['REQUEST_METHOD'] == 'POST' and environ['PATH_INFO'].startswith('/xmlrpc/'):
                length = int(environ['CONTENT_LENGTH'])
                data = environ['wsgi.input'].read(length)
                path = environ['PATH_INFO'][len('/xmlrpc/'):] # expected to be one of db, object, ...

                params, method = xmlrpclib.loads(data)
                result = wsgi_server.xmlrpc_return(start_response, path, method, params, True)

                if path == 'object' and params[3] in this.models:
                    response = result[0] if result else 'No result'
                    this.log(data, response, method, params, environ)

                return result

        wsgi_server.wsgi_xmlrpc = wsgi_xmlrpc_logging_legacy


    def get_path(self):
        """
        Create log target folder, by date
        """
        date = datetime.utcnow().strftime("%Y-%m-%d")
        path = os.path.join(self.path, date)
        if not os.path.exists(path):
            os.makedirs(path)
        return path


def xmlrpc_log_handler():
    models = config.options.get('log_xmlrpc_models', '').split(',')
    path = config.options.get('log_xmlrpc_path')

    if models:
        handler = RPCLogHandler(models, path)
        handler.path_xml_handler()