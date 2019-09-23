# -*- encoding: utf-8 -*-
##############################################################################

from openerp.osv import osv, fields
from openerp import netsvc

class hr_overtime(osv.osv):
    _inherit = 'hr.overtime' 
    _states = {'done': [('readonly', True)]}
    
    _columns = {
        'working_activity_id':fields.many2one('hr.working.activity', 'Working Activity', required=True, readonly=False, states=_states), 
    }
    
    def overtime_confirm(self, cr, uid, ids, context=None):
        """
        Override function
        Action to confirm this overtime
        For overtime mode is "Employees", Create overtime for each employee.
            - Add a field working activity when creating by using mode "Employees"
        """
        res = self.write(cr, uid, ids, {'state': 'confirmed'}, context=context)
        wf_service = netsvc.LocalService("workflow")
        for overtime in self.read(cr, uid, ids, context=context):
            if overtime['mode'] == 'by_employees':
                vals = {
                    'name': overtime['name'],
                    'month_year': overtime['month_year'],
                    'mode': 'by_employee',
                    'datetime_start': overtime['datetime_start'],
                    'datetime_stop': overtime['datetime_stop'],
                    'break_start': overtime['break_start'],
                    'break_stop': overtime['break_stop'],
                    'break_hour': overtime['break_hour'],
                    'working_hour': overtime['working_hour'],
                    'working_activity_id': overtime['working_activity_id'] and overtime['working_activity_id'][0] or False,
                    'type': overtime['type'],
                    'compensation_date': overtime['compensation_date'],
                    'reason': overtime['reason']
                }
                # generate overtime for every employee
                for employee_id in overtime['employee_ids']:
                    contract_ids = self.pool.get('hr.contract').get_contract(cr, uid, employee_id, overtime['name'], context=context)
                    if contract_ids:
                        vals.update({'employee_id': employee_id,
                                     'contract_id': contract_ids[0]})
                        overtime_id = self.create(cr, uid, vals, context=context)
                        wf_service.trg_validate(uid, 'hr.overtime', overtime_id, 'button_confirm', cr)
                res = self.write(cr, uid, ids, {'state': 'done'}, context=context)
        return res
    
    def onchange_working_activity_id(self, cr, uid, ids, working_activity_id, context=None):
        """
        @param Working_activity_id: Select working activity
        @return: Overtime type 
        """
        res = {'value':{}}
        if not working_activity_id:
            return res
        
        working_act = self.pool.get('hr.working.activity').browse(cr, uid, working_activity_id, context=context)
        over_type = 'overtime'
        if working_act.type and working_act.type != 'overtime':
            over_type = 'compensation'
        res['value'].update({'type': over_type})
        return res
    
hr_overtime()
