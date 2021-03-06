# -*- encoding: utf-8 -*-
##############################################################################

from openerp.osv import osv, fields

class booking_chart(osv.osv):
    
    _name = "booking.chart"
    _description = "Booking Chart"
    
    def extra_fields(self, cr, uid, ids, field_names, arg, context=None):
        result = {}
        supported_models = []
        for chart in self.browse(cr, uid, ids, context=context):
            
            for supported_model in chart.supported_model_ids:
                supported_models.append((supported_model.model, supported_model.name))
            
            result[chart.id] = {
                'resource_model_name': chart.resource_model.model,
                'create_model_name': chart.create_model and chart.create_model.model or False,
                'supported_models': supported_models 
            }
        
        return result

    _columns = {

        'name': fields.char('Chart Name'),

        'resource_model': fields.many2one(
            'ir.model', 'Model of the Resource', required=True,
            help='OpenERP model that represents the booked resource.'),

        'resource_domain': fields.char(
            'Domain to filter the resources', help='''This Domain has the format of an domain expression
            (see: https://doc.openerp.com/trunk/web/rpc/ ). It is used if we want to display only some resources
            filtered based on that domain. Example: [["is_company","=",false]]'''),

        'resource_name': fields.char('Resource Name'),
        'create_model': fields.many2one('ir.model', 'Origin model of creating Resource', help='''When clicking button create on booking 
            chart, the form of this model will be opened.'''),
        
        'supported_model_ids': fields.many2many(
            'ir.model', 'booking_chart_to_model_rel', id1='chart_id', id2='model_id', required=True,
            string='Target/Orgin Resource Models', help='Models used for Resource Booking Target and Origin.'),
        
        'resource_model_name': fields.function(
            extra_fields, method=True, type='serialized', string='Resource Model Name', multi=True, readonly=True),
        'create_model_name': fields.function(
            extra_fields, method=True, type='char', string='Create Model Name', multi=True, readonly=True),                

        'supported_models': fields.function(
            extra_fields, method=True, type='serialized', string='Supported Model Array', multi=True, readonly=True)
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
