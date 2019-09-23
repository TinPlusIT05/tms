# -*- encoding: utf-8 -*-
##############################################################################

from openerp.osv import osv

class post_object(osv.osv_memory):
    
    _name = 'post.default.uae.data'
    _description = 'Defaul UAE Data > Post Object '
    _auto = False
    _log_access = True
    
    
    def start(self, cr, uid):
        return True
    
post_object()
