# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
from openerp.tools.translate import _

class fingerprint_record(osv.osv):
    _name = 'fingerprint.record'
    _description = 'Fingerprint Record'
    _order = 'model,id_src'
    
    def _get_record_name(self, cr, uid, ids, field_name, arg, context=None):
        """
        Record name is the name of the record (to be synchronized) and the mapping name.
        """
        res = {}
        for sync_obj in self.read(cr, uid, ids, ['model', 'id_src'], context=context):
            res[sync_obj['id']] = sync_obj['model'] + ' - ' + str(sync_obj['id_src'])
        return res
    
    _columns = {
        'name': fields.function(
            _get_record_name,
            type='char',
            string='Name',
            size=256,
            store={
                'fingerprint.record': (lambda self, cr, uid, ids, context=None: ids, ['model', 'id_src'], 10)
            }
        ),
        'model': fields.char('Model', size=64, required=True),
        'id_src': fields.integer('OpenERP ID', required=True),
        'id_remote': fields.integer('FingerPrint ID'),
        'date': fields.datetime('Last Synchronization Date'),
        'state': fields.selection((('draft', 'Draft'), ('running', 'Running'),
                                   ('success', 'Success'), ('fail', 'Failed')),
                                  'Last Synchronization Status'),
        'is_deleted': fields.boolean('Deleted Record'),
        'active': fields.boolean('Active'),
    }
    
    _defaults = {
        'state': lambda *a: 'draft',
        'active': lambda *a: True,
    }
    
    _sql_constraints = [
        ('uniq_src_model_remote_model', 'unique(model, id_src)', _('This fingerprint record is already existed!')),
    ]
    
    def unlink(self, cr, uid, ids, context=None):
        """
        Do NOT allow users to delete manually a fingerprint record.
        """
        if context is None:
            context = {}
        if not context.get('delete_from_sync', False):
            raise osv.except_osv(_('Warning'),
                                 _('You cannot delete manually a fingerprint record!'))
        return super(fingerprint_record, self).unlink(cr, uid, ids, context=context)

fingerprint_record()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
