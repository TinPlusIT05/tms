# -*- encoding: utf-8 -*-

{
    "name" : "Trobz HR Advanced Working Schedule",
    "version" : "1.0",
    "category": "Generic Modules/Human Resources",
    "depends" : [
        # Trobz Standard
        'trobz_base',
        'trobz_hr_holiday',
        'trobz_hr_payroll_working_hour',
        'trobz_hr_payroll_overtime',
        ],
    "author" : "Trobz",
    "description": """
Trobz HR Advanced Working Schedule
==============================
**Advanced Working Time**

**Advanced Working Schedule**

**Advanced Working Plan Template**

**Check attendances consistency**

**Employee**
Link to the latest advanced working schedule in current date

**Payroll Working Hours**
Add more fields:
- Advanced working schedule 
- Flexible

**Overtime**
Add more fields:
- Advanced working schedule

**Expected Working Days**
When genrate the payroll working hours, the expected working days will be created/updated for the selected period

**Holiday**
- Public hoildays: add status (draft, approve)
- On the leave request, the number of leave days will be calculate base on the advanced working plan template and approved public holidays

**Compute Payslip**
- The Payslip Worked Days will be calculated base on the payroll working hours that group by the working activity and flexible day 

""",
    'website': 'http://trobz.com',
    'data': [
        #data
        'data/hr_advanced_working_schedule_data.xml',
        #security
        "security/ir.model.access.csv",
        'data/ir_cron_data.xml',
        
        #view
        'view/hr_advanced_working_time_view.xml',
        'view/hr_advanced_working_schedule_view.xml',
        'view/hr_payroll_working_hour_view.xml',
        'view/resource_calendar_view.xml',
        'view/resource_calendar_attendance_view.xml',
        'view/hr_attendance_view.xml',
        'view/trobz_hr_public_holidays_view.xml',
        'view/hr_employee_view.xml',
        'view/hr_expected_working_day_view.xml',
        'view/hr_overtime_view.xml',
        
        #wizard
        'wizard/generate_working_hour_wizard.xml',
        'wizard/approve_public_holiday_wizard.xml',
        'wizard/compute_working_hour_wizard.xml',
        
        #menu
        'menu/hr_menu.xml',
    ],
    'demo_xml': [],  
    'installable': True,
    'active': False,
    'certificate' : '',
    'post_objects': [],
}
