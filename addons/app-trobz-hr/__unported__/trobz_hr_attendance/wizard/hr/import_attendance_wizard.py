# -*- coding: utf-8 -*-
from openerp.osv import osv,fields
from openerp.tools.translate import _
import base64
import csv
import cStringIO
import logging
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class import_attendance_wizard(osv.osv_memory):
    
    _name = 'import.attendance.wizard'
    
    _columns = {
        'csv_file': fields.binary('File CSV', filters='*.csv,*.txt', required=True),
    }
    
    quotechar = '"'
    
    def import_attendance(self, cr, uid, ids,  context=None, dict_fields={'employee': 'name_related', 'action_reason': 'name'}):
        if context is None:
            context = {}
            
        logging.info('Begin to insert attendance ...')
        try:
            HEADER_COMMA = u'''"Employee","Date","Action","Action Reason"'''
            HEADER_SEMIC = u'''"Employee";"Date";"Action";"Action Reason"'''
            employee_obj = self.pool.get('hr.employee')
            action_reason_obj = self.pool.get('hr.action.reason')
            attendance_obj = self.pool.get('hr.attendance')
            attendance_error_obj = self.pool.get('import.attendance.error')
            for data in self.read(cr, uid, ids, ['csv_file'], context=context):
                if not data['csv_file']:
                    raise osv.except_osv(_('Error!'), _('Cannot read the csv file!'))
    
                content = base64.decodestring(data['csv_file'])
                delimeter_detected = self.pool.get('trobz.csv').check_valid_content_and_detect_delimeter(cr, uid, content, 4, HEADER_COMMA, HEADER_SEMIC, context=context)
                
                csv_input = cStringIO.StringIO(content)
                reader = csv.reader(csv_input, quotechar=self.quotechar, delimiter=delimeter_detected)
                header = True
                
                if not reader:
                    return
                
                attendance_lines = []
                is_error = False
                # delete attendance error
                attendance_error_ids = attendance_error_obj.search(cr, uid, [])
                attendance_error_obj.unlink(cr, uid, attendance_error_ids)
                
                for row in reader:
                    if not row or header:
                        header = False
                        continue
                    # get employee
                    employee_ids = employee_obj.search(cr, uid, [(dict_fields.get('employee'), '=', row[0].strip())])
                    if not employee_ids:
                        error = 'Not Found employee ' + row[0].strip()
                        error_vals = self.prepare_date(cr, uid, row[0], row[1], row[2], row[3], error)
                        attendance_error_obj.create(cr, uid, error_vals, context)
                        is_error = True
                        continue
                    # get date
                    attendance_date =  row[1].strip()
                    try:
                        name = self.pool.get('trobz.base').convert_from_current_timezone_to_utc(cr, uid, datetime.strptime(attendance_date, "%Y-%m-%d %H:%M:%S"), context=context)
                    except:
                        error = 'Date is not correct ' + attendance_date
                        error_vals = self.prepare_date(cr, uid, row[0], row[1], row[2], row[3], error)
                        attendance_error_obj.create(cr, uid, error_vals, context)
                        is_error = True
                        continue
                    # get action
                    action_code = ''
                    action = row[2].strip()
                    if action not in ['Sign In','Sign Out','Action']:
                        error = 'Not Found Action ' + row[2].strip()
                        error_vals = self.prepare_date(cr, uid, row[0], row[1], row[2], row[3], error)
                        attendance_error_obj.create(cr, uid, error_vals, context)
                        is_error = True
                        continue
                    actions = {'Sign In': 'sign_in', 'Sign Out': 'sign_out', 'Action': 'action'}
                    if action and actions.get(action):
                        action_code = actions[action]     
                    # get action reason
                    action_reason_ids = action_reason_obj.search(cr, uid, [(dict_fields.get('action_reason'), '=', row[3].strip())])
                    if not action_reason_ids and row[3].strip():
                        error = 'Not Found Action Reason ' + row[3].strip()
                        error_vals = self.prepare_date(cr, uid, row[0], row[1], row[2], row[3], error)
                        attendance_error_obj.create(cr, uid, error_vals, context)
                        is_error = True
                        continue 
                    #create attendance line
                    
                    vals = {
                            'employee_id': employee_ids[0],
                            'name': name.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                            'action': action_code,
                            'action_desc' : action_reason_ids and action_reason_ids[0] or False,
                            }
                    attendance_lines.append(vals)
            if not is_error:
                attendance_ids = []
                for vals in attendance_lines: 
                    attendance_id = attendance_obj.create(cr, uid, vals)
                    attendance_ids.append(attendance_id)
                return {'type': 'ir.actions.act_window',
                        'res_model': 'hr.attendance',
                        'name': 'Attendances',
                        'view_mode': 'tree',
                        'res_id': attendance_ids,
                    }
            else:
                return {'type': 'ir.actions.act_window',
                        'res_model': 'import.attendance.error',
                        'name': 'Imported Attendance Error', 
                        'view_mode': 'tree',}
        except ValueError:
            raise osv.except_osv(_('Error!'), _('Please check file input !'))
        logging.info('Done ...')
        return True
    
    def prepare_date(self, cr, uid, *arg):
        vals = {}
        if arg:
            vals['employee_id'] = arg[0]
            vals['date'] = arg[1]
            vals['action'] = arg[2]
            vals['action_reason_id'] = arg[3]
            vals['error'] = arg[4]
        return vals
        
import_attendance_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

