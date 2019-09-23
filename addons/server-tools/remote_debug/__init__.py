# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
#    Trobz - Open Source Solutions for the Enterprise                        #
#    Copyright (C) 2009 Trobz (<http://trobz.com>). All Rights Reserved      #
#                                                                            #
##############################################################################

import sys
import logging
import commands

from openerp.tools import config

_logger = logging.getLogger('remote-debug')


def remote_debug(host, port=5678):

    if host == 'auto':
        status_code, default_host = commands.getstatusoutput(
            "netstat -nr | grep '^0\.0\.0\.0' | awk '{print $2}'"
        )
        host = default_host if status_code == 0 else 'localhost'

    try:
        import pydevd
    except:
        _logger.error(
            "pydevd module not found.\n" +
            "Please install it and add it to your PYTHONPATH.\n" +
            "see: http://goo.gl/mhLa8k")
        sys.exit(1)

    try:
        stderr = sys.stderr
        sys.stderr = open('/dev/null', 'a+')
        pydevd.settrace(host, port=int(port), suspend=False)
        sys.stderr = stderr
        _logger.info('Connected to remote debugger on %s:%s.', host, port)
    except:
        _logger.error(
            "Cannot connect to remote debugging at %s:%s.",
            host, port)
        _logger.error(
            "Please, check if your IDE is listening " +
            "on port %s for remote debugging.", port)
        sys.stderr = stderr


if config.get('debug_enabled', False):
    remote_debug(config.get('debug_host', 'auto'),
                 config.get('debug_port', 5678))
