# -*- coding: utf-8 -*-

from openerp.osv import osv, fields

class connection_config(osv.osv):
    _name = 'connection.config'
    _description = 'Connection Config'
    
    def get_connection(self, cr, uid, ids, field_name, arg, context=None):
        """
        Record name is the name of the record (to be synchronized) and the mapping name.
        """
        res = {}
        for sync_obj in self.read(cr, uid, ids, ['model', 'id_src'], context=context):
            res[sync_obj['id']] = sync_obj['model'] + ' - ' + str(sync_obj['id_src'])
        return res
    
    _columns = {
        'url':fields.char('Url', size=256, required=True),
        'url_type':fields.selection([('check','Check In/Out'),('create','Create'),
                                       ('update','Update'),('delete','Delete')],string='Type',required=True),
        'last_check_date': fields.datetime('Last Check Date'),
        'b_run_again': fields.boolean('Cheking Again'),
        'date_run_again': fields.datetime('Running Date Again'),
    }
    
    _defaults = {
        'b_run_again': lambda *a: False,
    }
    
connection_config()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
