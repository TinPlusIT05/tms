# -*- encoding: utf-8 -*-
##############################################################################
#                                                                            #
#    Trobz - Open Source Solutions for the Enterprise                        #
#    Copyright (C) 2009 Trobz (<http://trobz.com>). All Rights Reserved      #
#                                                                            #
##############################################################################

import logging
_logger = logging.getLogger('pretask')

class Register(list):
    
    def register(self, name, func, *args):
        """
        Register a function.
        """
        self.append({
            'name': name,
            'func': func,
            'args': args
        })
        

    def run(self):
        """
        Run all registered functions.
        """
        for command in self:
            _logger.info('execute "%s"...', command['name'])
            command['func'](*command['args'])

    def cleanup(self):
        """
        Clean up logging handlers.
        """
        import logging
        root = logging.getLogger()
        if root.handlers:
            for handler in root.handlers:
                root.removeHandler(handler)


#some kind of singleton...
pretask_instance = None
def get_pretask():
    global pretask_instance
    if not isinstance(pretask_instance, Register):
        pretask_instance = Register()
    return pretask_instance
 
pretask = get_pretask()
