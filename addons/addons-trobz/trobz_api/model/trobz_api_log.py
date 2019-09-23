# -*- encoding: utf-8 -*-
##############################################################################

from openerp.osv import fields, osv

class trobz_api_log(osv.osv):
    _name = "trobz.api.log"
    _description = "Trobz API Log"
    
    _columns = {
        'name': fields.datetime('Date Time', required=True),
        'uid':fields.many2one('res.users', string='User'),
        'model':fields.char('Model'),
        'action':fields.char('Action'),
        'vals': fields.serialized('Vals'),
        'domain': fields.char('Domain'),
        'message': fields.char('Return Message'),
        'resource_id':fields.integer('Resource'),
        'status': fields.selection([('pass','Pass'),('fail','Fail')],'Status'),
    }

    _order = "name desc"
    
    _defaults = {
        'name': lambda *a: fields.datetime.now(),
    }
    
trobz_api_log()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
