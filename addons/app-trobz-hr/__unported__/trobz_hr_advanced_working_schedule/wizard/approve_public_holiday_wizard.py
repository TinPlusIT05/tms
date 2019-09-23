# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
from openerp.tools.translate import _

class approve_public_holiday_wizard(osv.osv_memory):
    
    _name = 'approve.public.holiday.wizard'
    
    _description = 'Approve Public Holiday'
    
    
    _columns = {
                'public_holiday_ids': fields.many2many('trobz.hr.public.holidays', 'approve_public_holiday', 'approve_id', 'holiday_id', string="Public Holidays", required=True),
    }
    
    def apply(self, cr, uid, ids, context=None):
        public_holidays_obj = self.pool.get('trobz.hr.public.holidays')
        
        if ids:
            update_public_holiday_ids = []
            approve_public_holidays = self.read(cr, uid, ids, ['public_holiday_ids'], context)
            for approve_public_holiday in approve_public_holidays:
                public_holiday_ids = approve_public_holiday.get('public_holiday_ids', [])
                public_holidays = public_holidays_obj.read(cr, uid, public_holiday_ids, ['state', 'template_holidays'], context)
                
                for public_holiday in public_holidays:
                    state = public_holiday.get('state', False)
                    template_holidays = public_holiday.get('template_holidays', False)
                    if template_holidays:
                        raise osv.except_osv(_('Error!'), _('You cannot approve a public holiday template!')) 
                    if state == 'draft':
                        update_public_holiday_ids.append(public_holiday.get('id', False))
            
            if update_public_holiday_ids:
                public_holidays_obj.write(cr, uid, update_public_holiday_ids, {'state': 'approved'}, context)
                        
        return True
    
    
approve_public_holiday_wizard()
