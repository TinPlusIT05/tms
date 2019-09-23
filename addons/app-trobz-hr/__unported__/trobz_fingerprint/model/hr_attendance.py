# -*- coding: utf-8 -*-

from openerp.osv import osv
import urllib2
import json
from datetime import datetime, timedelta
from openerp.osv.osv import except_osv
from openerp.tools.translate import _
import unicodedata
from openerp import tools
from operator import itemgetter
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

import logging
_logger = logging.getLogger(__name__)

ACTION_IN = ('I', '1', 'i')
ACTION_OUT = ('O', '0', 'o')
DEFAULT_DATETIME_FORMAT_FINGERPRINT = '%m/%d/%Y %I:%M:%S %p'

class hr_attendance(osv.osv):
    _inherit = 'hr.attendance'
    
    def convert_to_nomalize(self, name):
        name_convert = ''.join((c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn'))
        str_name_convert = name_convert.encode('utf8')
        if 'Đ' or 'đ' in str_name_convert:
            name_convert = str_name_convert.replace('Đ', 'D') or str_name_convert.replace('đ', 'd') 
        return name_convert
    
    def get_phone_number(self, number):
        phone_number = filter(str.isdigit,str(number) )[:20]
        return phone_number
    
    def update_status_duplicate(self, cr, uid, attendances, time_delay=3, context=None):
        """
        *** Update status for each attendance
        Avoid to import duplicated attendances before insert into openerp system.
        If the gap between two attendances is less than delay amount, they are considered duplicated.
        Examples: Delay = 3 minutes. 2014-04-27 11:14:15 and 2014-04-27 11:16:17 are duplicated.
        First attendance will be removed from the final result.
        """
        _logger.info('===================== START update_status_duplicate ============')
        if not attendances:
            _logger.info('===================== STOP update_status_duplicate ============')
            return attendances
        
        # If the gap between two attendances is less than delay amount, they are considered duplicated.
        # Examples: Delay = 3 minutes. 2014-04-27 11:14:15 and 2014-04-27 11:16:17 are duplicated.
        # First attendance will be updated: status=duplicate, active=False
        # Sort the attendances by SSN and by Date
        attendances = sorted(attendances, key=itemgetter('SSN', 'Date'))
        updated_attendances = [] # Include all attendances after updating duplicate attendance
        # Process to delete duplicated attendances
        while attendances:
            first_att = attendances.pop(0)
            if attendances:
                second_att = attendances[0]
                if first_att['SSN'] == second_att['SSN']:
                    first_datetime = datetime.strptime(first_att['Date'], DEFAULT_DATETIME_FORMAT_FINGERPRINT)
                    second_datetime = datetime.strptime(second_att['Date'], DEFAULT_DATETIME_FORMAT_FINGERPRINT)
                    # Gap between two attendances is less then the time_delay
                    if first_datetime <= (second_datetime  + timedelta(minutes=time_delay))\
                        and first_datetime >= (second_datetime - timedelta(minutes=time_delay)):
                        first_att.update(status='duplicate', active=False)
                        _logger.warning('[1] Attendance %s will be created with status is duplicate!' % str(first_att))
            updated_attendances.append(first_att)
        _logger.info('===================== STOP update_status_duplicate ============')
        return updated_attendances
    
    def check_attendance_exist(self, cr, uid, condition, context=None):
        """
        check if attendance existing then don't insert attendance into system
        """
        if condition:
            attendance_ids = self.search(cr, uid, condition, limit=1, context=context)
            if attendance_ids:
                return True
        return False
    
    def run_get_data_from_finger_machine(self, cr, uid, context=None):
        """
        Get the attendances from fingerprint software's database and import them into ERP.
        """
        _logger.info('>>>>>>BEGIN GET DATA FINGER PRINT')
        data = []
        employee_name = self.pool.get('hr.employee')
        trobz_base = self.pool.get('trobz.base')
        employee_dict = {} # {Internal ID: Employee ID}
        
        # Get url from Connection Config which 'url_type','=','check'
        connection_obj = self.pool.get('connection.config')
        connection_ids =  connection_obj.search(cr, uid, [('url_type', '=', 'check')],
                                                context=context)
        connection_config_data = connection_obj.read(cr, uid, connection_ids, ['url', 'url_type', 'last_check_date',
                                                                               'date_run_again', 'b_run_again'],
                                                     context = context)
        # Get the delay amount (in minutes)
        time_delay = self.pool.get('ir.config_parameter').get_param(cr, uid, 'default_delay_fingerprint', default=3)
        try:
            time_delay = int(time_delay)
        except:
            _logger.error('Cannot convert time_delay %s into integer!' % time_delay)
            time_delay = 3
        
        for config_data in connection_config_data:
            last_check_date = config_data['last_check_date'] and str(config_data['last_check_date']).split('.')[0] or ''
            _logger.info('[UTC] last_check_date %s' % last_check_date)
            last_check_date_tz = trobz_base.convert_from_utc_to_current_timezone(cr, uid, last_check_date)
            _logger.info('[Current Time Zone] last_check_date %s' % last_check_date_tz)
            last_check_date = last_check_date_tz.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            if last_check_date:
                date_data = {
                    "CHECK": last_check_date and str(last_check_date).split('+')[0] or ''
                }
                data.append(date_data)
            date_to = False
            if config_data['b_run_again']:
                date_again = config_data['date_run_again'] and str(config_data['date_run_again']).split('.')[0] or ''
                if date_again:
                    date_to = trobz_base.convert_from_utc_to_current_timezone(cr, uid, date_again)
            _logger.info('Get attendance from %s to %s', last_check_date, date_to or 'now')
            
            if config_data['url']:
                #change data to json type
                data = json.dumps(data)
                request = urllib2.Request(str(config_data['url']), data, {'Content-Type': 'application/json'})
                try:
                    # connect to webApi
                    f = urllib2.urlopen(request)
                    received_attendances = f.read()
                    f.close()
                except:
                    raise except_osv(_("Warning !"),_("Could not connect to WebApi"))
                try:
                    if received_attendances:
                        # receive response from webAPI
                        # ["{'Date': '9/20/2013 3:25:31 PM', 'Action': 'O', 'SSN': '000003'}"]
                        received_attendances = eval(received_attendances.replace( '\"',''))
                        values = []
                        
                        """ Update status is duplicate for all duplicate attendances"""
                        attendances = self.update_status_duplicate(cr, uid, received_attendances,
                                                                   time_delay=time_delay, context=context)
                        for attendance in attendances:
                            if attendance['SSN'] not in employee_dict:
                                employee_ids = employee_name.search(cr, uid, [('internal_id', '=', attendance['SSN'])],
                                                                    context=context)
                                employee_id = employee_ids and employee_ids[0] or False
                                employee_dict[attendance['SSN']] = employee_id
                            else:
                                employee_id = employee_dict.get(attendance['SSN'], False)
                            if not employee_id:
                                _logger.warning('[2] Attendance %s is ignored!' % str(attendance))
                                continue
                            
                            date_utc = trobz_base.convert_from_current_timezone_to_utc(cr, uid, attendance['Date'],
                                                                                       datetime_format=DEFAULT_DATETIME_FORMAT_FINGERPRINT)
                            date_tz = datetime.strptime(attendance['Date'], DEFAULT_DATETIME_FORMAT_FINGERPRINT)
                            day_tz = date_tz.strftime(DEFAULT_SERVER_DATE_FORMAT)
                            name_tz = date_tz.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                            if date_to and date_utc > date_to:
                                _logger.warning('[3] Attendance %s is ignored!' % str(attendance))
                                continue
                            
                            value = False
                            condition_check = []
                            date_3_greater = date_utc + timedelta(minutes=time_delay)
                            date_3_less = date_utc - timedelta(minutes=time_delay)
                            
                            # condition to check attendances is existing yet?
                            condition_check = [
                                ('employee_id','=', employee_id),
                                ('name', '<=', date_3_greater.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                ('name', '>=', date_3_less.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
                            ]

                            val = """
                            (%d, '%s', '%s', '%s', '%s', %d, NOW() AT TIME ZONE 'UTC', 
                            '%s', False, %d, NOW() AT TIME ZONE 'UTC', %s)
                            """
                            # Exist key status, active if attendance is duplicated 
                            status = attendance.get('status', 'normal')
                            active = attendance.get('active', True)
                            
                            if attendance['Action'] in ACTION_IN:
                                value = val% (employee_id, 'sign_in', 
                                              date_utc.strftime(DEFAULT_SERVER_DATETIME_FORMAT), 
                                              name_tz, day_tz, uid, status, uid, active)
                            elif attendance['Action'] in ACTION_OUT:
                                value = val% (employee_id, 'sign_out', 
                                              date_utc.strftime(DEFAULT_SERVER_DATETIME_FORMAT), 
                                              name_tz, day_tz, uid, status, uid, active)
                            else:
                                _logger.warning('[4] Attendance %s is ignored!' % str(attendance))

                            if value and not self.check_attendance_exist(cr, uid, condition_check, context=context):
                                values.append(value)
                            else:
                                _logger.warning('Attendance %s is existed!' % str(attendance))
                        if values:
                            sql = '''
                                INSERT INTO hr_attendance(employee_id, action, name, name_tz, 
                                day_tz, write_uid, write_date, status, consistency_checked, 
                                create_uid, create_date, active)
                                VALUES 
                            '''
                            sql += ','.join(values)
                            cr.execute(sql)
                            cr.commit()
                            _logger.info('>>>>>>CHECK CONSISTENCY')
                            
                            # Check attendance
                            #TODO: Improve speed of check consistency
                            att_ids = self.search(cr, uid, [('consistency_checked', '=', False)],
                                                  context=context)
                            self.check_consistency(cr, uid, att_ids, context=context)
                except Exception as exc:
                    raise except_osv(_("Warning !"),_("There is an error while getting attendances: %s" % exc))
                
                #write the last date run Check In/Out
                connection_obj.write(cr, uid, [config_data['id']], {'last_check_date': datetime.now(), 'b_run_again': False}, context=context)
            else:
                raise except_osv(_("Warning !"),_("You must put correct URL to connect WebApi !!!"))
        _logger.info('>>>>>>END GET DATA FINGER PRINT')
        return True
    
    
    
    def run_post_data_to_finger_machine(self, cr, uid, context = None):
        _logger.info('>>>>>>BEGIN POST DATA FINGER PRINT')
        is_production_instance = tools.config.get('is_production_instance', False)
        if not is_production_instance:
            return False
        # get url, type
        connection_obj = self.pool.get('connection.config')
        connection_ids =  connection_obj.search(cr, uid, [], context = context)
        urls = connection_obj.read(cr, uid, connection_ids, ['url', 'url_type', 'last_check_date'], context=context)
        urls_dict = {}
        for url in urls:
            _logger.info('>>>>>>URL TYPE %s'%(url))
            #delete 
            if url['url_type'] == 'delete':
                urls_dict.update({
                    'delete': url
                })
            #edit
            elif url['url_type'] == 'update':
                urls_dict.update({
                    'update': url
                })
            #create
            elif url['url_type'] == 'create':
                urls_dict.update({
                    'create': url
                })
        
        self.delete_employee(cr, uid, urls_dict.get('delete', False), context)
        self.edit_employee(cr, uid, urls_dict.get('update', False), context)
        self.create_employee(cr, uid, urls_dict.get('create', False), context)
        
        _logger.info('>>>>>>END POST DATA FINGER PRINT')
        return True
    
    def delete_employee(self, cr, uid, config_data, context = None):
        """
        When an employee is deleted in OpenERP, delete related user(s) in the attendance software.
        """
        if not config_data:
            return False
        if context is None:
            context = {}
        context['delete_from_sync'] = True
        
        # Find all employees that have been deleted or inactivated
        # but still exist in fingerprint records.
        select_sql = """
            SELECT fre.id, fre.id_remote
            FROM fingerprint_record fre
            WHERE fre.is_deleted != 't'
                AND fre.active = 't'
                AND fre.model = 'hr.employee'
                AND fre.id_src NOT IN (
                    SELECT hem.id
                    FROM hr_employee hem
                        JOIN resource_resource rre
                            ON rre.id = hem.resource_id
                                AND rre.active = 't'
                );
        """
        cr.execute(select_sql)
        remote_data = []
        inactive_finger_ids = []
        for fingerprint_record in cr.fetchall():
            # Append the remote id to send to API
            remote_data.append({
                "REMOTE": str(fingerprint_record[1])
            })
            # Append fingerprint id to list of ids that will be inactivate
            inactive_finger_ids.append(fingerprint_record[0])
        
        # Update related fingerprint records: set is_deleted to True and active to False.
        if inactive_finger_ids:
            fingerprint_obj = self.pool.get('fingerprint.record')
            fingerprint_obj.write(cr, uid, inactive_finger_ids, {'is_deleted': True,
                                                                 'active': False},
                                  context=context)
        
        if remote_data:
            remote_data = json.dumps(remote_data)
            if config_data['url']:
                req = urllib2.Request(str(config_data['url']), remote_data, {'Content-Type': 'application/json'})
                try:
                    f = urllib2.urlopen(req)
                    f.close()
                except:
                    raise except_osv(_("Warning !"),_("Could not connect to WebApi"))
            else:
                raise except_osv(_("Warning !"),_("You must put correct URL to connect WebApi !!!"))
            
        #write last date run Delete to Connection Config
        connection_obj = self.pool.get('connection.config')
        connection_obj.write(cr, uid, [config_data['id']], {'last_check_date': datetime.now()}, context=context)
        return True
    
    def edit_employee(self, cr, uid, config_data, context = None):
        """
        When there is an update of employee, update information for related user in the software.
        """
        select_sql = """
            SELECT hem.id, hem.internal_id, hem.name_related, hem.birthday,
                hem.hire_date, hem.work_phone, hem.mobile_phone, hem.write_date
            FROM hr_employee hem
                JOIN resource_resource rre
                    ON hem.resource_id = rre.id
                        AND rre.active = 't'
            WHERE hem.write_date > '%s'
                AND EXISTS (
                    SELECT 1
                    FROM fingerprint_record fre
                    WHERE fre.id_src = hem.id
                        AND fre.active = 't'
                        AND fre.is_deleted != 't'
                )
            ORDER BY hem.id;
        """ % config_data['last_check_date']
        cr.execute(select_sql)
        remote_data = []
        for employee in cr.fetchall():
            remote_data.append({
                "SSN": employee[1], # internal_id
                "Name": self.convert_to_nomalize(employee[2]), # name_related
                "Birthday": employee[3] or "", # birthday
                "DateHire": employee[4] or "", # hire_date
                "WorkPhone": self.get_phone_number(employee[5]) or "", # work_phone
                "WorkMobile": self.get_phone_number(employee[6]) or "", # mobile_phone
            })
        
        if remote_data:
            remote_json_data = json.dumps(remote_data)
            if config_data['url']:
                req = urllib2.Request(str(config_data['url']), remote_json_data, {'Content-Type': 'application/json'})
                try:
                    f = urllib2.urlopen(req)
                    responses = f.read()
                except:
                    raise except_osv(_("Warning !"),_("Could not connect to WebApi"))
                try:
                    if responses:
                        # Type of response is string like ["{'userid':'vals','ssn':vals}"]
                        responses = eval(responses.replace( '\"',''))
                        ids_remote = []
                        for response in responses:
                            print response
                            ids_remote.append(response['USERID'])
                        if ids_remote:
                            update_sql = """
                                UPDATE fingerprint_record
                                SET date = NOW() AT TIME ZONE 'UTC'
                                WHERE id_remote IN (%s);
                            """ % ','.join(map(str, ids_remote))
                            cr.execute(update_sql)
                    f.close()
                except Exception as exc:
                    raise except_osv(_("Warning !"),_("There is an error while getting attendances: %s" % exc))
            else:
                raise except_osv(_("Warning !"),_("You must put correct URL to connect WebApi !!!"))
            
            #write last date run Update to Connection Config
            connection_obj = self.pool.get('connection.config')
            connection_obj.write(cr, uid, [config_data['id']], {'last_check_date': datetime.now()}, context=context)
        return True
    
    def create_employee(self, cr, uid, url, context = None):
        """
        When an employee is created in OpenERP
         - Create a user in fingerprint software
         - Create a fingerprint record
        """
        # Find all active employees that do NOT have a fingerprint record yet.
        select_sql = """
            SELECT hem.id, hem.internal_id, hem.name_related, hem.birthday,
                hem.hire_date, hem.work_phone, hem.mobile_phone
            FROM hr_employee hem
                JOIN resource_resource rre
                    ON rre.id = hem.resource_id
                        AND rre.active = 't'
            WHERE hem.internal_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1
                    FROM fingerprint_record fre
                    WHERE fre.id_src = hem.id
                        AND fre.model = 'hr.employee'
            )
            ORDER BY hem.internal_id;
        """
        cr.execute(select_sql)
        employee_obj = self.pool.get('hr.employee')
        data = []
        
        # Read info of new employees
        for employee in cr.fetchall():
            data.append({
                "SSN": employee[1], # internal_id
                "Name": self.convert_to_nomalize(employee[2]), # name_related
                "Birthday": employee[3] or "", # birthday
                "DateHire": employee[4] or "", # hire_date
                "WorkPhone": self.get_phone_number(employee[5]) or "", # work_phone
                "WorkMobile": self.get_phone_number(employee[6]) or "", # mobile_phone
            })
        
        if data:
            data = json.dumps(data)
            if url['url']:
                req = urllib2.Request(str(url['url']), data, {'Content-Type': 'application/json'})
                try:
                    f = urllib2.urlopen(req)
                    responses = f.read()
                except ValueError:
                    raise except_osv(_("Warning !"),_("Could not connect to WebApi %s")%ValueError)
                try:
                    if responses:
                        #Type of respone is string like ["{'userid':'vals','ssn':vals}"]
                        responses = eval(responses.replace( '\"',''))
                        fingers_pool = self.pool.get('fingerprint.record')
                        for response in responses:
                            employee_ids = employee_obj.search(cr, uid, [('internal_id', '=', response['SSN'])],
                                                               context=context, limit=1)
                            employee_id = employee_ids and employee_ids[0] or False
                            if not employee_id:
                                continue
                            record_ids = fingers_pool.search(cr, uid, [('model','=','hr.employee'),
                                                                       ('id_src','=',employee_id)],
                                                             context=context )
                            if not record_ids: 
                                data = {
                                    'id_src': employee_id,
                                    'id_remote': response['USERID'],
                                    'model': 'hr.employee',
                                    'date': datetime.now(),
                                }
                                fingers_pool.create(cr, uid, data, context=context)
                    f.close()
                except Exception as exc:
                    raise except_osv(_("Warning !"),_("There is an error while getting attendances: %s" % exc))
            else:
                raise except_osv(_("Warning !"),_("You must put correct URL to connect WebApi !!!"))
            
            #write last date run Create to Connection Config
            connection_obj = self.pool.get('connection.config')
            connection_obj.write(cr, uid, [url['id']], {'last_check_date': datetime.now()}, context=context)
        return True
    
hr_attendance()
