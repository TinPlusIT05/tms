# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
from openerp.tools import  DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _
import logging

#TODO: Check unique a payroll working hour: date, employee, advanced working schedule, working activity, state

class hr_payroll_working_hour(osv.osv):
    _inherit = 'hr.payroll.working.hour'
    
    _columns = {
        ##########IMPORTANT####################
        #Update the plan_line_id when create a payroll working hour 
        #Do not allow to delete plan line link to payroll working hour 
        #Handle case plan line update starting date (remove starting date)
        #Only cancel the payroll working hours of this plan_line_id 
        
        'plan_line_id': fields.many2one('resource.calendar.attendance', 'Advanced Working Plan Template Line'),
        'is_flexible': fields.boolean('Flexible Day', readonly=True, states={'draft':[('readonly',False)]}),
        'advanced_schedule_id': fields.many2one("hr.advanced.working.schedule", "Advanced Working Schedule", readonly=True, states={'draft':[('readonly',False)]}),
        'contract_id': fields.many2one('hr.contract', 'Contract', readonly=True, states={'draft':[('readonly',False)]}),
        'overtime_id': fields.many2one('hr.overtime', 'Overtime'),
        'leave_line_id': fields.many2one('hr.holidays.line', 'Leave Line'),
        'public_holiday_id': fields.many2one('trobz.hr.public.holidays', 'Public Holiday'),
        #When re-compute dayoff PWH, Some fields need to be revert base on the field below
        'old_activity_id': fields.many2one('hr.working.activity', 'Old Working Activity', help="Use to revert the working activity. Update new one when compute PWH and revert old one when re-compute PWH"),
        'old_expected_start': fields.datetime('Old Expected Start'),
        'old_expected_end': fields.datetime('Old Expected End'),
        'old_break_start': fields.datetime('Old Break Start'),
        'old_break_end': fields.datetime('Old Break End'),
        'old_break_time': fields.float('Old Break Time'),
        'old_expected_working_hour': fields.float('Old Expected Working Hour'),
        
    }
    
    _defaults = {
        'is_flexible': False,
    }
    
    def _check_date(self, cr, uid, ids):
        for pwh in self.browse(cr, uid, ids):
            pwh_ids = self.search(cr, uid, [('expected_start', '<=', pwh.expected_end), 
                                            ('expected_end', '>=', pwh.expected_start), 
                                            ('employee_id', '=', pwh.employee_id.id), 
                                            ('id', '<>', pwh.id)])
            if pwh_ids:
                return False
        return True
    
    _constraints = [
        (_check_date, 'You can not have 2 payroll working hours that overlaps on same period!', ['expected_start','expected_end']),
    ]
    
    def onchange_advanced_schedule_id(self, cr, uid, ids, employee_id, str_date, advanced_schedule_id, context=None): 
        """
        @param str_date: (string) str_date
        @param advance_schedule_id: Advance working Schedule
        @return: 
            Contract
            Working Activity
            Expected Start
            Expected End
            Working Hours
            Break Start 
            Break End
            Break hours
        """
        time_obj = self.pool.get('hr.advanced.working.time')
        schedule_obj = self.pool.get('hr.advanced.working.schedule')
        if not advanced_schedule_id or not employee_id or not date:
            return {}
       
        schedule = schedule_obj.browse(cr, uid, advanced_schedule_id, context=context)
        schedule_data = {}
        if schedule:
            activity_id = schedule.activity_id.id
            work_from = time_obj.compute_datetime(cr, uid, str_date, schedule.work_from.id, context=context)
            work_to = time_obj.compute_datetime(cr, uid, str_date, schedule.work_to.id, context=context)
            str_work_from = work_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            str_work_to = work_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            expected_working_hour = time_obj.diff_hour(work_from, work_to)
            
            break_hour = 0.0
            str_break_from = ''
            str_break_to = ''
            if schedule.break_from and schedule.break_to:
                break_from = time_obj.compute_datetime(cr, uid, str_date, schedule.break_from.id, context=context)
                break_to = time_obj.compute_datetime(cr, uid, str_date, schedule.break_to.id, context=context)
                str_break_from = break_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                str_break_to = break_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                break_hour = time_obj.diff_hour(break_from, break_to)
            
            contract_ids = self.pool.get('hr.contract').get_contract(cr, uid, employee_id, str_date, str_date, context=context)
            if not contract_ids:
                raise osv.except_osv(_("Warning!"), _("Please setup the labor contract of this employee"))
            if str_break_from == '' or str_break_to == '':
                schedule_data = {'activity_id': activity_id,
                                 'contract_id': contract_ids[0],
                                 'expected_start': str_work_from,
                                 'expected_end': str_work_to,
                                 'break_start': False,
                                 'break_end': False,
                                 'expected_working_hour':expected_working_hour - break_hour
                                }
            else:
                schedule_data = {'activity_id': activity_id,
                                 'contract_id': contract_ids[0],
                                 'expected_start': str_work_from,
                                 'expected_end': str_work_to,
                                 'break_start': str_break_from,
                                 'break_end': str_break_to,
                                 'break_time': break_hour,
                                 'expected_working_hour':expected_working_hour - break_hour
                                 }
        return {'value': schedule_data}
    
    def _create_pwh_sql(self, insert_data):
        """
        GENERATE PWH
        Build sql to insert PWH when generate PWH
        """
        if not insert_data:
            return ''
        sql = """INSERT INTO hr_payroll_working_hour
                        (create_uid, create_date, date, employee_id, advanced_schedule_id, activity_id, 
                         expected_start, expected_end, break_start, break_end, break_time, expected_working_hour,
                         is_flexible, plan_line_id, state) 
                 VALUES %s;"""%(insert_data)
        return sql
    
    def _update_pwh_sql(self, cr, uid, str_date, employee_ids, advanced_schedule_id, schedule_data, context=None): 
        """
        GENERATE PWH
        Build sql to update PWH when generate PWH in case that the schedule on that date has been changed
        """
        time_obj = self.pool.get('hr.advanced.working.time')
        cr.execute("""
                    SELECT wh.id
                            FROM hr_payroll_working_hour wh 
                            WHERE
                            state not in ('cancel', 'approve')
                            AND wh.date = '%s' 
                            AND (wh.advanced_schedule_id != 
                                (
                                SELECT advanced_schedule_id 
                                FROM resource_calendar_attendance
                                WHERE id = wh.plan_line_id
                                )
                            OR wh.is_flexible != 
                                (
                                SELECT is_flexible 
                                FROM resource_calendar_attendance
                                WHERE id = wh.plan_line_id
                                ))
                            AND wh.employee_id in (%s)
                            AND (
                                SELECT advanced_schedule_id 
                                FROM resource_calendar_attendance
                                WHERE id = wh.plan_line_id
                                ) = %s"""%(str_date, 
                                           ','.join(map(str,employee_ids)),
                                           advanced_schedule_id))
                 
        working_hours_ids = [x[0] for x in cr.fetchall()]
        sql = ''
        if working_hours_ids:
            # SQL update payroll working hour on this date
            expected_start_datetime = time_obj.compute_datetime(self, cr, uid, str_date, schedule_data['expected_start'], get_str=True, context=context)
            expected_end_datetime = time_obj.compute_datetime(self, cr, uid, str_date, schedule_data['expected_end'], get_str=True, context=context)
            break_start_datetime = schedule_data['break_start'] and time_obj.compute_datetime(self, cr, uid, str_date, schedule_data['break_start'], get_str=True, context=context)
            break_end_datetime = schedule_data['break_end'] and time_obj.compute_datetime(self, cr, uid, str_date, schedule_data['break_end'], get_str=True, context=context)
            sql = """
                    UPDATE hr_payroll_working_hour 
                    SET write_uid = %s,
                        write_date = NOW() AT TIME ZONE 'UTC',
                        advanced_schedule_id = %s,
                        activity_id = %s,
                        expected_start = '%s',
                        expected_end = '%s',
                        break_start = '%s',
                        break_end = '%s',
                        break_time = %s,
                        expected_working_hour = %s,
                        is_flexible = (
                                SELECT is_flexible 
                                FROM resource_calendar_attendance
                                WHERE id = hr_payroll_working_hour.plan_line_id
                                )
                    WHERE id in (%s);"""%(uid,
                                          advanced_schedule_id, 
                                          schedule_data['activity_id'], 
                                          expected_start_datetime, 
                                          expected_end_datetime, 
                                          schedule_data['expected_working_hour'], 
                                          break_start_datetime,
                                          break_end_datetime,
                                          schedule_data['break_time'],
                                          ','.join(map(str, working_hours_ids)))
        return sql
    
    def _cancel_pwh_sql(self, uid, employee_ids, str_from_date, str_to_date):        
        """
        GENERATE PWH
        Build sql to cancel PWH when the advanced working schedule on that date has been update a NULL value
        """
        sql = """
                UPDATE hr_payroll_working_hour
                SET state = 'cancel',
                    write_uid = %s,
                    write_date = NOW() AT TIME ZONE 'UTC'
                WHERE id in (
                    SELECT wh.id
                    FROM hr_payroll_working_hour wh 
                    WHERE
                    state not in ('cancel', 'approve')
                    AND wh.date >= '%s' 
                    AND wh.date <= '%s'
                    AND (
                        SELECT advanced_schedule_id 
                        FROM resource_calendar_attendance
                        WHERE id = wh.plan_line_id
                        ) IS NULL
                    AND wh.employee_id in (%s)
                    );"""%(uid, str_from_date, str_to_date, ','.join(map(str, employee_ids)))
        return sql
    
    
    def generate_calendar(self, cr, uid, employee_ids, from_date, to_date, plan_id, plan_lines, cycle, force=False, context=None):
        """
        PREPARE DATA 
        - Prepare data for schedule: computed_advanced_schedules
        - Prepare data for advanced working plan template line: computed_plan_lines
        CALCULATE PAYROLL WORKING HOUR
        * Only Update and cancel if Force has been checked on wizard Generate PWH
        - Update payroll working hours if advanced_working_schedule_id CHANGED on Advanced working plan template line 
        - Cancel payroll working hours if advanced_working_schedule_id SET NULL on Advanced working plan template line 
        - Create payroll working hours for employees have not created yet
            + Days in month: Max records to create
            + Number of cycles
                > First loop:
                    - start at day = day of from_date in plan template
                    - length of loop: cycle + 1 - day of from_date in plan template
                > Middle loop: 
                    - start at day = 1
                    - length of loop: cycle of length template
                > Last loop:
                    If to_date is map with the last plan template line 
                    - start at day = 1
                    - length of loop: Days in month - number of created lines
                    If NOT 
                    - start at day = 1
                    - length of loop: day of to_date in plan template
            + Number of created lines: sum of the length of loop
                
        
        @param employee_ids: employee ids 
        @param plan_id: ID of advance working plan template (resource_calendar)
        @param plan_lines: attendance_ids in resource_calendar
        @param cycle: The day in cycle 
        @param from_date: (Date) The date start generation of PWH. Maybe NOT the first date of month 
        @param to_date: (Date) The date stop generation of PWH. Maybe stop before finish a cycle
        @return: SQL to insert, update, cancel PWH
        """        
        
        #Prepare data for advanced working schedules 
        time_obj = self.pool.get('hr.advanced.working.time')
        computed_advanced_schedules = {}
        cr.execute(""" SELECT DISTINCT(advanced_schedule_id)
                        FROM resource_calendar_attendance
                        WHERE calendar_id = %s"""%(plan_id))
        advanced_schedule_ids = []
        for schedule_data in cr.fetchall():
            schedule_id = schedule_data[0]
            advanced_schedule_ids.append(schedule_id)
            
            schedule = self.pool.get('hr.advanced.working.schedule').browse(cr, uid, schedule_id, context=context)
            if schedule:
                activity_id = schedule.activity_id.id
                expected_start = schedule.work_from
                expected_end = schedule.work_to
                expected_working_hour = time_obj.delta_hours(expected_start.hour, expected_start.day, expected_end.hour, expected_end.day)
                break_start = schedule.break_from
                break_end = schedule.break_to
                break_time = (break_start and break_end) and time_obj.delta_hours(break_start.hour, break_start.day, break_end.hour, break_end.day) or 0
                schedule_data = {
                                 'activity_id': activity_id,
                                 'expected_start': expected_start.id,
                                 'expected_end': expected_end.id, 
                                 'expected_working_hour':expected_working_hour - break_time,
                                 'break_start': break_start and break_start.id or False,
                                 'break_end': expected_end and break_end.id or False,
                                 'break_time': break_time,                                 
                                 }
                computed_advanced_schedules.update({schedule_id:schedule_data})

        #Prepare data for Advanced working plan template lines 
        computed_plan_lines = {}
        for plan_line in plan_lines:
            line_data = (plan_line.id, plan_line.advanced_schedule_id and plan_line.advanced_schedule_id.id or False, plan_line.is_flexible)
            computed_plan_lines.update({plan_line.day: line_data})
        
        #Update and Cancel If Force is True 
        sql_update = ''
        sql_cancel = ''
        if force: 
            str_from_date = from_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
            str_to_date = to_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
            
            """
            Case 1:Cancel Payroll Working Hours of seleted employees
            SET NULL the advanced working schedule of this plan template line (plan_line_id)
            """
            logging.info('--------------START FORCE UPDATE-----------')
            sql_cancel = self._cancel_pwh_sql(uid, employee_ids, str_from_date, str_to_date)
            
            """
            Case 2: Update Payroll Working Hours 
            The advanced schedule of this payroll working schedule and the advanced plan template line are different
            """
            sql_update = ''
            for advanced_schedule_id in advanced_schedule_ids:
                if advanced_schedule_id:
                    # Find date to update
                    cr.execute("""
                        SELECT DISTINCT(date)
                        FROM hr_payroll_working_hour wh 
                        WHERE 
                            state not in ('cancel', 'approve')
                            AND wh.date >= '%s'
                            AND wh.date <= '%s' 
                            AND (wh.advanced_schedule_id != 
                                (
                                SELECT advanced_schedule_id 
                                FROM resource_calendar_attendance
                                WHERE id = wh.plan_line_id
                                )
                            OR wh.is_flexible != 
                                (
                                SELECT is_flexible 
                                FROM resource_calendar_attendance
                                WHERE id = wh.plan_line_id
                                ))
                            AND wh.employee_id in (%s)
                            AND (
                                SELECT advanced_schedule_id 
                                FROM resource_calendar_attendance
                                WHERE id = wh.plan_line_id
                                ) = %s
                    """%(str_from_date, str_to_date, ','.join(map(str,employee_ids)), advanced_schedule_id))
                    
                    for str_date in cr.fetchall():
                        update_schedule = computed_advanced_schedules[advanced_schedule_id]
                        sql_update += self._update_pwh_sql(cr, uid, str_date[0], employee_ids, advanced_schedule_id, update_schedule, context=context)

            logging.info('SQL CANCEL: %s'%(sql_cancel))
            logging.info('SQL UPDATE: %s'%(sql_update))
            logging.info('---------------END FORCE UPDATE--------------')
        
        """
        Case 3: Create Payroll Working Hours
        The payroll working hour of this employee and this date have not been created   
        """
        
        #Calculate start(from_day_cycle), stop(stop_day_cycle) of a cycle in loop
        from_day_cycle = self.pool.get('resource.calendar').find_day_of_cycle(cr, uid, plan_id, cycle, from_date)
        stop_day_cycle = cycle
        max_lines = (to_date - from_date).days + 1# Max lines to create
        stop_day_cycle = min(stop_day_cycle, max_lines+from_day_cycle-1)
        
        #Calculate number_of_cycles
        days = (to_date - from_date).days + from_day_cycle
        divdays = days%cycle
        number_of_cycles = divdays == 0 and days/cycle or days/cycle +1
        
        #Initial data for loop
        create_emp_ids = []
        insert_data = ''
        created_lines = 0
        date = from_date + timedelta(days=-1)
        
        logging.info('START CALCULATE DATA TO CREATE')
        
        for obj in range(1, number_of_cycles+1):
            logging.info('Cycle: %s'%obj)
            logging.info('Start cycle: %s'%date)
            logging.info('DAY CYCLE WILL CREATE: %s'%(range(from_day_cycle, stop_day_cycle+1)))
            
            for day in range(from_day_cycle, stop_day_cycle+1):
                date = date + timedelta(days=1)
                str_date = date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                computed_plan_line = computed_plan_lines[day]
                plan_line_id = computed_plan_line[0] 
                advanced_schedule_id = computed_plan_line[1]
                is_flexible = computed_plan_line[2]
                logging.info('Date: %s, Day in cycle: %s, advanced_schedule_id: %s, Is Flexible: %s'%(date, day, advanced_schedule_id, is_flexible))
                
                if advanced_schedule_id:
                    ##########Calculate create_emp_ids############################################## 
                    #create_emp_ids: The employees need to create payroll working hour oon this date
                    #employee_ids: The Selected Employees
                    #exist_employee_ids: The employees exist a payroll working hour on this date 
                    
                    cr.execute("""
                        SELECT DISTINCT(employee_id) 
                        FROM hr_payroll_working_hour
                        WHERE state != 'cancel'
                        AND date = '%s' 
                        AND plan_line_id = %s
                        AND employee_id in (%s)
                        """%(date.strftime(DEFAULT_SERVER_DATE_FORMAT), 
                             plan_line_id, 
                             ','.join(map(str, employee_ids))))
                    
                    res = cr.fetchall()
                    exist_employee_ids = set([x[0] for x in res])
                    create_emp_ids = list(set(employee_ids) - exist_employee_ids)
                    
                    if create_emp_ids:
                        logging.info('TO BE CREATE: %s'%str(create_emp_ids))
                        #Get the info of a advanced working schedule in the computed_advanced_schedule
                        schedule =  computed_advanced_schedules[advanced_schedule_id]

                        #Calulate the insert_sql
                        #sql: sample record to insert with employee_id = %emp_id%
                        #For each employee_id: replace %emp_id% by employee_id
                        
                        str_expected_start = time_obj.compute_datetime(cr, uid, str_date, schedule['expected_start'], 
                                                                       get_str=True, context=context)
                        str_expected_end = time_obj.compute_datetime(cr, uid, str_date, schedule['expected_end'], 
                                                                     get_str=True, context=context)
                        str_break_start = schedule['break_start'] and time_obj.compute_datetime(cr, uid, str_date, 
                                                                                                schedule['break_start'], 
                                                                                                get_str=True, context=context)
                        str_break_end = schedule['break_end'] and time_obj.compute_datetime(cr, uid, str_date, 
                                                                                            schedule['break_end'],
                                                                                             get_str=True, context=context)
            
                        sql = """
                        (%s, NOW() AT TIME ZONE 'UTC', '%s', %s, %s, %s, '%s', '%s', '%s', '%s', %s, %s, %s, %s, 'draft'), """\
                        %(uid, date.strftime(DEFAULT_SERVER_DATE_FORMAT), '%emp_id%', advanced_schedule_id, 
                          schedule['activity_id'], str_expected_start, str_expected_end,
                          str_break_start, str_break_end, schedule['break_time'],
                          schedule['expected_working_hour'], is_flexible, plan_line_id)
                        
                        for emp_id in create_emp_ids:
                            insert_data += sql.replace('%emp_id%', str(emp_id))

            #Reset to start a new cycle
            created_lines += (stop_day_cycle+1 - from_day_cycle)
            from_day_cycle = 1
            stop_day_cycle = min(cycle, max_lines - created_lines)
        logging.info('END CALCULATE DATA TO CREATE')
        
        #Insert payroll working hours
        insert_data = insert_data[:-2]
        sql_insert = self._create_pwh_sql(insert_data)
        
        return sql_insert + sql_update + sql_cancel
    
    def generate_payroll_working_hour(self, cr, uid, employee_ids, str_from_date, str_to_date, force, context=None):
        """
        Generate the payroll working hours
        - Group employees by
            + Advanced working plan template 
            + From date to generate
            + To date to generate
            Calculate fields above base on the current contracts of the selected employees
        - For each group, Run generate_calendar
        - Update name for the created payroll working hours
        - Update contract for the created payroll working hours
        - Create/Update the expected working days
        
        @param str_from_date: (string) from date
        @param str_to_date: (string) to date
        @param employee_ids: employee_ids  
        @return: list working hour IDs
        """
        
        contract_obj = self.pool.get('hr.contract')
        groups = {}
        contracts = []
        working_hour_data = {}
        str_to_date = str_to_date and str_to_date or str_from_date
        for employee_id in employee_ids:
            contract_ids = contract_obj.get_contract(cr, uid, employee_id, str_from_date, str_to_date, context=context) 
            for contract in contract_obj.browse(cr, uid, contract_ids, 
                                                fields_process=['date_start', 
                                                                'date_end',
                                                                'working_hours', 
                                                                'working_hours.id', 
                                                                'working_hours.attendance_ids', 
                                                                'working_hours.cycle'
                                                                ], 
                                                context=context):
                working_hours = contract.working_hours
                if working_hours:
                    valid_from_date = max(contract.date_start, str_from_date)
                    valid_to_date = min(contract.date_end and contract.date_end or str_to_date, str_to_date)
                    
                    #contracts: list of contract of employee valid in a period
                    contracts.append((valid_from_date, valid_to_date, employee_id, contract.id))
                    
                    converted_from_date  = datetime.strptime(valid_from_date, DEFAULT_SERVER_DATE_FORMAT)
                    converted_to_date = datetime.strptime(valid_to_date, DEFAULT_SERVER_DATE_FORMAT)
                    working_hour_id = working_hours.id
                    cycle = working_hours.cycle
                    plan_lines = working_hours.attendance_ids
                    key = (working_hour_id, converted_from_date, converted_to_date)
                    
                    #Working hour data
                    if working_hour_id not in working_hour_data:
                        working_hour_data.update({working_hour_id: (cycle, plan_lines)})
                    
                    #groups = {(advanced_schedule_id, from_date, to_date): 
                    if key not in groups: 
                        groups.update({key: [employee_id]})
                    else:
                        groups[key].append(employee_id)
                    
        #For each group, run generate calendar                
        for group in groups.keys():
            # group = (working_hour_id, converted_from_date, converted_to_date)
            # plan = (cycle, plan_lines)
            logging.info("          =FOR EACH GROUP: %s"%str(group))
            logging.info('EMPLOYEES: %s'%(groups[group]))
            plan = working_hour_data[group[0]]
            sql = self.generate_calendar(cr, uid, groups[group], group[1], group[2], group[0], plan[1], plan[0], force=force, context=context)        
            sql and cr.execute(sql)
        
        #Update name for created payroll working hours
        cr.execute("""
            UPDATE hr_payroll_working_hour wh
            SET name = (SELECT name_related FROM hr_employee WHERE id = wh.employee_id) || ' ' ||date
            WHERE 
            employee_id in (%s)
            AND date >= '%s'
            AND date <= '%s'"""%(','.join(map(str, employee_ids)), str_from_date, str_to_date))
        
        #Update Contract for payroll working hours
        update_contract_sql = ''
        
        for start, end, emp_id, contract in contracts:
            update_contract_sql += """
            UPDATE hr_payroll_working_hour wh
            SET contract_id = %s
            WHERE 
            employee_id in (%s)
            AND date >= '%s'
            AND date <= '%s';"""%(contract, emp_id, start, end)
        update_contract_sql and cr.execute(update_contract_sql)
        
        #Update Public Holiday activity for payroll working hours
        param_obj = self.pool.get('ir.config_parameter')
        public_act_name = param_obj.get_param(cr, uid, 'public_holiday_act') or None
        if not public_act_name:
            raise osv.except_osv(_("Warning!"), _("Please setup a working activity for Public Holidays"))
        
        cr.execute("""
        UPDATE hr_payroll_working_hour wh
        SET activity_id = (
                SELECT id 
                FROM hr_working_activity 
                WHERE name = '%s'
                ),
            public_holiday_id = (
                SELECT id
                FROM trobz_hr_public_holidays 
                WHERE state = 'approved'
                    AND date = wh.date
                    AND country = (SELECT part.country_id 
                              FROM resource_resource emp 
                              JOIN res_company com ON emp.company_id = com.id
                              JOIN res_partner part ON part.id = com.partner_id
                              WHERE emp.id = wh.employee_id)
                ),
            working_hour = expected_working_hour,
            state = 'approve'
        WHERE state = 'draft' 
        AND date IN 
            (SELECT date
            FROM trobz_hr_public_holidays 
            WHERE state = 'approved'
            AND country = (SELECT part.country_id 
                              FROM resource_resource emp 
                              JOIN res_company com ON emp.company_id = com.id
                              JOIN res_partner part ON part.id = com.partner_id
                              WHERE emp.id = wh.employee_id)
            )
        AND date >= '%s'
        AND date <= '%s'
        AND employee_id IN (%s)"""%(public_act_name, str_from_date, str_to_date, ','.join(map(str, employee_ids))))
        
        #Record the expected working days
        logging.info("+++++++++++++START RECORD THE EXPECTED WORKING DAY+++++++++++++++")
        expected_from_date = datetime.strptime(str_from_date, DEFAULT_SERVER_DATE_FORMAT)
        expected_to_date = datetime.strptime(str_to_date, DEFAULT_SERVER_DATE_FORMAT)
        delta_months = relativedelta(expected_to_date, expected_from_date).months

        for month in range(0, delta_months+1):
            month_year = (expected_from_date + relativedelta(months=month)).strftime('%m/%Y')
            first_date = (expected_from_date + relativedelta(months=month, day=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            last_date = (expected_from_date + relativedelta(months=month+1, day=1, days=-1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            cr.execute( """
                --UPDATE EXPECTED WORKING DAYS
                UPDATE hr_expected_working_day ex
                SET days = (SELECT COUNT(date) as days
                            FROM hr_payroll_working_hour wh
                            JOIN hr_working_activity ac
                            ON wh.activity_id = ac.id
                            --WHERE ac.type = 'work' 
                            AND date >= '%s' AND date <= '%s'
                            AND plan_line_id IS NOT NULL
                            AND state != 'cancel'
                            AND is_flexible = False
                            AND contract_id = ex.contract_id),
                write_uid = %s,
                write_date = NOW() AT TIME ZONE 'UTC'
                WHERE month_year= '%s' 
                AND employee_id IN (%s)
                AND contract_id = ex.contract_id;"""%(first_date, last_date, uid, month_year, ','.join(map(str, employee_ids))) + """  
                --INSERT EXPECTED WORKING DAYS
                INSERT INTO hr_expected_working_day(create_uid, create_date, name, month_year, contract_id, employee_id, from_date, to_date, days)
                SELECT
                    %s,
                    NOW() AT TIME ZONE 'UTC',
                    TO_CHAR(MIN(date), 'MM/YYYY') || ' ' ||(SELECT name FROM hr_contract WHERE id = wh.contract_id) as name,
                    TO_CHAR(MIN(date), 'MM/YYYY') as month_year, 
                    contract_id,
                    employee_id,
                    MIN(date) as from_date,
                    MAX(date) as to_date,
                    COUNT(date) as days
                FROM hr_payroll_working_hour wh
                WHERE date >= '%s' AND date <= '%s'
                AND plan_line_id IS NOT NULL
                AND is_flexible = False
                AND state != 'cancel'
                AND NOT EXISTS(SELECT 1 
                                FROM hr_expected_working_day
                                WHERE month_year = '%s' AND contract_id = wh.contract_id)
                AND employee_id IN (%s)
                GROUP BY contract_id, employee_id;"""%(uid, first_date, last_date, month_year, ','.join(map(str, employee_ids))))
        logging.info('DONE GENERATE PAYROLL WORKING HOURS + RECORDE EXPECTED WORKING DAYS')
        
        # Get the payroll working hours have been generated
        pwh_ids = self.search(cr, uid, [('date', '>=', str_from_date),
                                        ('date', '<=', str_to_date),
                                        ('employee_id', 'in', employee_ids)], 
                              context=context)
        return pwh_ids
    
    def scheduler_generate_working_hour(self, cr, uid, context=None):
        """
        Scheduler to generate payroll working hours for the next month
        """
        working_hour_obj = self.pool.get('hr.payroll.working.hour')
        emp_obj = self.pool.get('hr.employee')
        employee_ids = emp_obj.search(cr, uid, [], context=context)
        from_date = (date.today() + relativedelta(months=1, day=1))
        to_date = (from_date + relativedelta(months=1, days=-1))
        
        logging.info('-----START SCHEDULER GENERATE PAYROLL WORKING HOURS------')
        working_hour_obj.generate_payroll_working_hour(cr, uid, employee_ids, from_date.strftime(DEFAULT_SERVER_DATE_FORMAT), to_date.strftime(DEFAULT_SERVER_DATE_FORMAT), force=False, context=context)
        logging.info('-----START SCHEDULER GENERATE PAYROLL WORKING HOURS------')
        return True
    
    ##############COMPUTE PAYROLL WORKING HOUR###########################
    def _insert_sql(self, insert_data):
        """
        Insert overtime pwh, leave request pwh
        """
        if not insert_data:
            return ''
        
        sql = """
            INSERT INTO hr_payroll_working_hour
                (create_date, create_uid, write_date, write_uid, employee_id, date, advanced_schedule_id, 
                activity_id, contract_id, expected_start, expected_end, break_start, break_end, break_time, 
                expected_working_hour, name, sign_in, sign_out, late_in, early_out, working_hour, 
                state, overtime_id, leave_line_id, is_flexible)
            %s;
        """%(insert_data)
        return sql
    
    def _full_off_update_sql(self, uid, pwh_id, working_hour, activity_id, leave_line_id):
        """
        Update sql if full day off
        """
        sql = """
            UPDATE hr_payroll_working_hour pwh
            SET write_date = NOW() AT TIME ZONE 'UTC',
                write_uid = %s,
                sign_in = NULL,
                sign_out = NULL,
                late_in = 0, 
                early_out = 0,
                activity_id = %s,  
                working_hour = %s,
                leave_line_id = %s,
                state = 'approve'
            WHERE id = %s;"""%(uid, activity_id, working_hour, leave_line_id, pwh_id)
        return sql
    
    def _half_working_update_sql(self, uid, pwh_id, expected_start, expected_end, expected_working_hour, leave_line_id):
        """
        Update sql if day off
        """
        sql = """
            UPDATE hr_payroll_working_hour pwh
            SET write_date = NOW() AT TIME ZONE 'UTC',
                write_uid = %s,
                leave_line_id = %s,
                expected_start = '%s',
                expected_end = '%s',
                break_start = NULL,
                break_end = NULL,
                break_time = 0,
                expected_working_hour = %s
            WHERE id = %s;"""%(uid, leave_line_id, expected_start, expected_end, expected_working_hour, pwh_id)
        return sql
    
    def _work_update_sql(self, uid, sign_in, sign_out, late_in, early_out, working_hour, pwh_id):
        """
        Update sql if working day or overtime
        """
        sql = """
            UPDATE hr_payroll_working_hour
            SET write_date = NOW() AT TIME ZONE 'UTC',
                write_uid = %s,
                sign_in = '%s',
                sign_out = '%s',
                late_in = %s,
                early_out = %s,
                working_hour = %s,
                state = 'approve'
            WHERE id = %s;"""%(uid, sign_in, sign_out, late_in, early_out, working_hour, pwh_id)
        return sql
    
    def _leave_data(self, cr, uid, employee_ids, hol_status_ids, str_from_date, str_to_date, context=None):
        """
        @param hol_status_ids: link to holiday status
        @param employee_ids: employees
        @param str_from_date: (string) From Date
        @param str_to_date:(string) To Date
        @return: leave_data = {(date, employee): {daysoff, activity}}   
        """
        sql = """
            SELECT
                hl.id, h.employee_id, hl.first_date, hl.last_date, 
                hl.first_date_type, hl.last_date_type, st.working_activity_id
            FROM 
                hr_holidays h
                JOIN hr_holidays_line hl ON (h.id=hl.holiday_id)
                JOIN hr_holidays_status st ON (hl.holiday_status_id=st.id)
            WHERE
                h.employee_id IN (%s) AND
                h.type='remove' AND
                h.state='validate' AND
                hl.holiday_status_id in (%s) 
                AND
                (
                    (hl.first_date > '%s' AND hl.last_date < '%s') 
                    OR ( hl.first_date <= '%s' AND hl.last_date >= '%s') 
                    OR (hl.first_date <= '%s' AND hl.last_date >= '%s')        
                )
                """%(','.join(map(str, employee_ids)),
                     ','.join(map(str, hol_status_ids)),
                     str_from_date, str_to_date, 
                     str_from_date, str_from_date, 
                     str_to_date, str_to_date)
        """Compute Leave Data: 
        {(str_date, employee_id): {id: leave_line_id,
                                   dayoff: 0.5, 
                                   date_type: afternoon/morning/full}}
        """
        cr.execute(sql)
        leave_data = {}
        for line in cr.dictfetchall():
            line_id = line['id']
            employee_id = line['employee_id']
            str_first_date = line['first_date']
            str_last_date = line['last_date']
            first_date_type = line['first_date_type']
            last_date_type = line['last_date_type']
            activity_id = line['working_activity_id']
            
            select_country_sql = """
                SELECT part.country_id 
                FROM resource_resource emp 
                JOIN res_company com ON emp.company_id = com.id
                JOIN res_partner part ON part.id = com.partner_id
                WHERE emp.id = %s"""%(line['employee_id'])
            cr.execute(select_country_sql)
            res = cr.fetchone()
            country_id = res and res[0] or False
            str_valid_from_date = str_from_date and max(str_first_date, str_from_date) or str_first_date 
            str_valid_to_date = str_to_date and min(str_last_date, str_to_date) or str_last_date
            valid_from_date = datetime.strptime(str_valid_from_date, DEFAULT_SERVER_DATE_FORMAT).date()
            valid_to_date = datetime.strptime(str_valid_to_date, DEFAULT_SERVER_DATE_FORMAT).date()
            has_working_hours = False
            
            # Start compute for each leave line
            line_obj = self.pool.get('hr.holidays.line')
            while valid_from_date <= valid_to_date:
                contract_obj = self.pool.get('hr.contract')
                contract_ids = contract_obj.get_contract(cr, uid, employee_id, valid_from_date, context=context)
                if contract_ids:
                    contract = contract_obj.browse(cr, uid, contract_ids[-1], fields_process=['working_hours'], context=context)
                    has_working_hours = contract.working_hours and contract.working_hours.id or False
            
                dayofweek = valid_from_date.weekday()
                date_type = 'full'
                str_date = valid_from_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                if valid_from_date == datetime.strptime(str_first_date, DEFAULT_SERVER_DATE_FORMAT).date():
                    date_type = first_date_type
                if valid_from_date == datetime.strptime(str_last_date, DEFAULT_SERVER_DATE_FORMAT).date():
                    date_type = last_date_type
                dayoff = line_obj.plus_day(cr, uid, has_working_hours, valid_from_date, dayofweek, date_type, country_id, context=context)
                key = (str_date, employee_id)
                leave_data.update({key: {'id': line_id, 'dayoff': dayoff, 'activity_id': activity_id, 'date_type': date_type}})
                #Next date in holiday line
                valid_from_date = valid_from_date + timedelta(1)
        return leave_data
    
    def _compute_attendances(self, cr, uid, pwh_id, tolerance, emp_id, str_work_from, str_work_to, str_break_from, str_break_to, break_time, max_early_in, max_late_out, context=None):
        """
        Use to calculate attendance working hour of a working/overtime payroll working hour
        @param str_work_from: Work From (string) of this payroll working hour
        @param str_work_to: Work To (string) of this payroll working hour
        @param str_break_from: Break From (string)
        @param str_break_to: Break To (string)
        @param auth_late_in: Authorized late in minutes(Float)
        @param auth_early_out: Authorized early out minutes (Float)
        @param ordered_att: 
            - List of Attendances from work_from to work_to order by datetime ascending
            - [(datetime in, datetime out), (datetime in, datetime out), ...]
        @return: 
            - Attendance Sign In
            - Attendance Sign Out
            - Late In
            - Early Out
            - Working Hour
        """
        update_sql = ''
        time_obj = self.pool.get('hr.advanced.working.time')
        
        # Compute the period to get the attendances. (work-from - max-early/work-to + max-late)
        work_from = datetime.strptime(str_work_from, DEFAULT_SERVER_DATETIME_FORMAT)
        work_to = datetime.strptime(str_work_to, DEFAULT_SERVER_DATETIME_FORMAT)
        
        # tolerance allow to employee can late-in/earl-out 2 minutes
        tolerance = tolerance and tolerance or 0
        tolerance_work_from = work_from + relativedelta(hours=tolerance/60, minutes=tolerance%60)
        tolerance_work_to = work_to - relativedelta(hours=tolerance/60, minutes=tolerance%60)
        
        # min_att_from, max_att_to use to compute the period to get the attendances
        min_att_from = work_from + relativedelta(minutes=-max_early_in) 
        max_att_to = work_to + relativedelta(minutes=max_late_out)
        str_min_att_from = min_att_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        str_max_att_to = max_att_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        
        select_att_sql = """
            SELECT id, name, action
            FROM hr_attendance
            WHERE name >= '%s'
            AND name <= '%s'
            AND employee_id = %s
            AND status = 'normal'
            ORDER BY name
        """%(str_min_att_from, str_max_att_to, emp_id)
        cr.execute(select_att_sql)
        res = cr.dictfetchall() 
        if not res:
            return update_sql 
        
        atts_in = []
        atts_out = []
        att_ids = []
        for att in res:
            att_ids.append(att['id'])
            if att['action'] == 'sign_in':
                atts_in.append(att['name'])
            if atts_in and att['action'] == 'sign_out':
                #Append the first sign-out after append the first sign-in
                atts_out.append(att['name'])
        ordered_att = zip(atts_in, atts_out)
        
        if not ordered_att:
            return update_sql
 
        ordered_att = ordered_att
        valid_att = []
        working_hour = 0
        late_in = 0
        early_out = 0
        
        #The advanced schedule have no break time
        if not str_break_from and not str_break_to:
            logging.info("                ==> The advanced schedule have no break time")
            # Get a valid attendance that map with the expected expected-start, expected-end
            for att in ordered_att:
                str_att_in = att[0]
                str_att_out = att[1]
                logging.info("                ==> Sign-in: %s, Sign-out: %s"%(str_att_in,str_att_out))
                
                # Check tolerance
                att_in = datetime.strptime(str_att_in, DEFAULT_SERVER_DATETIME_FORMAT)
                att_out = datetime.strptime(str_att_out, DEFAULT_SERVER_DATETIME_FORMAT)
                if att_in <= tolerance_work_from:
                    str_att_in = str_work_from
                if att_out >= tolerance_work_to:
                    str_att_out = str_work_to
                
                str_valid_att_in = max(str_att_in, str_work_from)
                str_valid_att_out = min(str_att_out, str_work_to)
                valid_att_in = datetime.strptime(str_valid_att_in, DEFAULT_SERVER_DATETIME_FORMAT)
                valid_att_out = datetime.strptime(str_valid_att_out, DEFAULT_SERVER_DATETIME_FORMAT)
                working_hour += time_obj.diff_hour(valid_att_in, valid_att_out)
                # valid_att stored all valid_att_in, valid_att_out to compute late_in, early_out
                valid_att.append((valid_att_in, valid_att_out))
        
        #The advanced schedule have break time        
        if str_break_from and str_break_to:
            for att in ordered_att:
                logging.info("                ==> The advanced schedule have break time")
                str_att_in = att[0]
                str_att_out = att[1]
                logging.info("                ==> Sign-in: %s, Sign-out: %s"%(str_att_in,str_att_out))
                
                # Check tolerance
                att_in = datetime.strptime(str_att_in, DEFAULT_SERVER_DATETIME_FORMAT)
                att_out = datetime.strptime(str_att_out, DEFAULT_SERVER_DATETIME_FORMAT)
                if att_in <= tolerance_work_from:
                    str_att_in = str_work_from
                if att_out >= tolerance_work_to:
                    str_att_out = str_work_to
                
                # Get a valid attendance that map with the expected expected-start, expected-end, break-start, break-end
                str_valid_att_in = '' 
                str_valid_att_out = ''
                if str_att_in >= str_break_from and str_att_out <= str_break_to:
                    logging.info("                   ==> sign-in and sign-out in break time")
                    continue
                elif str_att_in < str_break_from and str_att_out > str_break_to:
                    str_valid_att_in = max(str_att_in, str_work_from)
                    str_valid_att_out = min(str_att_out, str_work_to)
                    working_hour += - break_time
                    logging.info("                   ==> sign-in and sign-out in Morning + Aternoon")
                elif str_att_in < str_break_from and str_att_out <= str_break_to:
                    str_valid_att_in = max(str_att_in, str_work_from)
                    str_valid_att_out = min(str_att_out, str_break_from)
                    logging.info("                   ==> sign-in and sign-out in Morning")
                elif str_att_in >= str_break_from and str_att_out > str_break_to:
                    str_valid_att_in = max(str_att_in, str_break_to)
                    str_valid_att_out = min(str_att_out, str_work_to)
                    logging.info("                   ==> sign-in and sign-out in Aternoon")
                
                # Sum attendance working hour for each (sign-in, sign-out)
                valid_att_in = datetime.strptime(str_valid_att_in, DEFAULT_SERVER_DATETIME_FORMAT)    
                valid_att_out = datetime.strptime(str_valid_att_out, DEFAULT_SERVER_DATETIME_FORMAT)
                working_hour += time_obj.diff_hour(valid_att_in, valid_att_out)
                
                # valid_att stored all valid_att_in, valid_att_out to compute late_in, early_out
                valid_att.append((valid_att_in, valid_att_out))
            
        # Compute late_in, early_out
        if valid_att:    
            work_from = datetime.strptime(str_work_from, DEFAULT_SERVER_DATETIME_FORMAT)
            work_to = datetime.strptime(str_work_to, DEFAULT_SERVER_DATETIME_FORMAT)
            late_in = time_obj.diff_hour(work_from, valid_att[0][0])
            early_out = time_obj.diff_hour(valid_att[-1][-1], work_to)
        update_sql = working_hour > 0 and self._work_update_sql(uid, ordered_att[0][0], ordered_att[-1][-1], late_in, early_out, working_hour, pwh_id) or ''
        
        #Update computed_attendance, pwh_id after compute attendances 
        cr.execute("""
            UPDATE hr_attendance 
            SET computed_attendance = name, 
                pwh_id = %s
            WHERE id IN (%s)
        """%(pwh_id, ','.join(map(str, att_ids))))
        logging.info("                   ==> Working Hour: %s, Late in: %s, Late out: %s"%(working_hour, late_in, early_out))
        return update_sql

    def compute(self, cr, uid, employee_ids, str_from_date, str_to_date, context=None):
        """ 
        @param str_from_date: From date (string)
        @param str_to_date: To Date (string)
        @param employee_ids: Employees to compute PWH
        @return: PWH_ids of employees on this period 
          
        Wizard to create/Override the payroll working hours:
        
        Tolerance = 2 minutes mean:
        work from: 07:00, sign-in: 07:00->07:02 that mean sign-in:07:00
        similar for work-to
        
        1. COMPUTE_EMPLOYEES:
            - Get a list of employees to be checked. 
            - Ignore employees who have at least one inconsistent attendances.
        2. PREPARE PWH OF COMPUTE_EMPLOYEES:
            - Overtime: Create PWH
                + Input: Confirmed Overtime
                + Output: SQL to insert PWH
                + Process:
                    > Cancel Overtime-PWH if the Overtime register of this PWH changed
                    > For each Overtime register > Insert a draft Overtime-PWH 
            - Leave request
                + Input: Approved leave request
                + Output: SQL to cancel/update PWH
                + Process:
                    > Cancel New leave-PWH if the Leave request(Half dayoff) of this PWH cancelled
                    > Set draft leave-PWH (link to a schedule plan line) if the Leave request of this PWH cancelled
            - Working day
                + Revert working-PWH to draft if attendances of this PWH changed
            - Public holiday: Nothing to do
        3. COMPUTE PWH: 
        For each date, employee:
            - Read PWH of this employee on this date
                + Input: date, employee, PWHs
                + Output: PWHs include: official Work, overtime, , Leave request, Public holiday(approved in advance) 
            - Read Leave Request: Create/update and approve PWH
                + Input: Approved Leave Request on this period
                + Output: 
                    SQL to insert/update PWH
                    Don't need compute PWH if this employee has full day off
            - Start compute PWH ...
                + Function compute_attendances:
                    > PHW info: work-from, work-to, break-from, break-to, auth late in, auth early out
                    > Attendances:
                        of this employee
                        in period (PWH work_from - max_early_in parameter --> PWH work_to + max_late_out parameter)
                    > Return update_sql
                + Process:
                    > For each work/compensation/overtime-PWH: Use Function compute_attendances
                + Output:
                    > SQL to update PHW
            - Execute update_sql, insert_sql(For a half day off)
        """
        
        if context is None:
            context = {}
        context.update({'compute_pwh': True})
        time_obj = self.pool.get('hr.advanced.working.time')
        
        #CHECK EMPLOYEE ATTENDANCES CONSISTENCY
        logging.info('     ==> START CHECK EMPLOYEE ATTENDANCES CONSISTENCY....')
        select_sql = """
            SELECT id
            FROM hr_employee hem
            WHERE NOT EXISTS (
                SELECT 1
                FROM hr_attendance hat
                WHERE hat.employee_id = hem.id
                    AND name >= '%s'
                    AND name <= '%s'
                    AND status = 'inconsistent' 
                    --is_inconsistent = True
                )
            AND hem.id IN (%s);
        """ % (str_from_date, str_to_date + ' 23:59:59', ','.join(map(str, employee_ids)))
        cr.execute(select_sql)
        employee_ids = [row[0]for row in cr.fetchall()]
        if not employee_ids:
            return []
        logging.info('     ==> Number of employees are being computed %d' % len(employee_ids))
        
        #Read maximum_early_minutes, maximum_late_minutes
        param_obj = self.pool.get('ir.config_parameter')
        max_early_in = float(param_obj.get_param(cr, uid, 'maximum_early_minutes')) or 0
        max_late_out = float(param_obj.get_param(cr, uid, 'maximum_late_minutes')) or 0
        
        logging.info('     *** PREPARE DATA BEFORE COMPUTE PWH....')
        #OVERTIME/COMPENSATION
        logging.info('     ==> START COMPUTE OVERTIME BEFORE COMPUTE PWH....')
        #If a confirmed Overtime/Compensation has been change after compute PWH 
        # => Cancel approved PWH of this overtime  
        cancel_ot_pwh_sql = """
            UPDATE hr_payroll_working_hour 
            SET state = 'cancel'
            WHERE id IN 
                (SELECT pwh.id
                    FROM hr_payroll_working_hour pwh
                        JOIN hr_overtime ot ON pwh.overtime_id = ot.id
                    WHERE overtime_id IS NOT NULL
                        AND ot.write_date >= pwh.write_date
                        AND pwh.state = 'approve'
                );
        """
        cr.execute(cancel_ot_pwh_sql)
        logging.info('     ==> DONE OVERTIME CHANGED > CANCEL PWH')
        
        #For each a confirmed overtime 
        # => Create PWH if not exists an draft/approved PWH link to this overtime
        logging.info('     ==> START CREATE OVERTIME PWH....')
        insert_ot_data = """
            SELECT 
                NOW() AT TIME ZONE 'UTC', %s, NOW() AT TIME ZONE 'UTC', %s,
                employee_id, ot.name, advanced_schedule_id, 
                working_activity_id, contract_id, datetime_start, datetime_stop, 
                break_start, break_stop, break_hour, working_hour, emp.name_related || to_char(ot.name, 'YY-MM-DD'), 
                null, null, 0, 0, 0, 'draft', ot.id, NULL, False
            FROM hr_overtime ot
            JOIN hr_employee emp ON ot.employee_id = emp.id
            WHERE employee_id IN (%s)
                AND ot.state = 'confirmed'
                AND ot.mode = 'by_employee'
                AND ot.name >= '%s'
                AND ot.name <= '%s'
                AND NOT EXISTS (SELECT 1 
                                FROM hr_payroll_working_hour 
                                WHERE overtime_id = ot.id
                                AND state != 'cancel')
        """ % (uid, uid, ','.join(map(str,employee_ids)), str_from_date, str_to_date)
        insert_ot_sql = self._insert_sql(insert_ot_data)
        cr.execute(insert_ot_sql)
        logging.info('     ==> DONE CREATE OVERTIME PWH')
        
        #LEAVE REQUEST: Cancel invalid day-off PWHs
        logging.info('     ==> COMPUTE LEAVE REQUEST BEFORE COMPUTE PWH ...')
        #Cancel Day-off PWHs have been created for a half day off (plan_line_id is null) that changing after computing PWHs
        #Cancel Day-off PWHs have no leave_line_id that mean the leave requests were deleted
        update_leave_pwh_sql = """
            UPDATE hr_payroll_working_hour u_pwh
            SET write_date = NOW() AT TIME ZONE 'UTC',
                write_uid = %s,
                state = 'cancel'
            WHERE id IN
                (SELECT pwh.id 
                FROM hr_payroll_working_hour pwh
                    LEFT JOIN hr_holidays_line hl ON pwh.leave_line_id = hl.id 
                    JOIN hr_working_activity act ON pwh.activity_id = act.id
                WHERE act.type = 'daysoff'
                    AND pwh.employee_id IN (%s)
                    AND pwh.date >= '%s'
                    AND pwh.date <= '%s'
                    AND pwh.plan_line_id IS NULL 
                    AND pwh.state = 'approve'
                    AND (leave_line_id IS NULL 
                        OR (leave_line_id IS NOT NULL and hl.write_date >= pwh.write_date)
                        )
                );
        """%(uid, ','.join(map(str, employee_ids)), str_from_date, str_to_date)
        cr.execute(update_leave_pwh_sql)
        logging.info('     ===> LEAVE REQUEST CHANGED > DONE CANCEL PWH')
        
        #Read leave data to compute PWH below
        hol_status_ids = self.pool.get('hr.holidays.status').search(cr, uid, [('working_activity_id', '!=', False)], context=context)
        leave_data = self._leave_data(cr, uid, employee_ids, hol_status_ids, str_from_date, str_to_date, context=context)
        leave_dates = ["'"+x[0]+"'" for x in leave_data.keys()]
        logging.info('     **** LEAVE REQUEST DATA: %s'%str(leave_data))

        # REVERT PWH
        # Draft PWHs: If PWH has been updated old_.. fields before. That mean re-computing PWHs 
        # Approved Working PWH: If Exist the attendances changed related to a pwh
        # Approved Day-off PWH: If Create and approved a New leave request on PWH date
        #              IF leave request of this PWH is cancelled/deleted After computing PWH
        logging.info("     ===> START REVERT PWH.... ")
        revert_sql = """
            -- exists attendances change
            UPDATE hr_payroll_working_hour
            SET 
                state = 'draft',
                sign_in = NULL,
                sign_out = NULL,
                late_in = 0,
                early_out = 0,
                working_hour = 0
            WHERE state = 'approve'
                AND plan_line_id IS NOT NULL
                AND employee_id IN (%s)
                AND date >= '%s'
                AND date <= '%s'
                AND id IN (SELECT pwh_id 
                            FROM hr_attendance
                            WHERE name <> computed_attendance
                            );
        """%(','.join(map(str, employee_ids)), str_from_date, str_to_date)
        
        if leave_dates:
            revert_sql ="""
            UPDATE hr_payroll_working_hour
            SET 
                activity_id = old_activity_id,
                expected_start = old_expected_start,
                expected_end = old_expected_end,
                break_start = old_break_start,
                break_end = old_break_end,
                break_time = old_break_time,
                expected_working_hour = old_expected_working_hour,
                state = 'draft',
                sign_in = NULL,
                sign_out = NULL,
                late_in = 0,
                early_out = 0,
                working_hour = 0,
                leave_line_id = NULL
            WHERE employee_id IN (%s)
            AND plan_line_id IS NOT NULL
            AND id IN (SELECT pwh.id 
                        FROM hr_payroll_working_hour pwh 
                        LEFT JOIN hr_holidays_line hl ON pwh.leave_line_id = hl.id 
                        WHERE
                        pwh.state = 'approve'
                        AND 
                        (
                            -- Create new approved leave request on PWH date
                            (pwh.leave_line_id IS NULL 
                                AND pwh.date IN (%s)
                            )
                            OR
                            -- Re-approved an old cancelled leave request 
                            (pwh.leave_line_id IS NOT NULL 
                                AND hl.write_date >= pwh.write_date
                                AND pwh.date IN (%s)
                            )
                        )
            );"""%(','.join(map(str, employee_ids)), ','.join(map(str, leave_dates)), ','.join(map(str, leave_dates)))
        cr.execute(revert_sql)
        logging.info("     ===> DONE REVERT PWH")
        
        logging.info("     ===> START READ PWH > PREPARE TO COMPUTE PWH BELOW....")
        #Read draft PWH to compute/re-compute below
        #pwh_data = {
        #           (date, employee_id, activity type): dict of select columns above,
        #           (date, employee_id, activity type): dict of select columns above,
        #           ...
        #           }
        select_pwh_sql = """
        SELECT 
            pwh.id, pwh.date, pwh.employee_id, act.type as act_type, 
            pwh.expected_start, pwh.expected_end, pwh.expected_working_hour,
            pwh.break_start, pwh.break_end, pwh.break_time,
            pwh.auth_late_in, pwh.auth_early_out, plan_line_id,job.tolerance,
            -- IF PWH has old_expected_start that mean recomputing 
            -- Using old_ for half day off
            pwh.old_expected_start, pwh.old_break_start, pwh.old_break_end, pwh.old_expected_end
        FROM 
            hr_payroll_working_hour pwh 
            JOIN hr_working_activity act ON pwh.activity_id = act.id
            JOIN hr_contract cnt ON pwh.contract_id = cnt.id
            LEFT JOIN hr_job job ON cnt.job_id = cnt.id
        WHERE
            pwh.date >= '%s'
            AND pwh.date <= '%s'
            AND pwh.employee_id in (%s)
            AND pwh.state = 'draft'
        """%(str_from_date, str_to_date, ','.join(map(str, employee_ids)))
        cr.execute(select_pwh_sql)
        pwh_data = {}
        for pwh in cr.dictfetchall():
            key = (pwh['date'], pwh['employee_id'], pwh['act_type'])
            if key in pwh_data: 
                pwh_data[key].append(pwh)
            else:
                pwh_data.update({key: [pwh]})
        logging.info('     **** PWHs DATA: %s'%str(len(pwh_data.keys())))
        
        #Backup activity_id, advanced working schedule info before compute PWH
        logging.info("     ===> BACKUP ACTIVITY, ADVANCED WORKING INFO OF WORKING PWH ....")
        backup_pwh_sql = """
            UPDATE hr_payroll_working_hour pwh
            SET old_activity_id =  pwh.activity_id,
                old_expected_start = pwh.expected_start,
                old_expected_end = pwh.expected_end,
                old_break_start = pwh.break_start,
                old_break_end = pwh.break_end,
                old_break_time = pwh.break_time,
                old_expected_working_hour = pwh.expected_working_hour
            WHERE date >= '%s'
                AND date <= '%s'
                AND employee_id in (%s)
                AND state = 'draft'
                -- Only backup PWH that generate from schedule
                -- Avoid backup PWH when recompute
                AND old_expected_start IS NULL
        """%(str_from_date, str_to_date, ','.join(map(str, employee_ids)))
        cr.execute(backup_pwh_sql)
        logging.info("     ===> DONE BACKUP WORKING PWH")
        logging.info('     *** DONE PREPARE DATA BEFORE COMPUTE PWH....')
        insert_sql = '' # Use to create PWH for a half day-off
        update_sql = '' # Use to update attendance info for working day and overtime
        dt_from_date = datetime.strptime(str_from_date, DEFAULT_SERVER_DATE_FORMAT)
        dt_to_date = datetime.strptime(str_to_date, DEFAULT_SERVER_DATE_FORMAT)
        
        logging.info("     ===> START COMPUTE PWH ......")
        while dt_from_date <= dt_to_date:
            str_date = dt_from_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
            logging.info('************************************')
            logging.info('     ===> DATE: %s ......'%str_date)
            for employee_id in employee_ids:
                logging.info('     ===> EMPLOYEE: %s ......'%employee_id)
                """    
                SCHEMA:
                - If there is no schedule (Means this date is day off or public holiday)
                 + Only need to compute overtime PWH if any: Use the attendances to compute attendance information of this PWH.
                - If there is a schedule (a payroll working hour exists on this day - working activity that has type 'Work')
                 + If there is a leave request (full day), update existing payroll working hour with real attendance information.
                 (Update working activity of this working hour to the activity of the leave type of this leave request).
                 + If there is a leave request (half day), create a payroll working hour for this leave request.
                 Update the existing payroll working hour to match real attendance information.
                 + If there is an overtime, create a payroll working hour
                 and use the attendances to compute attendance information.
                 + If there is no overtime nor leave request, use real attendance information to update existing payroll working hour.
                """
                work_key = (str_date, employee_id, 'work')
                ot_key = (str_date, employee_id, 'overtime')
                work_pwhs = pwh_data.get(work_key, [])
                ot_pwhs = pwh_data.get(ot_key, [])
                
                # PWH is generated from advanced working plan template
                main_work_pwh = False
                for pwh in work_pwhs:
                    if pwh['plan_line_id']:
                        main_work_pwh = pwh
                        #Remove from work_pwhs for no duplicate compute work_pwhs
                        #If have a leave request a half day off, we must update main_work_pwh info 
                        work_pwhs.remove(main_work_pwh)
                        break
                     
                if not main_work_pwh:
                    logging.info('           => THIS IS NOT WORKING DAY.....')
                    # If there is no schedule, only need to compute overtime/compensation
                    logging.info('              => Start compute overtime/compensation....')
                    for ot_pwh in ot_pwhs + work_pwhs:
                        update_sql += self._compute_attendances(cr, uid, ot_pwh['id'], ot_pwh['tolerance'],employee_id, 
                                                                ot_pwh['expected_start'], ot_pwh['expected_end'], 
                                                                ot_pwh['break_start'], ot_pwh['break_end'], 
                                                                ot_pwh['break_time'], max_early_in, max_late_out, 
                                                                context=context)
                    logging.info('              => Done compute overtime/compensation')
                else:
                    logging.info('           => THIS IS WORKING DAY.....')
                    # Leave request
                    logging.info('              => Start compute leave request')
                    leave = leave_data.get((str_date, employee_id), False)
                    if leave and leave['dayoff'] == 1:
                        logging.info("                   ==> Leave Date type %s"%leave['date_type'])
                        # Update if full day off
                        update_sql += self._full_off_update_sql(uid, main_work_pwh['id'],  
                                                                main_work_pwh['expected_working_hour'], 
                                                                leave['activity_id'], leave['id'])
                        #Set null main_work_pwh for no compute this pwh below
                        main_work_pwh = {}
                    elif leave and leave['dayoff'] == 0.5:
                        logging.info("                   ==> Leave Date type %s"%leave['date_type'])
                        old_expected_start = ''
                        old_expected_end = ''
                        new_expected_start = ''
                        new_expected_end = ''
                        if not main_work_pwh['old_expected_start']:
                            logging.info("                   ==> Start compute a half day-off")
                            #COMPUTE the first time
                            #If have no break time in a schedule. calculate break from = work from + expected_working_hour/2
                            temp_break_start = main_work_pwh['break_start']
                            if not temp_break_start:
                                dt_temp_break_start = datetime.strptime(main_work_pwh['expected_start'], DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(minutes=leave['dayoff']*main_work_pwh['expected_working_hour'])
                                temp_break_start = dt_temp_break_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                            
                            temp_break_end = main_work_pwh['break_end']
                            if not temp_break_end:
                                temp_break_end = temp_break_start
                            
                            # Off Morning
                            # old_expected_start/stop is expected_start/stop of original PWH
                            old_expected_start = temp_break_end #main_work_pwh['break_end']
                            old_expected_end = main_work_pwh['expected_end']
                            # new_expected_start/stop is expected_start/stop of New PWH for 0.5 day off
                            new_expected_start = main_work_pwh['expected_start']
                            new_expected_end = temp_break_start#main_work_pwh['break_start']
                            if leave['date_type'] == 'afternoon':
                                # Off Afternoon
                                old_expected_start = main_work_pwh['expected_start']
                                old_expected_end = temp_break_start #main_work_pwh['break_start']
                                new_expected_start = temp_break_end #main_work_pwh['break_end']
                                new_expected_end = main_work_pwh['expected_end']
                        else:
                            logging.info("                   ==> Start re-compute a half day-off")
                            #RECOMPUTE
                            temp_break_start = main_work_pwh['old_break_start']
                            if not temp_break_start:
                                dt_temp_break_start = datetime.strptime(main_work_pwh['old_expected_start'], DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(minutes=leave['dayoff']*main_work_pwh['expected_working_hour'])
                                temp_break_start = dt_temp_break_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                            
                            temp_break_end = main_work_pwh['old_break_end']
                            if not temp_break_end:
                                temp_break_end = temp_break_start
                            
                            # Off Morning
                            # old_expected_start/stop is expected_start/stop of original PWH
                            old_expected_start = temp_break_end #main_work_pwh['break_end']
                            old_expected_end = main_work_pwh['old_expected_end']
                            # new_expected_start/stop is expected_start/stop of New PWH for 0.5 day off
                            new_expected_start = main_work_pwh['old_expected_start']
                            new_expected_end = temp_break_start#main_work_pwh['break_start']
                            if leave['date_type'] == 'afternoon':
                                # Off Afternoon
                                old_expected_start = main_work_pwh['old_expected_start']
                                old_expected_end = temp_break_start #main_work_pwh['break_start']
                                new_expected_start = temp_break_end #main_work_pwh['break_end']
                                new_expected_end = main_work_pwh['old_expected_end']
                        
                        logging.info("                   ==> Work start: %s", old_expected_start)
                        logging.info("                   ==> Work end: %s", old_expected_end)
                        logging.info("                   ==> Off start: %s", new_expected_start)
                        logging.info("                   ==> Off end: %s", new_expected_end)
                       
                        # Original PWH
                        # Dict main_work_pwh use to compute attendances below
                        # main_work_pwh Update: expected_start, expected_start, expected_working_hour, break_start=NULL, break_end=NULL
                        dt_old_expected_start = datetime.strptime(old_expected_start, DEFAULT_SERVER_DATETIME_FORMAT)
                        dt_old_expected_end = datetime.strptime(old_expected_end, DEFAULT_SERVER_DATETIME_FORMAT)
                        expected_hour = time_obj.diff_hour(dt_old_expected_start, dt_old_expected_end)
                        update_sql += self._half_working_update_sql(uid, main_work_pwh['id'], 
                                                                    old_expected_start, old_expected_end, 
                                                                    expected_hour, leave['id'])
                        
                        main_work_pwh.update({'expected_start': old_expected_start,
                                              'expected_end': old_expected_end,
                                              'expected_working_hour': expected_hour,
                                              'break_start': '',
                                              'break_end': '',
                                              'break_time': 0})
                        # Create PWH for 0.5 day off
                        dt_new_expected_start = datetime.strptime(new_expected_start, DEFAULT_SERVER_DATETIME_FORMAT)
                        dt_new_expected_end = datetime.strptime(new_expected_end, DEFAULT_SERVER_DATETIME_FORMAT)
                        off_hour = time_obj.diff_hour(dt_new_expected_start, dt_new_expected_end)
                        
                        insert_data = """
                        SELECT 
                            NOW() AT TIME ZONE 'UTC', %s, NOW() AT TIME ZONE 'UTC', %s,
                            employee_id, date, advanced_schedule_id, %s, contract_id, 
                            '%s', '%s', NULL, NULL, NULL, %s, name, NULL, NULL, 
                            NULL, NULL, %s, 'approve', NULL, %s, False
                        FROM hr_payroll_working_hour pwh
                        WHERE id = %s
                        AND NOT EXISTS (SELECT 1 FROM hr_payroll_working_hour pwh
                                        JOIN hr_working_activity act ON pwh.activity_id = act.id
                                        WHERE act.type = 'daysoff'
                                        AND pwh.leave_line_id = %s
                                        AND pwh.date = '%s'
                                        AND pwh.state != 'cancel')
                        """%(uid, uid, leave['activity_id'], new_expected_start, new_expected_end, 
                             off_hour, off_hour, leave['id'], main_work_pwh['id'], leave['id'], str_date)
                        insert_sql += self._insert_sql(insert_data)
                    logging.info('              => Done compute leave request')
                    
                    # Official work/Compensation/Overtime
                    logging.info('              => Start compute attendances (work/Compensation/Overtime)')
                    main_work_pwhs = main_work_pwh and [main_work_pwh] or []
                    for work_pwh in work_pwhs + ot_pwhs + main_work_pwhs:
                        logging.info("""                ==> Work start %s, break start %s, 
                                    break end %s, work end %s
                                    """%(work_pwh['expected_start'], work_pwh['break_start'], 
                                         work_pwh['break_end'],work_pwh['expected_end']))
                        
                        update_sql += self._compute_attendances(cr, uid, work_pwh['id'], work_pwh['tolerance'], employee_id, 
                                                                work_pwh['expected_start'], work_pwh['expected_end'], 
                                                                work_pwh['break_start'], work_pwh['break_end'], 
                                                                work_pwh['break_time'], max_early_in, max_late_out, 
                                                                context=context)
                    logging.info('              => Done compute attendances (work/Compensation/Overtime)')
            logging.info('     ===> DONE DATE %s'%str_date)
            # Next date
            dt_from_date += relativedelta(days=1)
        logging.info("    ==> DONE COMPUTE PWH")
        insert_sql and cr.execute(insert_sql)
        update_sql and cr.execute(update_sql)
        
        # Get PWH IDs have been computed 
        pwh_ids = self.search(cr, uid, [('date', '>=', str_from_date),
                                        ('date', '<=', str_to_date),
                                        ('employee_id', 'in', employee_ids)], 
                              context=context)
        return pwh_ids
    
hr_payroll_working_hour()
