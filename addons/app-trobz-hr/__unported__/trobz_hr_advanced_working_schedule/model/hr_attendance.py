# -*- encoding: utf-8 -*-

from openerp.osv import fields, osv
from datetime import datetime, timedelta
from openerp.tools.translate import _
from openerp.osv.osv import except_osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging

class hr_attendance(osv.osv):
    _inherit = "hr.attendance"
    
    _columns = {
        'inconsistence_reason': fields.text('Inconsistence Reason'),
        'computed_attendance': fields.datetime('Work From', help="When compute PWH, update this field current attendance that use to check recompute PWH or Not"),
        'pwh_id': fields.many2one('hr.payroll.working.hour', 'Payroll Working Hour'),
    }
    
    def compute_max_early_max_late(self, cr, uid, date_time, context=None):
        """
        
        """
        att_name = datetime.strptime(date_time, DEFAULT_SERVER_DATETIME_FORMAT)
        
        param_obj = self.pool.get('ir.config_parameter') 
        max_early = param_obj.get_param(cr, uid, 'maximum_early_minutes', default=60)
        max_late = param_obj.get_param(cr, uid, 'maximum_late_minutes', default=60)
        try:
            max_early = int (max_early)
            max_late = int (max_late)
        except:
            raise except_osv(_("Warning !"),_("maximum_early_minutes or maximum_late_minutes in config parameter is incorrect"))
                
        time_early = att_name + timedelta(minutes = max_early)
        time_late = att_name - timedelta(minutes = max_late)
        return time_early, time_late
    
    def check_first_sign_in(self, cr, uid, att, context=None):
        """
        In case have 2 shifts ( Payroll working hour, Overtime) consecutively.
        - On a  shift,  a sign-out is inconsistent if have no sign-in that belongs to this shift
        - If this inconsistent sign-out belongs to a shift which has another shift starts/ends at the same time.
          + If there is no sign-in nor sign-out at this time, create a two attendances (sign-in, sign-out) at this time automatically
           + If there is only one sign-in/sign-out at this time, do not create.
        """
        pre_att_ids = self.search(cr, uid, [('employee_id', '=', att.employee_id.id), 
                                            ('name', '<', att.name), 
                                            ('action', 'in', ('sign_in', 'sign_out'))], limit=1, order='name DESC')
        inconsistence_reason = ''
        if not pre_att_ids and att.action == 'sign_out':
            return True, 'First attendance must be sign in.'
        if not pre_att_ids:
            return False, inconsistence_reason
        pre_att = self.read(cr, uid, pre_att_ids[0], ['action', 'name'], context=context)
        if att.action == 'sign_out' and pre_att['action'] == 'sign_in':
            working_hour_obj = self.pool.get('hr.payroll.working.hour')
            
            # check 2 attendances have same working hour?
            time_early_late = self.compute_max_early_max_late(cr, uid, att.name, context=context)
            working_hour_ids = working_hour_obj.search(cr, uid, [('employee_id', '=', att.employee_id.id),
                                                              ('expected_start', '<=', time_early_late[0].strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                              ('expected_end', '>=', time_early_late[1].strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                            ], context=context, limit=1, order='expected_start')
#             working_hour_ids = working_hour_obj.search(cr, uid, [('employee_id', '=', att.employee_id.id),
#                                                               ('expected_start', '<=', att.name),
#                                                               ('expected_end', '>=', att.name),
#                                                             ], context=context)
            
            time_pre_early_late = self.compute_max_early_max_late(cr, uid, pre_att['name'], context=context)
            working_hour_pre_ids = working_hour_obj.search(cr, uid, [('employee_id', '=', att.employee_id.id),
                                                              ('expected_start', '<=', time_pre_early_late[0].strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                              ('expected_end', '>=', time_pre_early_late[1].strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                            ], context=context, limit=1, order='expected_start')
#             working_hour_pre_ids = working_hour_obj.search(cr, uid, [('employee_id', '=', att.employee_id.id),
#                                                               ('expected_start', '<=', pre_att['name']),
#                                                               ('expected_end', '>=', pre_att['name']),
#                                                             ], context=context)
            # check 2 attendances have same overtime ?
            overtime_obj = self.pool.get('hr.overtime')
            orertime_ids = overtime_obj.search(cr, uid, [('employee_id', '=', att.employee_id.id),
                                                         ('mode', '=', 'by_employee'),
                                                         ('datetime_start', '<=', time_early_late[0].strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                         ('datetime_stop', '>=', time_early_late[1].strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                         ('state', 'in', ['confirmed', 'done'])
                                                ])
            orertime_pre_ids = overtime_obj.search(cr, uid, [('employee_id', '=', att.employee_id.id),
                                                         ('mode', '=', 'by_employee'),
                                                         ('datetime_start', '<=', time_pre_early_late[0].strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                         ('datetime_stop', '>=', time_pre_early_late[1].strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                         ('state', 'in', ['confirmed', 'done'])
                                                ])
            # (overtime and working hours) are continuously.
            if working_hour_ids and not working_hour_pre_ids and not orertime_ids and orertime_pre_ids:
                working_start = working_hour_obj.read(cr, uid, working_hour_ids[0],['expected_start'], context=context)['expected_start']
                overtime_stop = overtime_obj.read(cr, uid, orertime_pre_ids[0],['datetime_stop'], context=context)['datetime_stop']
                # - 1 seconds
                working_stop_pre = datetime.strptime(overtime_stop, DEFAULT_SERVER_DATETIME_FORMAT) - timedelta(seconds = 1)
                self.create(cr, uid, {'name': working_stop_pre.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                      'action': 'sign_out',
                                      'employee_id': att.employee_id.id,
                                    }, context=context)
                self.create(cr, uid, {'name': working_start,
                                      'action': 'sign_in',
                                      'employee_id': att.employee_id.id,
                                    }, context=context)
#                 self.check_consistency(cr, uid, [att_new_id],context=context)
                return False, inconsistence_reason
            # (working hours and overtime) are continuously.
            if orertime_ids and not orertime_pre_ids and not working_hour_ids and working_hour_pre_ids:
                working_stop = working_hour_obj.read(cr, uid, working_hour_pre_ids[0],['expected_end'], context=context)['expected_end']
                overtime_start = overtime_obj.read(cr, uid, orertime_ids[0],['datetime_start'], context=context)['datetime_start']
                working_stop_pre = datetime.strptime(working_stop, DEFAULT_SERVER_DATETIME_FORMAT) - timedelta(seconds = 1)
                
                self.create(cr, uid, {'name': working_stop_pre.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                      'action': 'sign_out',
                                      'employee_id': att.employee_id.id,
                                    }, context=context)
                self.create(cr, uid, {'name': overtime_start,
                                      'action': 'sign_in',
                                      'employee_id': att.employee_id.id,
                                    }, context=context)
#                 self.check_consistency(cr, uid, [att_new_id],context=context)
                return False, inconsistence_reason
            if not orertime_ids and working_hour_ids and working_hour_ids != working_hour_pre_ids:
                inconsistence_reason = 'First attendance must be sign in every working hour.'
                return True, inconsistence_reason
            
            if not working_hour_ids and orertime_ids and orertime_ids != orertime_pre_ids:
                inconsistence_reason = 'First attendance must be sign in every overtime.'
                return True, inconsistence_reason
        return False, inconsistence_reason
    
    def check_wrong_time(self, cr, uid, att, context=None):
        """
        He works on wrong date or at wrong time.
        """
        # check have overtime yet?
        att_name = datetime.strptime(att.name, DEFAULT_SERVER_DATETIME_FORMAT)
        param_obj = self.pool.get('ir.config_parameter') 
        max_early = param_obj.get_param(cr, uid, 'maximum_early_minutes', default=60)
        max_late = param_obj.get_param(cr, uid, 'maximum_late_minutes', default=60)
        try:
            max_early = int (max_early)
            max_late = int (max_late)
        except:
            raise except_osv(_("Warning !"),_("maximum_early_minutes or maximum_late_minutes in config parameter is incorrect"))
                
        time_early = att_name + timedelta(minutes = max_early)
        time_late = att_name - timedelta(minutes = max_late)
        
        overtime_obj = self.pool.get('hr.overtime')
        overtime_confirmed_ids = overtime_obj.search(cr, uid, [('employee_id', '=', att.employee_id.id),
                                                     ('mode', '=', 'by_employee'),
                                                     ('name', '=', att.day_tz),
                                                     ('datetime_start', '<=', time_early.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                     ('datetime_stop', '>=', time_late.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                     ('state', 'in', ['confirmed'])
                                            ])
        if overtime_confirmed_ids:
            return False
        working_hour_obj = self.pool.get('hr.payroll.working.hour')
        
        
        
        
        working_hour_ids = working_hour_obj.search(cr, uid, [('employee_id', '=', att.employee_id.id),
                                                              ('expected_start', '<=', time_early.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                              ('expected_end', '>=', time_late.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                            ], context=context)
        if not working_hour_ids:
            return True
        return False
    
    def check_leave_request_holiday(self, cr, uid, att, context=None):
        """
        He creates a leave request on that date or that date is a public holiday but he still has a sign in / sign out on that date.
        """
        if att:
            # check have overtime yet?
            att_name = datetime.strptime(att.name, DEFAULT_SERVER_DATETIME_FORMAT)
            param_obj = self.pool.get('ir.config_parameter') 
            max_early = param_obj.get_param(cr, uid, 'maximum_early_minutes', default=60)
            max_late = param_obj.get_param(cr, uid, 'maximum_late_minutes', default=60)
            try:
                max_early = int (max_early)
                max_late = int (max_late)
            except:
                raise except_osv(_("Warning !"),_("maximum_early_minutes or maximum_late_minutes in config parameter is incorrect"))
                    
            time_early = att_name + timedelta(minutes = max_early)
            time_late = att_name - timedelta(minutes = max_late)
            
            overtime_obj = self.pool.get('hr.overtime')
            overtime_confirmed_ids = overtime_obj.search(cr, uid, [('employee_id', '=', att.employee_id.id),
                                                         ('mode', '=', 'by_employee'),
                                                         ('name', '=', att.day_tz),
                                                         ('datetime_start', '<=', time_early.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                         ('datetime_stop', '>=', time_late.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                         ('state', 'in', ['confirmed'])
                                                ])
            if overtime_confirmed_ids:
                return False
            
            public_holiday_obj = self.pool.get('trobz.hr.public.holidays')
            public_holiday_ids = public_holiday_obj.search(cr, uid, [('date', '=', att.day_tz), ('state', '=', 'approved')], context=context)
            if public_holiday_ids:
                return True
            sql = '''
                SELECT line.first_date_type, line.first_date, line.last_date_type, line.last_date
                FROM hr_holidays_line line JOIN hr_holidays h ON line.holiday_id = h.id
                WHERE h.employee_id = %d
                AND line.first_date <= '%s' AND line.last_date >= '%s'
                AND h.state = 'validate'
            '''% (att.employee_id.id, att.day_tz, att.day_tz)
            cr.execute(sql)
            for leave in cr.fetchall():
                if att.action == 'sign_out':
                    afternoon = datetime.strptime(att.name_tz, DEFAULT_SERVER_DATETIME_FORMAT).hour >= 13
                else:
                    afternoon = datetime.strptime(att.name_tz, DEFAULT_SERVER_DATETIME_FORMAT).hour >= 12
                if att.day_tz == leave[1]:
                    if leave[0] == 'afternoon' and afternoon:
                        return True
                    if  leave[0] == 'morning' and not afternoon:
                        return True
                    if leave[0] == 'full':
                        return True
                if att.day_tz == leave[3]:
                    if leave[2] == 'afternoon' and afternoon:
                        return True
                    if  leave[2] == 'morning' and not afternoon:
                        return True
                    if leave[2] == 'full':
                        return True
                if datetime.strptime(att.day_tz, '%Y-%m-%d') > datetime.strptime(leave[1], '%Y-%m-%d')\
                                and datetime.strptime(att.day_tz, '%Y-%m-%d') < datetime.strptime(leave[3], '%Y-%m-%d'):
                    return True
        return False
    
    def check_absent_pre_date(self, cr, uid, att, context=None):
        """
        An employee is absent but no leave request is created -> Mark the first sign in on next date to Inconsistent.
        """
        if att:
            # check employee absent pre date
            pre_att_ids = self.search(cr, uid, [('employee_id', '=', att.employee_id.id), 
                                                ('name', '<', att.name), 
                                                ('action', 'in', ('sign_in', 'sign_out'))], 
                                      limit=1)
            param_obj = self.pool.get('ir.config_parameter')
            working_hour_obj = self.pool.get('hr.payroll.working.hour')
            max_early = param_obj.get_param(cr, uid, 'maximum_early_minutes', default=60)
            max_late = param_obj.get_param(cr, uid, 'maximum_late_minutes', default=60)
            trobz_base_obj = self.pool.get('trobz.base')
            att_name = datetime.strptime(att.name_tz, DEFAULT_SERVER_DATETIME_FORMAT)
            try:
                max_early = int (max_early)
                max_late = int (max_late)
            except:
                raise except_osv(_("Warning !"),_("maximum_early_minutes or maximum_late_minutes in config parameter is incorrect"))
                    
            time_late = att_name - timedelta(minutes = max_late)
            
            working_hour_ids=[] #Payroll Working Hours (Only read working PWH, Not Leave or Overtime PWH) 
            if not pre_att_ids:
                working_hour_ids = working_hour_obj.search(cr, uid, [('employee_id', '=', att.employee_id.id),
                                                                     ('expected_end', '<', time_late.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                                     ('plan_line_id', '!=', False)
                                                                     ], 
                                                           context=context)
            else:
                pre_time_early = self.read(cr, uid, pre_att_ids[0], ['name_tz'], context=context)['name_tz']
                time_start_early = datetime.strptime(pre_time_early, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(minutes = max_early)
                working_hour_ids = working_hour_obj.search(cr, uid, [('employee_id', '=', att.employee_id.id),
                                                                     ('expected_start', '>', time_start_early.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                                     ('expected_end', '<', time_late.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                                     ('plan_line_id', '!=', False)
                                                                    ], context=context, order='date DESC')
            if not working_hour_ids:
                return False
            else:
                for working in working_hour_obj.browse(cr, uid, working_hour_ids, context=context):
                    # check public holiday
                    holiday_ids = self.pool.get('trobz.hr.public.holidays').search(cr, uid, [('date','=', working.date)], context=context) 
                    if holiday_ids:
                        return False
                    # full
                    sql = '''
                            SELECT line.id
                            FROM hr_holidays_line line JOIN hr_holidays h ON line.holiday_id = h.id
                            WHERE h.employee_id = %d
                            AND line.first_date < '%s' AND line.last_date > '%s'
                            AND h.state = 'validate'
                        '''% (working.employee_id.id, working.date, working.date)
                    cr.execute(sql)
                    if cr.fetchall():
                        continue
                    else:
                        sql = False
                        expected_start = trobz_base_obj.convert_from_utc_to_current_timezone(cr, uid, working.expected_start, False, DEFAULT_SERVER_DATETIME_FORMAT, False, context=context)
                        time_start = expected_start.hour
                        expected_end = trobz_base_obj.convert_from_utc_to_current_timezone(cr, uid, working.expected_end, False, DEFAULT_SERVER_DATETIME_FORMAT, False, context=context)
                        time_end = expected_end.hour
                        # wh afternoon
                        if time_start >= 12 and time_end >=12:
                            sql = '''
                                SELECT line.id
                                FROM hr_holidays_line line JOIN hr_holidays h ON line.holiday_id = h.id
                                WHERE h.employee_id = %d
                                AND (line.first_date = '%s' OR line.last_date = '%s')
                                AND h.state = 'validate'
                                AND (line.last_date_type = 'afternoon' OR line.first_date_type = 'afternoon')
                            '''% (working.employee_id.id, working.date, working.date)
                        # wh morning
                        elif time_start < 12 and time_end <= 12:
                            sql = '''
                                SELECT line.id
                                FROM hr_holidays_line line JOIN hr_holidays h ON line.holiday_id = h.id
                                WHERE h.employee_id = %d
                                AND (line.first_date = '%s' OR line.last_date = '%s')
                                AND h.state = 'validate'
                                AND (line.last_date_type = 'morning' OR line.first_date_type = 'morning')
                            '''% (working.employee_id.id, working.date, working.date)
                        
                        if sql:
                            cr.execute(sql)
                            if cr.fetchall():
                                continue
                        # wh full
                        sql = '''
                            SELECT line.id
                            FROM hr_holidays_line line JOIN hr_holidays h ON line.holiday_id = h.id
                            WHERE h.employee_id = %d
                            AND (line.first_date = '%s' OR line.last_date = '%s')
                            AND h.state = 'validate'
                            AND (line.last_date_type = 'full' OR line.first_date_type = 'full')
                        '''% (working.employee_id.id, working.date, working.date)
                        cr.execute(sql)
                        res = cr.fetchall()
                        if res or (time_late >= expected_start and time_late <= expected_end):
                            continue
                        return True
        return False
    
    def check_overtime(self, cr, uid, att, context=None):
        """
        this function return True if He works overtime but his overtime record 
            is not yet approved by HR Manager.
        """
        if att:
            overtime_obj = self.pool.get('hr.overtime')
            orertime_ids = overtime_obj.search(cr, uid, [('employee_id', '=', att.employee_id.id),
                                                         ('mode', '=', 'by_employee'),
                                                         ('name', '=', att.day_tz),
                                                         ('datetime_start', '<=', att.name),
                                                         ('datetime_stop', '>=', att.name),
                                                         ('state', 'not in', ['cancel', 'confirmed', 'done'])
                                                ])
            if orertime_ids:
                return True
        return False
    
    def check_consistency(self, cr, uid, ids, context=None):
        """
        #TODO: TO REVIEW CAREFULLY
        Check attendance: if attendance is inconsistency then show row red in tree
        Do not need to check the duplicate attendance
        """
        # Sort the given attendances by employee and date.
        select_sql = """
            SELECT employee_id, id
            FROM hr_attendance
            WHERE id IN (%s)
              AND active = 't'
            ORDER BY employee_id, name;
        """ %','.join(map(str, ids))
        cr.execute(select_sql)
        emp_att_dict = {}
        for att in cr.fetchall():
            if att[0] not in emp_att_dict:
                emp_att_dict[att[0]] = []
            emp_att_dict[att[0]].append(att[1])
        inconsistency_true = []
        inconsistency_false = []
        for emp_id, att_ids in emp_att_dict.iteritems():
            logging.info('>> Check attendance consistency of %s (%d)' % (emp_id, len(att_ids)))
            for att in self.browse(cr, uid, att_ids, context=context):
                # search and browse for first previous and first next records
                prev_att_ids = self.search(cr, uid, [('employee_id', '=', att.employee_id.id), ('name', '<', att.name), ('action', 'in', ('sign_in', 'sign_out'))], limit=1, order='name DESC')
                next_add_ids = self.search(cr, uid, [('employee_id', '=', att.employee_id.id), ('name', '>', att.name), ('action', 'in', ('sign_in', 'sign_out'))], limit=1, order='name ASC')
                prev_atts = self.browse(cr, uid, prev_att_ids, context=context)
                next_atts = self.browse(cr, uid, next_add_ids, context=context)
                
                # Two consecutive attendances have same action (Previous)
                if prev_atts and prev_atts[0].action == att.action: 
                    inconsistence_reason = 'Two consecutive attendances have same action. Attendance id: ('+ str(att.id) +'; ' + str(prev_att_ids[0]) + ')'
                    inconsistency_true.append({'att_id': att.id, 'reason': inconsistence_reason})
                    inconsistency_true.append({'att_id': prev_att_ids[0], 'reason': inconsistence_reason})
                    continue
                
                # Two consecutive attendances have same action (Next)
                if next_atts and next_atts[0].action == att.action: 
                    inconsistence_reason = 'Two consecutive attendances have same action. Attendance id:('+ str(att.id) +'; ' + str(next_add_ids[0]) + ')'
                    inconsistency_true.append({'att_id': att.id, 'reason': inconsistence_reason})
                    inconsistency_true.append({'att_id': next_add_ids[0], 'reason': inconsistence_reason})
                    continue
                
                # First attendance must be sign_in
                #TODO: merge with another case
                if (not prev_atts) and (not next_atts) and att.action != 'sign_in':
                    inconsistence_reason = 'First attendance must be sign in.'
                    inconsistency_true.append({'att_id':att.id, 'reason': inconsistence_reason})
                    continue
                
                # First shift (working hours or overtime) must sign_in
                # or (working hours and overtime) or (overtime and working hours) continuously
                check = self.check_first_sign_in(cr, uid, att, context=context)
                if att.action == 'sign_out' and check[0]:
                    inconsistency_true.append({'att_id':att.id, 'reason': check[1]})
                    continue
                
                # He works overtime but his overtime record is not yet approved by HR Manager.
                if self.check_overtime(cr, uid, att, context=context):
                    inconsistence_reason = 'He works overtime but his overtime record is not yet approved by HR Manager.'
                    inconsistency_true.append({'att_id':att.id, 'reason': inconsistence_reason})
                    continue
                # He works on wrong date or at wrong time.
                if self.check_wrong_time(cr, uid, att, context=context):
                    inconsistence_reason = 'He exchanges the shift with another worker but he has not got approval from HR Manager. OR He works on wrong date or at wrong time.'
                    inconsistency_true.append({'att_id': att.id, 'reason': inconsistence_reason})
                    continue
                # He creates a leave request on that date or that date is a public holiday but he still has a sign in / sign out on that date.
                if self.check_leave_request_holiday(cr, uid, att, context=context):
                    inconsistence_reason = 'He creates a leave request on that date or that date is a public holiday but he still has a sign in / sign out on that date.'
                    inconsistency_true.append({'att_id':att.id, 'reason': inconsistence_reason})
                    continue
                # An employee is absent but no leave request is created -> Mark the first sign in on next date to Inconsistent.
                if self.check_absent_pre_date(cr, uid, att, context=context):
                    inconsistence_reason = 'An employee is absent but no leave request is created'
                    inconsistency_true.append({'att_id':att.id, 'reason': inconsistence_reason})
                    continue
                
                # Consistent attendance
                inconsistency_false.append(att.id)
            if len(inconsistency_true) == 20:
                sql = ''
                for att_inconsistency in inconsistency_true:
                    sql += """
                        UPDATE hr_attendance 
                        SET status = 'inconsistent',
                        --is_inconsistent = True,
                            inconsistence_reason = '%s',
                            consistency_checked = True,
                            write_uid = %d,
                            write_date = NOW() AT TIME ZONE 'UTC'
                        WHERE id = %d;
                    """ % (att_inconsistency['reason'], uid, att_inconsistency['att_id'])
                cr.execute(sql)
                cr.commit()
                inconsistency_true = []
        
        # Set status is inconsistent if attendance is inconsistent       
        # [Removed] set is_inconsistent = True if attendance is inconsistent
        sql = ''
        for att_inconsistency in inconsistency_true:
            sql += """
                UPDATE hr_attendance 
                SET status = 'inconsistent',
                -- is_inconsistent = True,
                    inconsistence_reason = '%s',
                    consistency_checked = True,
                    write_uid = %d,
                    write_date = NOW() AT TIME ZONE 'UTC'
                WHERE id = %d;
            """ % (att_inconsistency['reason'], uid, att_inconsistency['att_id'])
        sql and cr.execute(sql)
        cr.commit()
        # Set status is normal if attendance is consistent       
        # [Removed] set is_inconsistent = False if attendance is consistent
        if inconsistency_false:
            sql='''
                UPDATE hr_attendance 
                SET status = 'normal',
                --is_inconsistent = False,
                    inconsistence_reason = '',
                    consistency_checked = True,
                    write_uid = %d,
                    write_date = NOW() AT TIME ZONE 'UTC'
                WHERE id in (%s);
            '''% (uid, ','.join(map(str,inconsistency_false)))
            cr.execute(sql)
        return True
    
    def recheck_attendance(self, cr, uid, ids, context=None):
        self.check_consistency(cr, uid, ids, context=context)
        return True
    
hr_attendance()
