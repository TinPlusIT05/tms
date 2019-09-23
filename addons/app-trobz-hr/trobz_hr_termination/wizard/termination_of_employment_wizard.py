# -*- coding: utf-8 -*-
from openerp.osv import osv, fields
from datetime import date
from openerp.tools.translate import _

class termination_of_employment_wizard(osv.osv_memory):
    _name = 'termination.employment.wizard'
    _description = 'Termination of Employment'
    _columns = {
        'employee_ids': fields.many2many(
            'hr.employee', 'terminate_employment', 'terminate_id',
            'employee_id', string="Employees", required=True),
        'date_end': fields.date('Date End', required=True),
    }
    
    def apply(self, cr, uid, ids, context=None):
        """
        Cancel all info related with the selected employees:
            - Employees: Inactive
            - Contracts: update date-end is the selected date
            - Leaves/allocation requests: cancel all ones.
        """
        employee_obj = self.pool['hr.employee']
        contract_obj = self.pool['hr.contract']
        holiday_obj = self.pool['hr.holidays']
        if not ids:
            return True
        
        termination_employments = self.read(
            cr, uid, ids, ['employee_ids', 'date_end'], context=context)
        for termination_employment in termination_employments:
            employee_ids = termination_employment['employee_ids']
            date_end_wizard = termination_employment['date_end']
            if date_end_wizard > date.today().strftime('%Y-%m-%d'):
                raise osv.except_osv(
                    _('Warning!'),
                    _("The termination date must be now or in the past."))

            # Update date_end of contract of employees to be date_end of wizard
            # if date_end in contract over date_end in wizard
            contract_ids = contract_obj.search(
                cr, uid, [('employee_id', 'in', employee_ids),
                          ('date_start', '<=', date_end_wizard),
                          '|', ('date_end', '=', False),
                          ('date_end', '>', date_end_wizard)],
                context=context)
            if contract_ids:
                contract_obj.write(
                    cr, uid, contract_ids, {'date_end': date_end_wizard },
                    context=context)

            # Cancel all hr.holidays after date-end-wizard
            holiday_ids = holiday_obj.search(
                cr, uid, [('employee_id', 'in', employee_ids)],
                context=context)
            if holiday_ids:
                holiday_obj.write(
                    cr, uid, holiday_ids, {'state': 'cancel'}, context=context)                    
            
            # Inactive employees
            employee_obj.write(
                cr, uid, employee_ids, {'active': False}, context=context)
        return True

termination_of_employment_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
