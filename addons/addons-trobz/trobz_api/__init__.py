# -*- coding: utf-8 -*-

import model
import test_api

def patch_xmlrpc_handler():
    """
    monkey patch OpenERP XMLRPC request handler to add deep logging
    """
    from openerp.addons.trobz_api.rpc.handler import xmlrpc_log_handler
    xmlrpc_log_handler()

