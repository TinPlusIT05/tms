# -*- encoding: utf-8 -*-
##############################################################################
#                                                                            #
#    Trobz - Open Source Solutions for the Enterprise                        #
#    Copyright (C) 2009 Trobz (<http://trobz.com>). All Rights Reserved      #
#                                                                            #
##############################################################################

import logging
_logger = logging.getLogger('auto-install')

def override_get_module_info():
    from openerp import modules

    origin_load_information_from_description_file = modules.load_information_from_description_file

    module_without_autoinstall = [
        'bus',
        'im_chat',
    ]
    def remove_auto_install(module):
        info = origin_load_information_from_description_file(module)
        if module in module_without_autoinstall:
            _logger.warning("Removing the auto_install feature for the module %s",module)
            info['auto_install'] = False
        return info
    modules.load_information_from_description_file = remove_auto_install
    
from .register import pretask
 
pretask.register(
    'Disable auto_install for specific OpenERP modules',
    override_get_module_info
)

pretask.run()