# -*- coding: utf-8 -*-
from openerp.osv import osv
from datetime import date


class hr_contract(osv.Model):
    _inherit = "hr.contract"

    def _track_job_history(
            self, cr, uid, contract, current_job,
            date_of_change=False, context=None):
        """
        Prepare values of history record
        @param contract: browse_record of the changed contract
        @param current_job: new job is selected on contract
        @param date_of_change: if not inputed, contract date start or today
        """
        if context is None:
            context = {}
        his_obj = self.pool['hr.job.history']
        employee = contract.employee_id
        department_id = contract.department_id \
            and contract.department_id.id or False
        if not date_of_change:
            date_of_change = date.today()
        job_history = {
            'name': 'Change position of %s' % employee.name,
            'employee_id': employee.id,
            'contract_id': contract.id,
            'department_id': department_id,
            'previous_job_id': False,
            'current_job_id': current_job,
            'date_of_change': date_of_change,
            'responsible_user_id': uid,
        }
        latest_job_history_ids = his_obj.search(
            cr, uid, [('employee_id', '=', employee.id)],
            order='date_of_change DESC', limit=1,
            context=context
        )
        if not latest_job_history_ids:
            # The first history record
            # Previous job is job of this contract
            job_history.update({
                'previous_job_id': contract.job_id
                and contract.job_id.id or False,
                'date_of_change': contract.date_start,
            })
        else:
            # Change job on contract
            # Previous job is job of previous history record
            latest_job_history = his_obj.browse(
                cr, uid, latest_job_history_ids[0], context=context
            )
            job_history.update({
                'previous_job_id': latest_job_history.current_job_id.id,
            })
        his_obj.create(cr, uid, job_history, context=context)

    def create(self, cr, uid, vals, context=None):
        """
        Create history record when creating a contract
        """
        contract_id = super(hr_contract, self).create(cr, uid, vals, context)
        contract = self.browse(cr, uid, contract_id, context=context)
        self._track_job_history(
            cr, uid, contract, vals.get('job_id', False), context=context
        )
        return contract_id

    def write(self, cr, uid, ids, vals, context=None):
        """
        Create history record when updating job title on this contract
        """
        if vals.get('job_id', False):
            for contract in self.browse(cr, uid, ids, context=context):
                self._track_job_history(
                    cr, uid, contract, vals['job_id'], context=context
                )
        return super(hr_contract, self).write(cr, uid, ids, vals, context)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
