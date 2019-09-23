# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp.tools.translate import _

class hr_payslip_employees(osv.osv_memory):

    _inherit ='hr.payslip.employees'
    
    def compute_sheet(self, cr, uid, ids, context=None):
        """
        Override function
        Create the payslips of the selected employees on wizard 
        Add field the year of 13th month salary
        Add company_id from the on change fnct result
        """
        emp_pool = self.pool.get('hr.employee')
        slip_pool = self.pool.get('hr.payslip')
        run_pool = self.pool.get('hr.payslip.run')
        slip_ids = []
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context=context)[0]
        run_data = {}
        if context and context.get('active_id', False):
            run_data = run_pool.read(cr, uid, context['active_id'], ['date_start', 'date_end', 'credit_note', 'thirdteenth_year', 'journal_id'])
        from_date =  run_data.get('date_start', False)
        to_date = run_data.get('date_end', False)
        credit_note = run_data.get('credit_note', False)
        thirdteenth_year = run_data.get('thirdteenth_year', False)
        journal_id =  run_data.get('journal_id', False)
        journal_id = journal_id and journal_id[0] or False
        
        if not data['employee_ids']:
            raise osv.except_osv(_("Warning!"), _("You must select employee(s) to generate payslip(s)."))
        for emp in emp_pool.browse(cr, uid, data['employee_ids'], context=context):
            slip_data = slip_pool.onchange_employee_id(cr, uid, [], from_date, to_date, emp.id, contract_id=False, context=context)
            res = {
                'employee_id': emp.id,
                'name': slip_data['value'].get('name', False),
                'struct_id': slip_data['value'].get('struct_id', False),
                'contract_id': slip_data['value'].get('contract_id', False),
                'payslip_run_id': context.get('active_id', False),
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids', False)],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids', False)],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': credit_note,
                'thirdteenth_year': thirdteenth_year,
                'company_id': slip_data['value'].get('company_id', False),
                'journal_id': journal_id,
            }
            slip_ids.append(slip_pool.create(cr, uid, res, context=context))
        slip_pool.compute_sheet(cr, uid, slip_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}

hr_payslip_employees()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
