# -*- coding: utf-8 -*-

from openerp.osv import osv, fields

class test_report_record(osv.osv):
    
    _name = 'test.report.record'
    
    _columns = {
        'res_id': fields.integer('Record Id', required=True),
        'report_id': fields.many2one('ir.actions.report.xml', 'Report'),        
        'res_model': fields.related('report_id','model',string= 'Model', type='char', store=True),
        'comment' : fields.text('Comment')
    }

test_report_record()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
