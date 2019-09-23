# -*- coding: utf-8 -*-
from openerp.osv import osv,fields
from datetime import datetime

class check_attendance_consistency_wizard(osv.osv_memory):
    
    _name = 'check.attendance.consistency.wizard'
    
    _columns = {
        'name':fields.char('name', size=64, required=False, readonly=False),
        'line_ids':fields.one2many('check.attendance.consistency.wizard.line', 'check_att_consis_id','Attendances', required=False, readonly=True),
    }
    
    def check_consistency(self, cr, uid, ids, context=None):
        return True
    
    def save(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        att_ids =[]
        for att_consistency in self.browse(cr, uid, ids, context=context):
            for line in att_consistency.line_ids:
                att_vals={
                    'name': line.name,
                    'action': line.action,
                    'action_desc': line.action_desc.id,
                    'employee_id': line.employee_id.id,
                    'status': 'normal',
#                    'is_inconsistent': False,
                }
                self.pool.get('hr.attendance').write(cr, uid, [line.att_id.id], att_vals, context=context)
                att_ids.append(line.att_id.id)
        return {'type': 'ir.actions.act_window',
                    'res_model': 'hr.attendance',
                    'name': 'Attendances',
                    'view_mode': 'tree',
                    'res_id': att_ids,
        }
    
    def check_again(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        # save
        for att_consistency in self.browse(cr, uid, ids, context=context):
            for line in att_consistency.line_ids:
                att_vals={
                    'name': line.name,
                    'action': line.action,
                    'action_desc': line.action_desc.id,
                    'employee_id': line.employee_id.id,
                    'status': 'normal',
#                    'is_inconsistent': False,
                }
                self.pool.get('hr.attendance').write(cr, uid, [line.att_id.id], att_vals, context=context)
#         return {'value': {'line_ids':self.get_attendance_inconsistent(cr, uid, context=context)}}
        return {'type': 'ir.actions.act_window',
                    'res_model': 'hr.attendance',
                    'name': 'Attendances',
                    'view_mode': 'tree',

        }
    
    def default_get(self, cr, uid, fields, context=None):
        res = super(check_attendance_consistency_wizard, self).default_get(cr, uid, fields, context=context)
        line_att_inconsistent = []
        att_obj = self.pool.get('hr.attendance')
        att_ids = att_obj.search(cr, uid, [('status','=','inconsistent')], context=context)
# Removed is_inconsistent
#        att_ids = att_obj.search(cr, uid, [('is_inconsistent','=',True)], context=context)
        trobz_base_obj = self.pool.get('trobz.base')
        today = datetime.now().date()
        for att in att_obj.browse(cr, uid, att_ids, context=context):
            date_tz = trobz_base_obj.convert_from_utc_to_current_timezone(cr, uid, att.name, False)
            if date_tz.date() < today:
                line_att_inconsistent.append({
                    'att_id': att.id,
                    'name': att.name,
                    'action': att.action,
                    'action_desc': att.action_desc.id,
                    'employee_id': att.employee_id.id,
                    'status': att.status,
#                    'is_inconsistent': att.is_inconsistent,
                })
        res.update({'line_ids':line_att_inconsistent})
        return res
    
    
                        
check_attendance_consistency_wizard()


class check_attendance_consistency_wizard_line(osv.osv_memory):
    
    _name = 'check.attendance.consistency.wizard.line'
    
    _columns = {
        'att_id':fields.many2one('hr.attendance', 'Attendance', required=False),
        'check_att_consis_id':fields.many2one('check.attendance.consistency.wizard', 'Check Attendance Consistency', required=False),
        'name': fields.datetime('Date'),
        'action': fields.selection([('sign_in', 'Sign In'), ('sign_out', 'Sign Out'), ('action','Action')], 'Action', required=True),
        'action_desc': fields.many2one("hr.action.reason", "Action Reason", domain="[('action_type', '=', action)]", help='Specifies the reason for Signing In/Signing Out in case of extra hours.'),
        'employee_id': fields.many2one('hr.employee', "Employee", required=True, select=True),
        #TODO: remove is_inconsistent field
        'status': fields.selection([('normal', 'Normal'),
                                    ('inconsistent', 'Inconsistent'),
                                    ('duplicate', 'Duplicate')], 
                                   string='Status', required=1),
        'is_inconsistent': fields.boolean('Is Inconsistent'),
    }

check_attendance_consistency_wizard_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
