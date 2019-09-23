# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
from openerp.tools.translate import _

class generate_working_hour_wizard(osv.osv_memory):
    _name = 'generate.working.hour.wizard'
    _description = 'Wizard allow to generate the payroll working hours'
    
    _columns = {
        'employee_ids': fields.many2many('hr.employee', 'rel_generate_working_hour_employee', 'wizard_id', 'employee_id', string="Employees", required=True),
        'from_date': fields.date('From Date', required=True),
        'to_date': fields.date('To Date'),
        'force': fields.boolean('Force'),
    }
    
    _defaults = {
        'force': True,
    }
    
    def _check_dates(self, cr, uid, ids, context=None):
        for obj in self.read(cr, uid, ids, ['from_date', 'to_date'], context=context):
            if obj['from_date'] and obj['to_date'] and obj['from_date'] > obj['to_date']:
                return False
        return True

    _constraints = [
        (_check_dates, 'Error! From-date must be less than to-date.', ['from_date', 'to_date'])
    ]
    
    def generate(self, cr, uid, ids, context=None):
        """
        Wizard to create/Override the payroll working hours 
        """
        pwh_obj = self.pool.get('hr.payroll.working.hour')
        mod_obj = self.pool.get('ir.model.data')
        
        data = self.read(cr, uid, ids[0], ['employee_ids', 'from_date', 'to_date', 'force'], context=context)
        employee_ids = data['employee_ids']
        str_from_date = data['from_date']
        str_to_date = data['to_date'] and data['to_date'] or data['from_date']
        force = data['force']
        
        pwh_ids = pwh_obj.generate_payroll_working_hour(cr, uid, employee_ids, str_from_date, str_to_date, force=force, context=context)
        
        form_id = mod_obj.get_object_reference(cr, uid, 'trobz_hr_payroll_working_hour', 'view_hr_payroll_working_hour_form')
        form_res = form_id and form_id[1] or False
        tree_id = mod_obj.get_object_reference(cr, uid, 'trobz_hr_payroll_working_hour', 'view_hr_payroll_working_hour_tree')
        tree_res = tree_id and tree_id[1] or False
        
        return {
            'name':_("Computed Payroll Working Hours"),
            'view_mode': 'tree, form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'hr.payroll.working.hour',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': "[('id', 'in', [%s])]" %','.join(map(str, pwh_ids)),
            'views': [(tree_res, 'tree'), (form_res, 'form')],
            }
    
generate_working_hour_wizard()
