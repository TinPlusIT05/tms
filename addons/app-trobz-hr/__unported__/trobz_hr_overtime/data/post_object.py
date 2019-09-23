# -*- encoding: utf-8 -*-
##############################################################################

from openerp.osv import osv

class post_object(osv.osv_memory):
    
    _name = 'post.object.trobz.hr.overtime'
    _description = 'post.object.trobz.hr.overtime'
    _auto = False
    _log_access = True

    def start(self, cr, uid):        
        #self.pool.get('trobz.help.page').create_help_page_for_trobz_module(
        # cr,uid,'trobz_hr_overtime')
        return True

post_object()
