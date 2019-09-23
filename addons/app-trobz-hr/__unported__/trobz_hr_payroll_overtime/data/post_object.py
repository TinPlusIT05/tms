# -*- encoding: utf-8 -*-
##############################################################################

from openerp.osv import osv

class post_object(osv.osv_memory):
    
    _name = 'post.object.trobz.hr.payroll.overtime'
    _description = 'post.object.trobz.hr.payroll.overtime'
    _auto = False
    _log_access = True

    def start(self, cr, uid):
        return True

post_object()
