# -*- encoding: utf-8 -*-

# enabling logging facilities before starting openerp

import logging

logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s', level=logging.INFO)
_logger = logging.getLogger('pretask')

# init the pretask register
import register
import auto_install
