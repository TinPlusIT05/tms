# -*- coding: utf-8 -*-
##############################################################################
from openerp.report import report_sxw
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


import xlwt
from openerp.addons.report_xls.report_xls import report_xls
from openerp.tools.translate import _


WORK_DAY_CODE = 'X'
PUBLIC_HOLIDAY_CODE = 'H'
BUSINESS_TRAVEL_CODE = 'BT'

FULL_DAY = 2
HALF_DAY = 1
WEEKEND = ['Sat', 'Sun']


class Parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            "get_print_date": self.get_print_date,
            "get_wizard_data": self.get_wizard_data,
            "get_contract_ids_of_month": self.get_contract_ids_of_month,
            "get_employee_working_schedule":
            self.get_employee_working_schedule,
            "get_employee_leave_schedule": self.get_employee_leave_schedule,
            "get_report_data": self.get_report_data,
            "calculate_employee_schedule": self.calculate_employee_schedule,
            "get_date_detail": self.get_date_detail,
            "get_employee_info": self.get_employee_info,
            "get_total_header": self.get_total_header,

            "report_name": _('STAFF WORKING ATTENDANCE SHEET'),
        })

    def get_print_date(self):
        data = self.get_wizard_data()
        inp_month = data.get('month')
        inp_year = data.get('year')

        month = datetime(int(inp_year), int(inp_month), 1, 0, 0).strftime("%b")
        result = '%s %s' % (month, inp_year)
        return result.upper()

    def get_wizard_data(self):
        return self.localcontext.get("data")

    def get_date_detail(self):
        """
        """
        weekdays = []
        input_data = self.get_wizard_data()
        month = int(input_data.get('month'))
        year = int(input_data.get('year'))
        start_month = datetime(int(year), int(month), 1, 0, 0, 0).date()
        end_month = start_month + relativedelta(months=1) - timedelta(days=1)
        day_count = (end_month - start_month).days + 1
        for single_date in (
                start_month + timedelta(n) for n in range(day_count)):
            weekday = single_date.strftime("%a")
            weekdays.append((weekday, single_date.day))
        return weekdays

    def get_employee_info(self, employee_id, year, month):
        """
        Return employee name and contract info
        """
        sql_employee_name = '''
        SELECT he.name_related
        FROM hr_employee AS he
        WHERE he.id = %s
        ''' % (employee_id)
        self.cr.execute(sql_employee_name)
        results = self.cr.fetchall()
        employee_name = results[0][0]

        start_month = datetime(int(year), int(month), 1, 0, 0, 0).date()
        end_month = start_month + relativedelta(months=1) - timedelta(days=1)
        sql_employee_info = '''
        SELECT he.name_related, hct."name", hc.is_trial, hc.date_end
        FROM hr_employee AS he
            JOIN hr_contract AS hc
                ON hc.employee_id = he.id
            JOIN hr_contract_type AS hct
                ON hct.id = hc.type_id
        WHERE he.id = %s
            AND ((hc.date_end >= '%s' AND hc.date_start <= '%s')
                or (hc.date_end >= '%s' AND hc.date_start <= '%s')
                or (hc.date_start <= '%s' AND hc.date_end is null))
        ''' % (employee_id, start_month,
               start_month, end_month, end_month, end_month)
        self.cr.execute(sql_employee_info)
        results = self.cr.fetchall()
        if not results:
            return {'name': employee_name}
        contract_type = results[0][1]
        is_trial = results[0][2]
        end_date = results[0][3]
        info = {}
        # Employee's name
        info['name'] = results[0][0]
        # Employee's contract type
        if contract_type == 'Trainee':
            info['contract_type'] = 'Trainee'
        elif contract_type == 'Employee':
            if is_trial:
                info['contract_type'] = 'Trial'
            else:
                if end_date:
                    info['contract_type'] = '1 year'
                else:
                    info['contract_type'] = 'Unlimited'
        # Employee's total leave day up
        casual_leave = self.pool.get('ir.config_parameter').get_param(
            self.cr, self.uid,
            "default_leave_type_to_add_allocation_each_month") or None
        hol_status_ids = self.pool.get(
            'hr.holidays.status').search(
                self.cr, self.uid, [('name', '=', casual_leave)])

        allocation_day = self.pool.get(
            'hr.holidays').compute_allo_days(
                self.cr, self.uid, employee_id, hol_status_ids)
        casual_leave_day = 0.0
        if hol_status_ids:
            casual_leave_day = self.pool.get(
                'hr.holidays').compute_leave_days(self.cr, self.uid,
                                                  employee_id, hol_status_ids)
        info['total_leave'] = allocation_day - casual_leave_day

        return info

    def get_contract_ids_of_month(self, employee_id, year, month):
        if not employee_id:
            return []
        # Get wizard input data
        input_data = self.get_wizard_data()
        month = int(input_data.get('month'))
        year = int(input_data.get('year'))
        start_month = datetime(int(year), int(month), 1, 0, 0, 0).date()
        end_month = start_month + relativedelta(months=1) - timedelta(days=1)
        sql = '''
        SELECT hc.id FROM hr_contract AS hc
        WHERE hc.employee_id = %s
            AND ((hc.date_end >= '%s' AND hc.date_start <= '%s')
                or (hc.date_end >= '%s' AND hc.date_start <= '%s')
                or (hc.date_start <= '%s' AND hc.date_end is null))
        ''' % (employee_id, start_month,
               start_month, end_month, end_month, end_month)
        self.cr.execute(sql)
        results = self.cr.fetchall()
        contract_ids = [contract_id[0] for contract_id in results]
        return contract_ids

    def get_employee_working_schedule(self, employee_id, year, month):
        """
        Return dict to store employee working schedule on month in format.
        Get data from resource calendar on contracts of employee related to
        @month
        {day: n}. n as 0 is not working, 1 is working half day, 2 is full day
        EX: {
            1: 1,
            2: 2,
            3: 1,
            4: 0,
            5: 0,
            6: 2
            ...
        }
        """
        month_working_schedule = {}
        start_month = datetime(int(year), int(month), 1, 0, 0, 0).date()
        end_month = start_month + relativedelta(months=1) - timedelta(days=1)
        contract_ids = self.get_contract_ids_of_month(employee_id, year, month)
        for contract_id in contract_ids:
            # === get working schedule of this contract in month
            # Init working attendace dict
            working_attendance = {}
            for index in range(0, 7):
                working_attendance.setdefault(str(index), 0)
            sql_resource_calendar_attendance = '''
                SELECT
                    rca.dayofweek,
                    rca.hour_from,
                    rca.hour_to,
                    rca.number_hours
                FROM resource_calendar_attendance AS rca
                    JOIN resource_calendar AS rc
                        ON rca.calendar_id = rc.id
                    JOIN hr_contract AS hc
                        ON hc.working_hours = rc.id
                WHERE hc.id = %s
            ''' % (contract_id)
            self.cr.execute(sql_resource_calendar_attendance)
            results = self.cr.fetchall()
            for attend in results:
                if attend[0] in working_attendance:
                    working_attendance[attend[0]] += 1

            # get start and end of contract
            sql_contract_start_end = '''
                SELECT date_start, date_end
                FROM hr_contract
                WHERE id = %s
            ''' % (contract_id)
            self.cr.execute(sql_contract_start_end)
            results = self.cr.fetchall()
            start_contract = datetime.strptime(
                results[0][0], '%Y-%m-%d').date()
            if results[0][1] <= None:
                end_contract = end_month
            else:
                end_contract = datetime.strptime(
                    results[0][1], '%Y-%m-%d').date()
            # compute start and end
            start = max(start_month, start_contract)
            end = min(end_month, end_contract)
            day_count = (end - start).days + 1
            for single_date in (
                    start + timedelta(n) for n in range(day_count)):
                weekday = single_date.isocalendar()[2] - 1
                month_working_schedule[
                    single_date.day] = working_attendance.get(str(weekday), 0)
        # Fill not exist date in month as empty
        day_count = (end_month - start_month).days + 1
        for single_date in (
                start_month + timedelta(n) for n in range(day_count)):
            if single_date.day not in month_working_schedule:
                month_working_schedule[single_date.day] = ' '
        return month_working_schedule

    def get_employee_leave_schedule(self, employee_id, year, month):
        """
        Return dict to store employee leave schedule on month in format.
        Get data from resource calendar on contracts of employee related to
        @month
        There 3 type of data: leave request, Business trip and public holidays
        {day: [{code: n, ...}]}. n as 1 is leave half day, 2 is leave full day
        EX: {
            1: {'U': 1, 'Si': 1},
            2: {'BT': 2},
            ...
        }
        """
        month_leave_schedule = {}
        start_month = datetime(int(year), int(month), 1, 0, 0, 0).date()
        end_month = start_month + relativedelta(months=1) - timedelta(days=1)

        # ==== [Leave request data] ====
        sql_leave_line = '''
        SELECT
            line.first_date,
            line.last_date,
            line.first_date_type,
            line.last_date_type,
            status.code
        FROM hr_holidays_line AS line
            JOIN hr_holidays_status AS status
                ON line.holiday_status_id = status.id
        WHERE employee_id = %s
            AND state in ('validate', 'to_cancel')
            AND ((line.first_date >= '%s' AND line.first_date <= '%s')
                or (line.last_date >= '%s' AND line.last_date <= '%s'))
        ''' % (employee_id, start_month, end_month, start_month, end_month)
        self.cr.execute(sql_leave_line)
        results = self.cr.fetchall()
        for leave in results:
            first_date = datetime.strptime(leave[0], '%Y-%m-%d').date()
            last_date = datetime.strptime(leave[1], '%Y-%m-%d').date()
            first_date_type = leave[2]
            last_date_type = leave[3]
            code = leave[4]

            start = max(start_month, first_date)
            end = min(end_month, last_date)
            day_count = (end - start).days + 1
            for single_date in (
                    start + timedelta(n) for n in range(day_count)):
                weekday = single_date.strftime("%a")
                # Ignore weekend
                if weekday in WEEKEND:
                    continue
                day_temp_data = month_leave_schedule.get(single_date.day, {})
                if single_date == first_date:
                    if first_date_type == 'full':
                        day_temp_data[
                            code] = day_temp_data.get(code, 0) + FULL_DAY
                    else:
                        day_temp_data[
                            code] = day_temp_data.get(code, 0) + HALF_DAY
                elif single_date == last_date:
                    if last_date_type == 'full':
                        day_temp_data[
                            code] = day_temp_data.get(code, 0) + FULL_DAY
                    else:
                        day_temp_data[
                            code] = day_temp_data.get(code, 0) + HALF_DAY
                else:
                    day_temp_data[
                        code] = day_temp_data.get(code, 0) + FULL_DAY
                month_leave_schedule[single_date.day] = day_temp_data

        # ==== [Public holiday data] ====
        sql_public_holiday = '''
        SELECT h.code, h."date"
        FROM hr_public_holiday AS h
        WHERE h."date" >= '%s' AND h."date" <= '%s'
        ''' % (start_month, end_month)
        self.cr.execute(sql_public_holiday)
        results = self.cr.fetchall()
        for holiday in results:
            h_day = datetime.strptime(holiday[1], '%Y-%m-%d')
            weekday = h_day.strftime("%a")
            if weekday in WEEKEND:
                continue
            h_code = holiday[0]
            day_schedule = month_leave_schedule.get(h_day.day, {})
            day_schedule[h_code] = FULL_DAY  # Public holiday is alway full day
            month_leave_schedule[h_day.day] = day_schedule

        # ==== [Business Travel holiday data] ====
        sql_bt = '''
        SELECT he.id, bt.date_from, bt.date_to, lo.code, he.name_related, bt.id
        FROM hr_employee AS he
            JOIN hr_employee_support_training_rel AS rel
                ON rel.employee_id = he.id
            JOIN tms_support_training AS bt
                ON bt.id = rel.support_training_id
            JOIN tms_location_type AS lo
                ON lo.id = bt.location_id
        WHERE ((bt.date_from <= '%s' AND bt.date_from >= '%s')
                OR(bt.date_to <= '%s' AND bt.date_to >= '%s'))
            AND he.id=%s
        ''' % (end_month, start_month, end_month, start_month, employee_id)
        self.cr.execute(sql_bt)
        results = self.cr.fetchall()
        for rec in results:
            date_from = datetime.strptime(rec[1], '%Y-%m-%d').date()
            date_to = datetime.strptime(rec[2], '%Y-%m-%d').date()
            code = rec[3]

            start = max(start_month, date_from)
            end = min(end_month, date_to)
            day_count = (end - start).days + 1
            for single_date in (
                    start + timedelta(n) for n in range(day_count)):
                weekday = single_date.strftime("%a")
                # Ignore weekend
                if weekday in WEEKEND:
                    continue
                day_schedule = month_leave_schedule.get(single_date.day, {})
                day_schedule[code] = FULL_DAY  # BT is alway full day
                month_leave_schedule[single_date.day] = day_schedule

        return month_leave_schedule

    def count_number_business_travel_day(self, employee_id):
        """
        Return number of business travel
        """
        count = 0
        input_data = self.get_wizard_data()
        month = int(input_data.get('month'))
        year = int(input_data.get('year'))
        start_month = datetime(int(year), int(month), 1, 0, 0, 0).date()
        end_month = start_month + relativedelta(months=1) - timedelta(days=1)
        sql_bt = '''
        SELECT he.id, bt.date_from, bt.date_to, lo.code, he.name_related, bt.id
        FROM hr_employee AS he
            JOIN hr_employee_support_training_rel AS rel
                ON rel.employee_id = he.id
            JOIN tms_support_training AS bt
                ON bt.id = rel.support_training_id
            JOIN tms_location_type AS lo
                ON lo.id = bt.location_id
        WHERE ((bt.date_from <= '%s' AND bt.date_from >= '%s')
                OR(bt.date_to <= '%s' AND bt.date_to >= '%s'))
            AND he.id=%s
        ''' % (end_month, start_month, end_month, start_month, employee_id)
        self.cr.execute(sql_bt)
        results = self.cr.fetchall()
        for rec in results:
            date_from = datetime.strptime(rec[1], '%Y-%m-%d').date()
            date_to = datetime.strptime(rec[2], '%Y-%m-%d').date()

            start = max(start_month, date_from)
            end = min(end_month, date_to)
            day_count = (end - start).days + 1
            for single_date in (
                    start + timedelta(n) for n in range(day_count)):
                weekday = single_date.strftime("%a")
                # Ignore weekend
                if weekday in WEEKEND:
                    continue
                count += 1
        return count

    def calculate_employee_schedule(self, employee_id, year, month):
        """
        Computed by working schedule subtract leave schedule
        Return {1: 'X', 2: 'X', 3, 'Si/2', ...}
        """
        working_schedule = self.get_employee_working_schedule(
            employee_id, year, month)
        leave_schedule = self.get_employee_leave_schedule(
            employee_id, year, month)
        schedule = {}
        for day in working_schedule:
            day_str = ''
            work_number = working_schedule[day]
            leave_detail = leave_schedule.get(day, {})
            if leave_detail:
                for code in leave_detail:
                    if leave_detail[code] == 1:
                        day_str += '%s/2' % code
                    elif leave_detail[code] == 2:
                        day_str += '%s' % code
            if not day_str:
                if work_number == 2:
                    day_str = WORK_DAY_CODE
                elif work_number == 1:
                    day_str = '%s/2' % WORK_DAY_CODE
                else:
                    day_str = ''
            schedule[day] = day_str
        return schedule

    def get_business_travel_location_code(self):
        """
        Return list on Business Travel location code
        """
        sql_bt_code = '''
        SELECT code
        FROM tms_location_type
        '''
        self.cr.execute(sql_bt_code)
        results = self.cr.fetchall()
        return [rec[0] for rec in results]

    def get_public_holiday_code(self):
        """
        Return list of code of public holidays
        """
        input_data = self.get_wizard_data()
        month = int(input_data.get('month'))
        year = int(input_data.get('year'))
        start_month = datetime(int(year), int(month), 1, 0, 0, 0).date()
        end_month = start_month + relativedelta(months=1) - timedelta(days=1)

        public_holiday_codes = []
        sql_public_holiday = '''
        SELECT h.code
        FROM hr_public_holiday AS h
        WHERE h."date" >= '%s' AND h."date" <= '%s'
        ''' % (start_month, end_month)
        self.cr.execute(sql_public_holiday)
        results = self.cr.fetchall()
        for rec in results:
            if rec[0] not in public_holiday_codes:
                public_holiday_codes.append(rec[0])
        return public_holiday_codes

    def get_total_header(self):
        """
        Return active holidays status, work day, public holidays,
        Business travel and paid day
        """

        total_col_title_fmt = '''
        %s
        (%s)
        '''
        total_titles = [
            total_col_title_fmt % ('Work days', WORK_DAY_CODE)
        ]
        total_codes_header = []
        total_codes = [WORK_DAY_CODE]

        # ==== [Get active Leave type] ====
        sql_leave_type = '''
        SELECT name, code FROM hr_holidays_status
        WHERE active = true
        ORDER BY sequence
        '''
        self.cr.execute(sql_leave_type)
        results = self.cr.fetchall()
        for result in results:
            total_titles.append(
                total_col_title_fmt % (result[0], result[1]))
            total_codes.append(result[1])
        total_codes_header.extend(total_codes)

        # ==== [Get Public holidays] ====
        public_holiday_codes = self.get_public_holiday_code()
        total_titles.append(
            total_col_title_fmt % (
                'Public Holiday Leave', ' + '.join(public_holiday_codes))
        )
        total_codes_header.append(PUBLIC_HOLIDAY_CODE)

        # ==== [Get BT] ====
        bt_codes = self.get_business_travel_location_code()
        total_titles.append(
            total_col_title_fmt % ('Business Travel', ' + '.join(bt_codes)))
        total_codes_header.append(BUSINESS_TRAVEL_CODE)

        # ==== [Get SUM of paid] ====
        # Get paid datas
        sql_paid_leave_type = '''
        SELECT code FROM hr_holidays_status
        WHERE active = true AND payment_type='paid'
        ORDER BY code
        '''
        self.cr.execute(sql_paid_leave_type)
        results = self.cr.fetchall()
        paid_types = [WORK_DAY_CODE]
        paid_leave_types = [rec[0] for rec in results]
        paid_types.extend(paid_leave_types)
        paid_types.append(BUSINESS_TRAVEL_CODE)
        paid_types.append(PUBLIC_HOLIDAY_CODE)

        total_titles.append(
            total_col_title_fmt % ('SUM OF PAID DAYS', ' + '.join(paid_types)))
        total_codes_header.append('PAID')

        return total_titles, total_codes_header

    def get_employee_leave_summary(self, employee_id, year, month):
        """
        Ex: {'X': 22, code: num, ..., 'PAID': 23}
        1. Get workdays
        2. Get leave days by holidays status
        3. Get paid days
        """
        datas = {}

        start_month = datetime(int(year), int(month), 1, 0, 0, 0).date()
        end_month = start_month + relativedelta(months=1) - timedelta(days=1)

        # Get workdays
        workday = 0
        working_schedule = self.get_employee_working_schedule(
            employee_id, year, month)
        leave_schedule = self.get_employee_leave_schedule(
            employee_id, year, month)
        for day in working_schedule:
            work_number = working_schedule[day]
            work_number = str(work_number).strip()  # Avoid empty work_number
            if not work_number:
                continue
            work_number = int(work_number)  # Avoid empty work_number
            leave_detail = leave_schedule.get(day, {})
            if leave_detail:
                for code in leave_detail:
                    work_number = work_number - leave_detail[code]
            if work_number > 0:
                workday += 1.0 * work_number / 2
        datas[WORK_DAY_CODE] = workday

        #  Get leave days by holidays status
        sql_leave_summary = '''
        SELECT status.name, status.code, sum(line.number_of_days)
        FROM hr_holidays_line AS line
            JOIN hr_holidays_status AS status
                ON line.holiday_status_id = status.id
        WHERE employee_id = %s
            AND state in ('validate', 'to_cancel')
            AND active = True
            AND ((line.first_date >= '%s' AND line.first_date <= '%s')
                or (line.last_date >= '%s' AND line.last_date <= '%s'))
        group by status.name, status.code
        ORDER BY status.code
        ''' % (employee_id, start_month, end_month, start_month, end_month)
        self.cr.execute(sql_leave_summary)
        leave_summary = self.cr.fetchall()
        for result in leave_summary:
            datas[result[1]] = result[2]

        # Public holidays
        sql_public_holiday = '''
        SELECT count(h.id)
        FROM hr_public_holiday AS h
        WHERE h."date" >= '%s' AND h."date" <= '%s'
            AND h."is_template" = false
        ''' % (start_month, end_month)
        self.cr.execute(sql_public_holiday)
        results = self.cr.fetchall()
        datas[PUBLIC_HOLIDAY_CODE] = results[0][0]

        # Get business travel
        datas[BUSINESS_TRAVEL_CODE] = self.count_number_business_travel_day(
            employee_id)

        # Get paid days
        sql_paid_leave_type = '''
        SELECT code FROM hr_holidays_status
        WHERE active = true AND payment_type='paid'
        ORDER BY code
        '''
        self.cr.execute(sql_paid_leave_type)
        results = self.cr.fetchall()
        paid_leave_types = [rec[0] for rec in results]
        paidday = workday
        for result in leave_summary:
            if result[1] in paid_leave_types:
                paidday += result[2]
        paidday += datas[PUBLIC_HOLIDAY_CODE]
        paidday += datas[BUSINESS_TRAVEL_CODE]

        datas['PAID'] = paidday
        return datas

    def get_report_data(self):
        """
        Return report data
        [
            [name, contract, ..., X, X, si, ' ']
        ]
        """
        input_data = self.get_wizard_data()
        month = int(input_data.get('month'))
        year = int(input_data.get('year'))
        employee_ids = input_data.get('employee_ids', [])
        domain = [('active', '=', True)]
        if employee_ids:
            domain.append(('id', 'in', employee_ids))
        employees = self.pool.get('hr.employee').search(
            self.cr, self.uid, domain)
        report_data = []
        index = 1
        for employee in employees:
            # ===== employee data = info + working detail + summary =====
            # Info
            employee_info = self.get_employee_info(employee, year, month)
            if not employee_info:
                continue
            data = [
                index, employee_info.get('name', ''),
                employee_info.get('contract_type', ''), employee_info.get(
                    'total_leave', '')
            ]
            # working detail
            schedule = self.calculate_employee_schedule(employee, year, month)
            if not schedule:
                report_data.append(data)
                continue
            for k in range(0, 32):
                if k in schedule:
                    data.append(schedule[k])
            # summary
            leave_summary = self.get_employee_leave_summary(
                employee, year, month)
            type_names, types_code = self.get_total_header()
            for code in types_code:
                data.append(leave_summary.get(code, 0))
            report_data.append(data)
            index += 1

        return report_data


class StaffWorkingAttendanceReport(report_xls):

    '''
    Return xls report

    Input:
    - parser: Parse Class
    - style: xls_style
    - data: Wizard datas
    - objects:
    - workbook: Excel Workbook
    If you want more colors:
    https://github.com/python-excel/xlwt/blob/master/xlwt/Style.py
    '''

    def generate_xls_report(self, _p, _xs, data, objects, wb):
        ws = wb.add_sheet(_p.report_name[:31], cell_overwrite_ok=True)
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 0
        row_pos = 0
        _bc = 'black'
        _xs['borders_all'] = 'borders: left thin, \
            right thin, top thin, bottom thin, \
            left_colour %s, right_colour %s, \
            top_colour %s, bottom_colour %s;' % (_bc, _bc, _bc, _bc)
        _xs['middle'] = 'align: vert center;'
        _xs['alignment'] = 'alignment: wrap on;'
        _xs['fill_pale_blue'] = 'pattern: pattern solid, fore_color pale_blue;'
        _xs['fill_ice_blue'] = 'pattern: pattern solid, fore_color ice_blue;'
        _xs['fill_yellow'] = 'pattern: pattern solid, fore_color yellow;'
        _xs['fill_gray'] = 'pattern: pattern solid, fore_color gray25;'
        _xs['fill_light_turquoise'] = 'pattern: pattern solid, \
            fore_color light_turquoise;'
        _xs['fill_sky_blue'] = 'pattern: pattern solid, \
            fore_color sky_blue;'

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        # Title
        ws.row(row_pos).height_mismatch = True
        ws.row(row_pos).height = 256 * 2  # normal height have 256 units
        cell_big_title_style = xlwt.easyxf(_xs['wrap'] +
                                           _xs['left'] +
                                           _xs['bold'] +
                                           'font: height 300;')
        report_name = _p.report_name.upper() + ' - ' + _p.get_print_date()
        c_specs = [
            ('report_name', 8, 0, 'text', report_name),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_big_title_style)

        # Write an empty line
        c_specs = [
            ('empty', 1, 0, 'text', None),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_big_title_style)

        # CSS for Header
        header_format = _xs['borders_all'] + _xs['wrap'] + \
            _xs['alignment'] + _xs['middle'] + _xs['center']
        header_style_center = xlwt.easyxf(header_format)
        header_style_center_italic = xlwt.easyxf(
            header_format + _xs['italic'])

        header_style_center_italic = xlwt.easyxf(
            header_format + _xs['italic'])
        style_center_yellow = xlwt.easyxf(
            header_format + _xs['fill_yellow'])
        style_center_gray = xlwt.easyxf(
            header_format + _xs['fill_gray'])

        # ==== [Write report content] ====
        sat_cols = []  # position of saturdays
        sun_cols = []  # position of sunday
        # ---- [Write report header] ----
        col_pos = 0
        # Write employee info part header
        employee_info_headers = [
            'Emp No.', 'Name', 'Type of Contract',
            'Total leave day up to this month']
        col_specs_template = {}
        for col in employee_info_headers:
            if col == 'Name':
                col_specs_template[col] = {'header': [1, 36, 'text', _(col)]}
            else:
                col_specs_template[col] = {'header': [1, 12, 'text', _(col)]}
        ws.row(row_pos).height_mismatch = True
        ws.row(row_pos).height = 1200
        c_specs = map(lambda x: self.render(x, col_specs_template, 'header'),
                      employee_info_headers)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        for col, size, spec in row_data:
            data = spec[4]
            style = header_style_center_italic
            if not data:
                # if no data, use default values
                data = report_xls.xls_types_default[spec[3]]
            if data == 'Name':
                ws.col(col_pos).width = 24 * 256
            ws.write_merge(row_pos, row_pos + 1, col_pos, col_pos, data, style)
            col_pos += 1

        # Write days detail part header
        # --> set height of row
        ws.row(row_pos).height_mismatch = True
        ws.row(row_pos).height = 600
        ws.row(row_pos + 1).height_mismatch = True
        ws.row(row_pos + 1).height = 1200

        weekdays_header = _p.get_date_detail()
        col_specs_template = {}
        for col in weekdays_header:
            col_specs_template[col] = {'header': [1, 12, 'text', _(col[0])]}

        c_specs = map(lambda x: self.render(x, col_specs_template, 'header'),
                      weekdays_header)

        row_data_weekdays = self.xls_row_template(
            c_specs, [x[0] for x in c_specs])
        for col, size, spec in row_data_weekdays:
            weekday = spec[0][0]
            day = spec[0][1]
            if not data:
                # if no data, use default values
                data = report_xls.xls_types_default[spec[3]]
            if weekday == 'Sat':
                style = style_center_yellow
                sat_cols.append(col_pos)
            elif weekday == 'Sun':
                style = style_center_gray
                sun_cols.append(col_pos)
            else:
                style = header_style_center
            ws.write_merge(row_pos, row_pos, col_pos, col_pos, weekday, style)
            ws.write_merge(
                row_pos + 1, row_pos + 1, col_pos, col_pos, day, style)
            col_pos += 1
        # leave summary header part
        types_name, types_code = _p.get_total_header()
        col_specs_template = {}
        for col in types_name:
            col_specs_template[col] = {'header': [1, 24, 'text', _(col[0])]}

        c_specs = map(lambda x: self.render(x, col_specs_template, 'header'),
                      types_name)

        row_data_types = self.xls_row_template(
            c_specs, [x[0] for x in c_specs])
        ws.write_merge(
            row_pos, row_pos, col_pos, col_pos + len(types_name) - 1,
            'Total', style)
        for col, size, spec in row_data_types:
            type_name = spec[0]
            style = header_style_center_italic
            ws.col(col_pos).width = 24 * 256
            ws.write_merge(
                row_pos + 1, row_pos + 1, col_pos, col_pos, type_name, style)
            col_pos += 1

        row_pos += 2
        col_pos = 0
        # ---- End write report header

        # ---- [Write report data]

        # CSS for cell
        cell_format = _xs['wrap'] + _xs['alignment'] + \
            _xs['middle'] + _xs['borders_all']
        cell_style = xlwt.easyxf(cell_format + _xs['center'])

        for line in _p.get_report_data():
            ws.row(row_pos).height_mismatch = True
            ws.row(row_pos).height = 2 * 256

            c_specs = []
            index = 0
            for item in line:
                cur_col = index
                index += 1
                if cur_col in sat_cols:
                    style = style_center_yellow
                elif cur_col in sun_cols:
                    style = style_center_gray
                else:
                    style = cell_style
                c_specs.append(
                    (index, 1, 0, 'text', unicode(item), None, style))

            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(ws, row_pos, row_data)


StaffWorkingAttendanceReport('report.staff_working_attendance',
                             'tms.working.hour',
                             parser=Parser)
