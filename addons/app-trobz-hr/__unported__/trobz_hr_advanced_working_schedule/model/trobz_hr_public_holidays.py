# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv

class trobz_hr_public_holidays(osv.osv):
    _inherit = "trobz.hr.public.holidays"

    _columns = {
        'state': fields.selection([('draft', 'Draft'),
                   ('approved', 'Approved')], 
                    'Status',readonly=True),
    }

    
    _defaults = {
        'state':'draft',
    }
    def action_process(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        
        # button Set to Draft
        if context.get('hr_advanced_working_schedule_state', False) == 'draft':
            self.action_set_to_draft(cr, uid, ids, context)
            
        # button Approved
        if context.get('hr_advanced_working_schedule_state', False) == 'approved':
            self.action_set_to_approve(cr, uid, ids, context)
            
        return True

    def action_set_to_draft(self, cr, uid, ids, context=None):
        if ids:
            self.write(cr, uid, ids, {'state': 'draft'}, context)
        
        return True
    
    def action_set_to_approve(self, cr, uid, ids, context=None):
        if ids:
            self.write(cr, uid, ids, {'state': 'approved'}, context)
            
        return True
    

trobz_hr_public_holidays()
