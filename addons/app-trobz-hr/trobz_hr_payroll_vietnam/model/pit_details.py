from openerp.osv import fields, osv

class pit_details(osv.osv):
    _name = 'pit.details'
    _description = 'PIT'
    _columns = {
        'name': fields.char('Description'),
        'price': fields.float('Price'),
        'tax': fields.float('Tax'),
        'sequence': fields.integer('Sequence'),
        'income_before_tax': fields.char('Income before tax')
    }

pit_details()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
