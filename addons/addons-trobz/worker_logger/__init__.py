# -*- coding: utf-8 -*-

# import netsvc

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import logging.handlers
import os
from openerp import tools
import sys
import threading

_logger = logging.getLogger(__name__)


path_prefix = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, _NOTHING, DEFAULT = range(
    10)
#The background is set with 40 plus the number of the color, and the foreground with 30
#These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"
COLOR_PATTERN = "%s%s%%s%s" % (COLOR_SEQ, COLOR_SEQ, RESET_SEQ)
LEVEL_COLOR_MAPPING = {
    logging.DEBUG: (BLUE, DEFAULT),
    logging.INFO: (GREEN, DEFAULT),
    logging.WARNING: (YELLOW, DEFAULT),
    logging.ERROR: (RED, DEFAULT),
    logging.CRITICAL: (WHITE, RED),
}


class DBFormatter(logging.Formatter):

    def format(self, record):
        record.pid = os.getpid()
        record.dbname = getattr(threading.currentThread(), 'dbname', '?')
        return logging.Formatter.format(self, record)

_logger_init = False


def init_logger():
    global _logger_init
    if _logger_init:
        return
    _logger_init = True

    root_logger = logging.getLogger()
    # create a format for log messages and dates
    format = '%(asctime)s %(pid)s %(levelname)s %(dbname)s %(name)s: %(message)s'

    if tools.config['logfile']:
        # LogFile Handler
        logf = tools.config['logfile']
        try:
            # We check we have the right location for the log files
            dirname = os.path.dirname(logf)
            if dirname and not os.path.isdir(dirname):
                os.makedirs(dirname)

            if tools.config['logrotate'] is not False and int(tools.config['workers']) > 1:
                root_logger.info("# OVERRIDE NATIVE logrotate init_logger #")
                try:
                    # try to import TimedRotatingFileHandlerSafe
                    from safe_logger import TimedRotatingFileHandlerSafe
                    log_handler = TimedRotatingFileHandlerSafe

                    # remove native TimedRotatingFileHandler of python
                    for handler in root_logger.handlers:
                        # check if has TimedRotatingFileHandler
                        if isinstance(handler, logging.handlers.TimedRotatingFileHandler):
                            # remove TimedRotatingFileHandler from root Logger
                            root_logger.removeHandler(handler)

                            # set update new log_handler time safe
                            handler = log_handler(
                                filename=logf, when='D',
                                interval=1, backupCount=30
                            )
                            formatter = DBFormatter(format)
                            handler.setFormatter(formatter)
                            root_logger.addHandler(handler)
                            root_logger.info(
                                "# using TimedRotatingFileHandlerSafe #"
                            )
                except:
                    root_logger.error(
                        " >>> OVERRIDE logfile rotate with multi-worker Fail #"
                    )
            else:
                root_logger.error("# Couldn't override logrotate #")

        except Exception:
            sys.stderr.write(
                "ERROR: couldn't create the logfile directory. Logging to the standard output.\n")

# self invoke to override
init_logger()
