from trobz_report_base.report import trobz_report_base
from datetime import datetime

class Parser(trobz_report_base.Parser):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
    
        self.report_name = 'detect_absence_report'
        self.localcontext.update({
            'get_date': self.get_date,
            'get_employees_absence': self.get_employees_absence,
        })
        
    def get_wizard_data(self):
        res = {}
        datas = self.localcontext['data']
        if datas:
            res['date'] = datas['form']['date'] or False
        return res
    
    def get_date(self):
        res = self.get_wizard_data()
        return res['date'] or False
    
    def get_employees_absence(self):
        """
        return: List all employees under contract who have no attendance,
         nor leave requests for a given date while they should be here according to the working schedule.
         
         [{'name': employee1, 'last_in': , 'last_out'}]
        """
        date = self.get_date()
        list_employees = []
        if not date:
            return list_employees
        emp_obj = self.pool.get('hr.employee')
        date_time = datetime.strptime(str(date), '%Y-%m-%d')
        week_date = date_time.weekday()
        sql = """
            SELECT employee_id 
            FROM hr_contract
            WHERE working_hours IN (
                SELECT DISTINCT rc.id 
                FROM resource_calendar rc JOIN resource_calendar_attendance rce ON rc.id = rce.calendar_id
                WHERE dayofweek = '%s'
                )
            EXCEPT
            SELECT employee_id FROM hr_attendance
            WHERE day = '%s'
            EXCEPT
            SELECT employee_id FROM hr_holidays
            WHERE DATE('%s') <= DATE(date_to) AND DATE('%s') >= DATE(date_from)
            AND state='validate'
        """% (week_date, date, date, date)
        self.cr.execute(sql)
        employee_ids = []
        for employee_id in self.cr.fetchall():
            employee_ids.append(employee_id[0])
        for employee_id in employee_ids:
            sql = """
                SELECT name, action
                FROM hr_attendance
                WHERE (name = ( SELECT max(name) 
                                FROM hr_attendance
                                WHERE employee_id = %s AND action = 'sign_in') AND action = 'sign_in')
                        OR 
                        (name = (SELECT max(name) 
                                FROM hr_attendance
                                WHERE employee_id = %s AND action = 'sign_out') AND action = 'sign_out')
            """% (employee_id, employee_id)
            self.cr.execute(sql)
            attendances = {}
            for attendance in self.cr.fetchall():
                attendances[attendance[1]] = attendance[0]
            list_employees.append({
                        'employee': emp_obj.read(self.cr, self.uid, employee_id, ['name']).get('name',''),
                        'last_in':attendances.get('sign_in',False),
                        'last_out':attendances.get('sign_out',False),
                   })
        return list_employees
        
        
        
        
        
        