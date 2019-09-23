# -*- encoding: utf-8 -*-
##############################################################################

import re

from openerp import models, api
from openerp import tools


class post_object_trobz_report(models.TransientModel):
    _name = 'post.object.trobz.report'

    @api.model
    def start(self):
        '''
        Start Post Object Function
        '''
        self.update_value_report_url()
        return True

    @api.model
    def update_value_report_url(self):
        
        check_bool = re.compile(r"^(?i)^on|true|yes$")
        ir_config_para = self.env['ir.config_parameter']
        
        port = tools.config.get('xmlrpc_port', None)
        interface = tools.config.get('xmlrpc_interface', None)
        report_url = tools.config.get('report_url', None)
        
        no_update = ir_config_para.get_param('report.url.noupdate', False)
        no_update = check_bool.match(str(no_update)) and True or False
        
        current_val = ir_config_para.get_param('report.url', None)
        current_val = current_val == '' and None or current_val
        
        if not no_update or (no_update and not current_val):
            if report_url:
                ir_config_para.set_param('report.url', report_url)
            elif interface and port:
                values = 'http://%s:%s' % (interface, str(port))
                ir_config_para.set_param('report.url', values)
            else:
                web_local = ir_config_para.get_param(key='web.base.url')
                ir_config_para.set_param('report.url', web_local)
    
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
