# -*- encoding: utf-8 -*-
##############################################################################

from openerp.osv import osv, fields
from datetime import datetime
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _

class hr_overtime(osv.osv):
    _name = 'hr.overtime'
    _inherit = 'mail.thread' 
    _description = 'Trobz HR Overtime'
    _order = 'name DESC, employee_id'
    _states = {'done': [('readonly', True)]}
    
    _columns = {
        'name': fields.date('Overtime Date', required=True, readonly=False, states=_states),
        'month_year': fields.char('Month/Year', size=8),
        'employee_ids': fields.many2many('hr.employee', 'overtime_employee_rel',
                                          'overtime_id', 'employee_id',
                                          string='List of Employees', required=False, readonly=False, states=_states),
        'employee_id':fields.many2one('hr.employee', 'Employee', required=False, readonly=False, states=_states), 
        'mode': fields.selection([
                                  ('by_employee', 'For a single employee'),
                                  ('by_employees', 'For a group of employees'),
                                 ],'Mode', select=True, readonly=False, required=True),
        'state': fields.selection([
                                   ('draft','Draft'),
                                   ('confirmed','Confirmed'),
                                   ('cancel','Cancelled'),
                                   ('done','Done'),
                                   ],'State', select=True, readonly=True),
        'datetime_start': fields.datetime('DateTime Start', required=True),
        'datetime_stop': fields.datetime('DateTime End', required=True),
        'break_start': fields.datetime('Break Start'),
        'break_stop': fields.datetime('Break End'),
        'break_hour': fields.float('Break Hours', digits=(16,2), readonly=True),
        'working_hour': fields.float('Expected Working Hours', digits=(16,2), readonly=True,
                                     help="Expected Working Hours is the result of (start - end)"),
        'type': fields.selection([
                                  ('compensation','Compensation'),
                                  ('overtime','Overtime'),
                                  ], 'Type'), 
        'compensation_date': fields.date('Compensation Date', readonly=False, states=_states,
                                         help="On the compensation date, this employee absent. So, this employee must be compensated for this date on the register date"),
        'reason': fields.text('Reason of the Overtime'),
        'contract_id': fields.many2one('hr.contract', 'Contract'),
    }
    
    _defaults = {
        'state': lambda *a: 'draft',
        'mode': lambda *a: 'by_employees',
        'type': lambda *a: 'overtime'
    }
    
    def _check_overlapped(self, cr, uid, ids, context=None):
        """
        Check for overlapped overtime.
        """
        for overtime in self.read(cr, uid, ids, ['name', 'mode', 'employee_id', 
                                                 'datetime_start', 'datetime_stop'],
                                  context=context):
            if overtime['mode'] == 'by_employees':
                continue
            overlapped_ids = self.search(cr, uid, [('employee_id', '=', overtime['employee_id'][0]),
                                                   ('id', '!=', overtime['id']),
                                                   ('mode', '!=', 'by_employees'),
                                                   '|', '|', '&', ('datetime_start', '<=', overtime['datetime_start']),
                                                   ('datetime_stop', '>=', overtime['datetime_start']),
                                                   '&', ('datetime_start', '<=', overtime['datetime_stop']),
                                                   ('datetime_stop', '>=', overtime['datetime_stop']),
                                                   '&', ('datetime_start', '>=', overtime['datetime_start']),
                                                   ('datetime_stop', '<=', overtime['datetime_stop'])],
                                         context=context, limit=1)
            if overlapped_ids:
                return False
        return True
    
    def _check_dates(self, cr, uid, ids, context=None):
        """
        Check datetime_stop > datetime_start
        """
        for overtime in self.read(cr, uid, ids, ['datetime_start', 'datetime_stop'], context=context):
            if overtime['datetime_start'] and overtime['datetime_stop'] and overtime['datetime_start'] >= overtime['datetime_stop']:
                return False
        return True
    
    def _check_register_date(self, cr, uid, ids, context=None):
        """
        Check register date = datetime start
        """
        for overtime in self.read(cr, uid, ids, ['datetime_start', 'name'], context=context):
            if overtime['datetime_start'][0:10] != overtime['name']:
                return False
        return True
    
    def _check_break_dates(self, cr, uid, ids, context=None):
        """
        Check break_stop > break_start
        """
        for overtime in self.read(cr, uid, ids, ['break_start', 'break_stop', 
                                                 'datetime_start', 'datetime_stop'], 
                                  context=context):
            if overtime['break_start'] and overtime['break_stop'] and overtime['break_start'] >= overtime['break_stop']:
                return False
            
            if overtime['break_start'] and overtime['break_stop'] and\
                overtime['datetime_start'] and overtime['datetime_stop'] and\
                (overtime['break_start'] <= overtime['datetime_start'] or\
                overtime['break_stop'] >= overtime['datetime_stop']):
                return False
        return True

    def _check_hour(self, cr, uid, ids, context=None):
        """
        Check overtime hour > 0
        """
        for overtime in self.read(cr, uid, ids, ['working_hour'], context=context):
            if overtime['working_hour'] <= 0:
                return False
        return True
    
    _constraints = [
        (_check_hour, 'Error! The overtime hours must be greater than 0.', ['working_hour']),
        (_check_dates, 'Error! datetime-stop must be less than datetime-start.', ['datetime_start', 'datetime_stop']),
        (_check_break_dates, 'Error! break-stop must be less than break-start or break-start and break-stop must be within datetime-start and datetime-stop', 
            ['break_start', 'break_stop', 'datetime_start', 'datetime-stop']),
        (_check_overlapped, 'An overtime of this employee has already existed!', ['name', 'employee_id']),
        (_check_register_date, 'Error! The Register Date and Datetime-Start must be the same date.', ['name', 'datetime_start'])
    ]
    
    def overtime_draft(self, cr, uid, ids, context=None):
        """
        Draft this overtime
        """
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)
    
    def overtime_confirm(self, cr, uid, ids, context=None):
        """
        Action to confirm this overtime
        For overtime mode is "By employees", Create overtime for each employee.
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
                    'type': overtime['type'],
                    'compensation_date': overtime['compensation_date'],
                    'reason': overtime['reason']
                }
                # Generate overtime records for selected employees
                for employee_id in overtime['employee_ids']:
                    contract_ids = self.pool.get('hr.contract').get_contract(cr, uid, employee_id, overtime['name'], context=context)
                    if contract_ids:
                        vals.update({'employee_id': employee_id,
                                     'contract_id': contract_ids[0]})
                        overtime_id = self.create(cr, uid, vals, context=context)
                        wf_service.trg_validate(uid, 'hr.overtime', overtime_id, 'button_confirm', cr)
                res = self.write(cr, uid, ids, {'state': 'done'}, context=context)
        return res
    
    def overtime_done(self, cr, uid, ids, context=None):
        """
        Done this overtime
        """
        return self.write(cr, uid, ids, {'state': 'done'}, context=context)
    
    def overtime_cancel(self, cr, uid, ids, context=None):
        """
        Cancel this overtime
        """
        return self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
    
    def button_set_to_draft(self, cr, uid, ids, context=None):
        """
        Button set this overtime to draft
        """
        res = self.write(cr, uid, ids, {'state': 'draft'}, context=context)
        wf_service = netsvc.LocalService("workflow")
        for overtime_id in ids:
            wf_service.trg_create(uid, 'hr.overtime', overtime_id, cr)
        return res
    
    def onchange_employee_id(self, cr, uid, ids, mode, employee_id, date, context=None):
        """
        @param mode: by employee/by employees
        @param employee_id: employee id
        @param date: (string) overtime date  
        @return: contract_id
        """
        res = {'value':{}}
        if mode == 'by_employee':
            contract_ids = self.pool.get('hr.contract').get_contract(cr, uid, employee_id, date, date, context=context)
            if not contract_ids:
                raise osv.except_osv(_("Warning!"), _("Please setup the labor contract of this employee"))
            res['value'].update({'contract_id': contract_ids[0]})
        return res
    
    def onchange_mode(self, cr, uid, ids, mode):
        """
        If overtime mode change to "by_employee" mode, set null employee_ids
        If overtime mode change to "by_employees" mode, set null employee_id
        @param mode: Select an employee/list of employees
        @return: employee_ids or employee_ids
        """
        if mode == 'by_employee':
            return {'value': {'employee_ids': [(6, 0, [])]}}
        return {'value': {'employee_id': False}}
    
    def diff_hour(self, datetime_start, datetime_stop):
        """
        Delta hours between datetime start to datetime stop
        """
        diff = datetime_stop - datetime_start
        return float(diff.days)* 24 + (float(diff.seconds) / 3600)
    
    def onchange_start_stop(self, cr, uid, ids, name, mode, employee_id, 
                            str_datetime_start, str_datetime_stop,
                            str_break_start, str_break_stop,
                            context=None):
        """
        @param str_datetime_start: Select Datetime start (string)
        @param str_datetime_stop: Select Datetime stop (string)
        @param str_break_start: Select Datetime start (string)
        @param str_break_stop: Select Datetime stop (string)
        @param employee_id: employee-id
        @param mode: mode: employee/employees
        @param name: current overtime date
        @return: name, working hour, month_year, contract_id
        """
        res = {'value': {'break_hour':0,
                         'working_hour': 0, 
                         'month_year': '',
                         'contract_id': False,
                         'name':''}}
        
        if not str_datetime_start or not str_datetime_stop:
            return res
        
        # Calculate break_hour = break_stop - break_start
        break_hour = 0
        if str_break_start and str_break_stop:
            break_start = datetime.strptime(str_break_start, DEFAULT_SERVER_DATETIME_FORMAT)
            break_stop = datetime.strptime(str_break_stop, DEFAULT_SERVER_DATETIME_FORMAT)
            break_hour = self.diff_hour(break_start, break_stop)
            res['value']['break_hour'] = break_hour
            
        # Calculate break_hour = datetime_stop - datetime_start - break_hour
        datetime_start = datetime.strptime(str_datetime_start, DEFAULT_SERVER_DATETIME_FORMAT)
        datetime_stop = datetime.strptime(str_datetime_stop, DEFAULT_SERVER_DATETIME_FORMAT)
        res['value']['working_hour'] = self.diff_hour(datetime_start, datetime_stop) - break_hour
        
        # Calculate overtime date, month/year
        res['value']['name'] = datetime_start.strftime(DEFAULT_SERVER_DATE_FORMAT)
        res['value']['month_year'] = datetime_start.strftime('%m/%Y')
        
        # Get valid contract on datetime_start
        if mode == 'by_employee' and employee_id:
            contract_ids = self.pool.get('hr.contract').get_contract(cr, uid, employee_id, name, name, context=context)
            if not contract_ids:
                raise osv.except_osv(_("Warning!"), _("Please setup the labor contract of this employee"))
            res['value']['contract_id'] = contract_ids[0]
        return res
    
    def unlink(self, cr, uid, ids, context=None):
        """
        Only allow to unlink overtime records that are not done
        """
        overtime_unlink = []
        for overtime in self.read(cr, uid, ids, ['state'], context=context):
            if overtime['state'] not in ['done']:
                overtime_unlink.append(overtime['id'])
        if overtime_unlink:
            return super(hr_overtime, self).unlink(cr, uid, overtime_unlink, context=context)
        return False
    
hr_overtime()
