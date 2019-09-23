# -*- coding: utf-8 -*-
from openerp.tools.translate import _

from openerp.osv import osv, fields
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from itertools import groupby
from operator import itemgetter

class hr_attendance(osv.osv):
    _inherit = 'hr.attendance'
    _order = 'employee_id, name desc'
    
    _columns = {
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the analytic journal without removing it."),
        'status': fields.selection([('normal', 'Normal'),
                                    ('inconsistent', 'Inconsistent'),
                                    ('duplicate', 'Duplicated')
                                    ], 
                                   string='Status', required=1, readonly=True),
        #TODO: remove is_inconsistent field 
        'is_inconsistent': fields.boolean('Is Inconsistent'), 
        'consistency_checked':fields.boolean('Consistency Checked'), 
        'name_tz': fields.datetime('Date TZ'),
        'day_tz': fields.char('Date TZ', size=64, required=False, readonly=False),
    }
    
    def _altern_si_so(self, cr, uid, ids, context=None):
        return True
    
    _defaults = {
        'status': 'normal',
        'active': True,  
        'consistency_checked': False,
    }
    
    _constraints = [(_altern_si_so, 'Error ! Sign in (resp. Sign out) must follow Sign out (resp. Sign in)', ['action'])]
    
    def compute_total_attendance(self, cr, uid, employee_id, date_from, date_to, context=None):                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
        """
        Compute total attendance of a employee from date_from to date_to
        Should be compute the Total Attendance when the attendance datas is correct
        If the attendances (sign in/sign out) is incorrect. Show the error message.
        Incorrect attendances mean:
            - Exist a attendance is error. Error field will be updated when import attendances for some case below:
                + Two consecutive sign ins / sign outs
                + Missing sign in before sign out 
            - The last attendance is sign in
        """
        total_attendance = 0
        # Check incorrect attendances
        # [removed] is_inconsistent
        attendance_error_ids = self.search(cr, uid, [('employee_id','=',employee_id),
                                                     ('name','>=',date_from),
                                                     ('name','<=',date_to),
                                                     ('status','=','inconsistent'),
                                                     ('action','in',('sign_in', 'sign_out'))
                                                     ],
                                           order='name',
                                           context=context)
        
        if attendance_error_ids:
            raise osv.except_osv(_('Warning!'),_('Some attendances are inconsistent. Please fix the attendances before generating the employee productivity.'))
        
        # Read all attendance datas from date_from to date_to
        attendance_ids = self.search(cr, uid, [('employee_id','=',employee_id),
                                               ('name','>=',date_from),
                                               ('name','<=',date_to),
                                               ('action','in',('sign_in', 'sign_out'))
                                              ],
                                     order='name',
                                     context=context)
        attendance_datas_tz = self.read(cr, uid, attendance_ids, ['name', 'day', 'action'], context=context)
        #change time zone
        trobz_base_obj = self.pool.get('trobz.base')
        attendance_datas = []
        for att in attendance_datas_tz:
            date_tz = trobz_base_obj.convert_from_utc_to_current_timezone(cr, uid, att['name'], False, DEFAULT_SERVER_DATETIME_FORMAT, False, context=context)
            print 'date_tz:',date_tz.strftime('%Y-%m-%d %H:%M:%S') 
            att.update({'name': date_tz.strftime('%Y-%m-%d %H:%M:%S'), 'day': date_tz.strftime('%Y-%m-%d')})
            attendance_datas.append(att)
        # Sort attendances by sign in/sign out datetime 
        sorted_attendance_datas = sorted(attendance_datas, key = lambda x: (x['name']))
        # Group attendances by day (date of sign in/sign out datetime), the attandance datas sort by name 
        grouped_attendance_datas = dict((day, [line for line in attendance_lines]) for day, attendance_lines in groupby(sorted_attendance_datas, itemgetter('day')))
        for atts_in_day in grouped_attendance_datas.values():
            #Check incorrect attendances: The last attendance is sign in
            if atts_in_day[-1]['action'] == 'sign_in':
                raise osv.except_osv(_('Warning!'),_('Some attendances are inconsistent. Please fix the attendances before generating the employee productivity.'))
            #Correct attendances:
            while len(atts_in_day) >= 2:  
                sign_in_date = datetime.strptime(atts_in_day[0]['name'], DEFAULT_SERVER_DATETIME_FORMAT)
                sign_out_date = datetime.strptime(atts_in_day[1]['name'], DEFAULT_SERVER_DATETIME_FORMAT)
                diff = sign_out_date - sign_in_date
                duration = float(diff.days)* 24 + (float(diff.seconds) / 3600)                    
                total_attendance += duration
                atts_in_day = atts_in_day[2:] 
        return total_attendance
    
    def set_is_inconsistency(self, cr, uid, ids, status, context=None):
        """
        Set status is inconsistent if attendance is inconsistency
        Removed is_inconsistent
        """
        sql='''
            UPDATE hr_attendance 
            SET status = '%s',
                write_uid = %d,
                write_date = NOW()
            WHERE id in %s;
        '''% (status, uid, str('('+','.join(str(int(i)) for i in ids)+')'))
        return sql
    
    def check_inconsistency_end_begin_day(self, cr, uid, employee_id, context=None):
        """
        if end day is sign in ==> inconsistency
        if begin day is sign out ==> inconsistency
        """
        attendance_error_ids = []
        attendance_ids = self.search(cr, uid, [('employee_id','=',employee_id),
                                                     ('action','in',('sign_in', 'sign_out'))],
                                           order='name',
                                           context=context)
        attendance_datas_tz = self.read(cr, uid, attendance_ids, ['name', 'day', 'action'], context=context)
        #change time zone
        trobz_base_obj = self.pool.get('trobz.base')
        attendance_datas = []
        for att in attendance_datas_tz:
            date_tz = trobz_base_obj.convert_from_utc_to_current_timezone(cr, uid, att['name'], False, DEFAULT_SERVER_DATETIME_FORMAT, False, context=context)
            print 'date_tz:',date_tz.strftime('%Y-%m-%d %H:%M:%S') 
            att.update({'name': date_tz.strftime('%Y-%m-%d %H:%M:%S'), 'day': date_tz.strftime('%Y-%m-%d')})
            attendance_datas.append(att)
        # Sort attendances by sign in/sign out datetime 
        sorted_attendance_datas = sorted(attendance_datas, key = lambda x: (x['name']))
        # Group attendances by day (date of sign in/sign out datetime), the attandance datas sort by name 
        grouped_attendance_datas = dict((day, [line for line in attendance_lines]) for day, attendance_lines in groupby(sorted_attendance_datas, itemgetter('day')))
        for atts_in_day in grouped_attendance_datas.values():
            #Check incorrect attendances: The last attendance is sign in
            if atts_in_day[-1]['action'] == 'sign_in':
                attendance_error_ids.append(atts_in_day[-1]['id'])
            if atts_in_day[0]['action'] == 'sign_out':
                attendance_error_ids.append(atts_in_day[0]['id'])
        return attendance_error_ids
    
    def get_att_same_day(self, cr, uid, att_1, att_ids, context=None):
        """
        search all att_ids have same day with att_1
        """
        trobz_base_obj = self.pool.get('trobz.base')
        if not att_1 or not att_ids:
            return []
        result = []
        att_1 = self.browse(cr, uid, att_1, context=context)
        att_tz_1 = trobz_base_obj.convert_from_utc_to_current_timezone(cr, uid, att_1.name, False, DEFAULT_SERVER_DATETIME_FORMAT, False, context=context)
        for att in self.browse(cr, uid, att_ids, context=context):
            att_tz = trobz_base_obj.convert_from_utc_to_current_timezone(cr, uid, att.name, False, DEFAULT_SERVER_DATETIME_FORMAT, False, context=context)
            if att_tz_1.strftime('%Y-%m-%d') == att_tz.strftime('%Y-%m-%d'):
                result.append(att.id)
        return result
    
    def check_consistency(self, cr, uid, ids, context=None):
        """
        check attendance: if attendance is inconsistency then show row red in tree
        TODO: To review, to merge with the changes in trobz_hr_advanced_working_schedule
        """
        today = datetime.now().date()
        trobz_base_obj = self.pool.get('trobz.base')
        inconsistency_true = []
        inconsistency_false = []
        for att in self.browse(cr, uid, ids, context=context):
            # search and browse for first previous and first next records
            prev_att_ids = self.search(cr, uid, [('employee_id', '=', att.employee_id.id), ('name', '<', att.name), ('action', 'in', ('sign_in', 'sign_out'))], limit=1, order='name DESC')
            next_add_ids = self.search(cr, uid, [('employee_id', '=', att.employee_id.id), ('name', '>', att.name), ('action', 'in', ('sign_in', 'sign_out'))], limit=1, order='name ASC')
            prev_atts = self.browse(cr, uid, prev_att_ids, context=context)
            next_atts = self.browse(cr, uid, next_add_ids, context=context)
            # previous exists and is same action
            if prev_atts and prev_atts[0].action == att.action: 
                inconsistency_true.append(att.id)
                inconsistency_true.append(prev_att_ids[0])
                continue
            # next exists and is same action
            if next_atts and next_atts[0].action == att.action: 
                inconsistency_true.append(att.id)
                inconsistency_true.append(next_add_ids[0])
                continue
            # first attendance must be sign_in
            if (not prev_atts) and (not next_atts) and att.action != 'sign_in': 
                inconsistency_true.append(att.id)
                continue
            # if end day is sign_in, begin day is sign_out
            # sign_in end day and diff today
            att_sign_out = self.search(cr, uid, [('employee_id', '=', att.employee_id.id), ('name', '>', att.name), ('action', '=', 'sign_out')])
            att_sign_out_day = self.get_att_same_day(cr, uid, att.id, att_sign_out, context=context)
            if att.action == 'sign_in' and not(att_sign_out_day):
                date_tz = trobz_base_obj.convert_from_utc_to_current_timezone(cr, uid, att.name, False, DEFAULT_SERVER_DATETIME_FORMAT, False, context=context)
                if today.strftime('%Y-%m-%d') != date_tz.strftime('%Y-%m-%d'):
                    inconsistency_true.append(att.id)
                    continue
            # sign_out begin day
            att_sign_in = self.search(cr, uid, [('employee_id', '=', att.employee_id.id), ('name', '<', att.name), ('action', '=', 'sign_in')])
            att_sign_in_day = self.get_att_same_day(cr, uid, att.id, att_sign_in, context=context)
            if att.action == 'sign_out' and not(att_sign_in_day):
                inconsistency_true.append(att.id)
                continue
            inconsistency_false.append(att.id)
        
        # Set status is inconsistent if attendance is inconsistent
        # [Removed] set is_inconsistent = True if attendance is inconsistent
        if inconsistency_true:
            sql='''
                UPDATE hr_attendance 
                SET status = 'inconsistent',
                --is_inconsistent = True,
                    consistency_checked = True,
                    write_uid = %d,
                    write_date = NOW()
                WHERE id in (%s);
            '''% (uid, ','.join(map(str,inconsistency_true)))
            cr.execute(sql)
        # Set status is normal if attendance is consistent
        # [Removed] is_inconsistent = False if attendance is consistent
        if inconsistency_false:
            sql='''
                UPDATE hr_attendance 
                SET status = 'normal',
                --is_inconsistent = False,
                    consistency_checked = True,
                    write_uid = %d,
                    write_date = NOW()
                WHERE id in (%s);
            '''% (uid, ','.join(map(str,inconsistency_false)))
            cr.execute(sql)
        return True
    
    def get_attendance_in_month(self, cr, uid, employee_ids, context=None):
        """
        Get all attendance of employee in month
        """
        # Get the current date
        today = date.today()
        # Find the first day and last day of this month (UTC)
        first_day = today + relativedelta(day=1)
        last_day = today + relativedelta(day=1, months=1, days=-1)
        first_day = first_day.strftime(DEFAULT_SERVER_DATE_FORMAT) + ' 00:00:00'
        last_day = last_day.strftime(DEFAULT_SERVER_DATE_FORMAT) + ' 23:59:59'
        
        search_domain = [('name', '>=', first_day), ('name', '<=', last_day)]
        if employee_ids:
            search_domain.append(('employee_id', 'in', employee_ids))
        month_att_ids = self.search(cr, uid, search_domain, context=context,
                                    order='employee_id, name desc')
        return month_att_ids
    
    def write(self, cr, uid, ids, vals, context=None):
        """
        Get date attendance changed time zone
        """
        if vals.get('name', False):
            trobz_base_obj = self.pool.get('trobz.base')
            date_tz = trobz_base_obj.convert_from_utc_to_current_timezone(cr, uid, vals['name'], False, DEFAULT_SERVER_DATETIME_FORMAT, False, context=context)
            if vals.get('day_tz', False):
                vals['day_tz'] = date_tz.strftime('%Y-%m-%d')
            else:
                vals.update({'day_tz': date_tz.strftime('%Y-%m-%d'), 'name_tz': date_tz.strftime('%Y-%m-%d %H:%M:%S')})
        super(hr_attendance, self).write(cr, uid, ids, vals, context=context)
        if vals.get('name', False) or vals.get('action', False):
            self.check_consistency(cr, uid, ids,context=context)
            employee_ids = [att.employee_id.id for att in self.browse(cr, uid, ids, context=context)]
            att_ids = self.get_attendance_in_month(cr, uid, employee_ids, context=context)
            if att_ids:
                self.check_consistency(cr, uid, att_ids, context=context)
        return True
    
    def create(self, cr, uid, vals, context=None): 
        # change time zone
        if vals.get('name', False):
            trobz_base_obj = self.pool.get('trobz.base')
            date_tz = trobz_base_obj.convert_from_utc_to_current_timezone(cr, uid, vals['name'], False,DEFAULT_SERVER_DATETIME_FORMAT, False, context=context)
            if vals.get('day_tz', False):
                vals['day_tz'] = date_tz.strftime('%Y-%m-%d')
            else:
                vals.update({'day_tz': date_tz.strftime('%Y-%m-%d'), 'name_tz': date_tz.strftime('%Y-%m-%d %H:%M:%S')})
        att_id = super(hr_attendance, self).create(cr, uid, vals, context=context)
        self.check_consistency(cr, uid, [att_id],context=context)
        employee_ids = [att.employee_id.id for att in self.browse(cr, uid, [att_id], context=context)]
        att_ids = self.get_attendance_in_month(cr, uid, employee_ids, context=context)
        if att_ids:
            self.check_consistency(cr, uid, att_ids, context=context)
        return att_id
    
    def unlink(self, cr, uid, ids, context=None):
        check_att_ids = []
        for att in self.browse(cr, uid, ids, context=context):
            prev_att_ids = self.search(cr, uid, [('employee_id', '=', att.employee_id.id), ('name', '<', att.name), ('action', 'in', ('sign_in', 'sign_out'))], limit=1, order='name DESC')
            next_add_ids = self.search(cr, uid, [('employee_id', '=', att.employee_id.id), ('name', '>', att.name), ('action', 'in', ('sign_in', 'sign_out'))], limit=1, order='name ASC')
            check_att_ids += prev_att_ids or []
            check_att_ids += next_add_ids or []
        check_att_ids = list(set(check_att_ids)-set(ids))
        res = super(hr_attendance, self).unlink(cr, uid, ids, context=context)
        if check_att_ids:
            self.check_consistency(cr, uid, check_att_ids, context=context)
        return res
    
    
hr_attendance()
