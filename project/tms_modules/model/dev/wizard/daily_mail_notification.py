# -*- encoding: UTF-8 -*-
from datetime import datetime, timedelta, date

from openerp import fields, api, models
import math
import logging
logger = logging.getLogger('tracker')


class daily_mail_notification(models.TransientModel):

    _name = 'daily.mail.notification'
    _description = 'send notification email to user'

    user_id = fields.Integer(string="User", required=True,
                             default=lambda self: self._uid)

    @api.multi
    def button_send_email_notification(self):
        email_template = self.env['email.template']
        email_template.send_daily_notifications_mail()
        return True

    @api.model
    def _get_kpi_from_sql(self, sql_query, params):
        sql_query = sql_query % params
        self._cr.execute(sql_query)
        res = self._cr.fetchall()
        result = [x[0] for x in res]
        return result[0]

    SQL_NET_TIME_SPENT = '''
        SELECT SUM(working_hour) FROM (
            SELECT user_id, login, sum(duration_hour) AS working_hour FROM (
            SELECT
                twh.id, twh.user_id, twh.employee_id, twh.date,
                twh.duration_hour, twh.tms_activity_id, rus.login
            FROM tms_working_hour twh
                JOIN tms_activity tac ON twh.tms_activity_id = tac.id
                JOIN res_users rus ON twh.user_id = rus.id
                JOIN resource_resource rr ON rr.user_id = rus.id
                JOIN hr_employee hem ON hem.resource_id = rr.id
                JOIN hr_department hed ON hem.department_id = hed.id
                JOIN hr_job hjb ON hem.job_type_id = hjb.id
            WHERE tac.name NOT IN ('Days Off', 'Compensation')
                AND twh.sprint = '%s'
                AND hed.name IN ('Production', 'Web')
                AND hjb.name NOT IN ('Functional Consultant')
                %s
            ) one
            GROUP BY user_id, login
        ) AS two
    '''

    SQL_BILLABLE_AND_NO_QUOTATION_REMAINING_TIME = '''
        select sum(remaining_time)
        from tms_forge_ticket tft
        join tms_project tp on tp.id = tft.project_id
        where tft.state <> 'closed'
        and tft.is_billable is True
        and tft.quotation='no'
        and tp.active = 't'
    '''

    SQL_TIME_SPENT_FIXING = '''
        select sum(twh.duration_hour)
        from tms_working_hour twh
        join tms_forge_ticket tft on tft.id = twh.tms_forge_ticket_id
        where twh.sprint = '%s'
        and tft.completion_date < twh.date
    '''

    SQL_VERY_HIGH_OPEN_TICKET_AVG_AGE = '''
        select ROUND(AVG(EXTRACT(epoch FROM CURRENT_TIMESTAMP
        at TIME ZONE 'UTC'-tft.create_date)/3600)) as AGE
        from tms_forge_ticket tft
        where tft.priority='very_high'
        and state <> 'closed';
    '''

    SQL_NOT_LOW_PRIORITY_OPEN_TO_TROBZ_TICKET_AVG_AGE = '''
        select round(AVG(EXTRACT(epoch FROM CURRENT_TIMESTAMP
        at TIME ZONE 'UTC'-tst.create_date)/86400)) as AGE
        from tms_support_ticket tst
        join res_users rus on rus.id = tst.owner_id
        where tst.priority<>'minor'
        and rus.is_trobz_member is True
        and tst.state <> 'closed';
    '''

    SQL_SPRINT_REMAINING_TIME = '''
        select sum(remaining_time)
        from tms_forge_ticket tft
        where tft.sprint='%s'
    '''

    SQL_SUM_HOURS_OF_LR_BY_DEV_OVERLAPING_DATES = '''
        select -8*sum(number_of_days)
        from hr_holidays
        where
            type='remove'
            and user_id=%s
            and (
                ( date_from > '%s' and date_from < '%s')
                or
                (date_to > '%s' and date_to < '%s')
            )
    '''

    SQL_SUM_WORKING_HOURS_BY_SPRINT_AND_TYPE_AND_DEV = '''
        select sum(duration_hour)
        from tms_working_hour twh
        join tms_activity tac on tac.id = twh.tms_activity_id
        where
        twh.sprint = '%s'
        and tac.name = '%s'
        and twh.user_id = '%s'
    '''

    SQL_SUM_HOURS_WORKING_SCHEDULE_BY_DEV = '''
        select sum(number_hours)
        from hr_contract hco
        join hr_employee hem on hem.id=hco.employee_id
        join resource_resource rre on rre.id = hem.resource_id
        join resource_calendar rca on rca.id = hco.working_hours
        join resource_calendar_attendance rcat on rcat.calendar_id = rca.id
        where rre.user_id=%s
        and (hco.date_end is null or '%s'<hco.date_end)
    '''

    SQL_OPEN_TO_TROBZ_TICKET_MAX_AGE_BY_PRIORITY = '''
        select round(max(EXTRACT(epoch FROM CURRENT_TIMESTAMP
        at TIME ZONE 'UTC'-tst.create_date)/86400)) as AGE
        from tms_support_ticket tst
        join res_users rus on rus.id = tst.owner_id
        where tst.priority in %s
        and rus.is_trobz_member is True
        and tst.state <> 'closed'
        and tst.project_state = 'active';
    '''

    SQL_MAX_READY_INTEGRATION = '''
        select max(nb) from (
            select count(tft.id) as nb
            from tms_forge_ticket tft
            where tft.state in ('code_completed','ready_to_deploy')
            group by tft.project_id
        ) as result
    '''

    SQL_MAX_READY_STAGING = '''
        select max(nb) from (
            select count(tft.id) as nb
            from tms_forge_ticket tft
            where tft.delivery_status= 'ready_for_staging'
            group by tft.project_id
        ) as result
    '''
    # get sum of all ticket estimated time for sprint
    SQL_NET_PRODUCTIVITY = '''
        select sum(development_time)
        from tms_forge_ticket tft
        join res_users rus on rus.id = tft.developer_id
        join resource_resource rre on rre.user_id = rus.id
        join hr_employee hem on hem.resource_id = rre.id
        join hr_department hde on hde.id = hem.department_id
        join hr_job hjb on hem.job_type_id = hjb.id
        where
        tft.completion_sprint_date = '%s'
        and hde.name in ('Production','Web')
        and hjb.name NOT IN ('Functional Consultant')
        %s
    '''

    def color_KPI_value(self, target, rate):
        """
        if net_productivity_rate, parameter input:
        (net_productivity_target,net_productivity_rate)
        if reopening_rate, parameter input:
        (reopening_rate,net_productivity_rate)
        """
        target, rate = float(target), float(rate)

        if not rate or not target:
            return '#F00'

        if rate > target:
            color = '#33CC00'
        elif rate < target and target / rate >= 2:
            color = '#F00'
        else:
            color = '#c2631b'
        return color

    @api.model
    def get_sprint_capacity(self, sprint):
        """
        @param sprint: a browse tms.sprint object
        @return integer: total of all employees in openerp
            department, not including FC
        """
        if not sprint:
            raise Warning("Warning!", "No sprint to get capacity.")

        sql_query = u"""
            SELECT SUM(COALESCE(ed.working_hour, 0) * ec.rate / 100) FROM (
                SELECT * FROM (
                    /*
                      LIST OF EMPLOYEE CAPACITY
                    */
                    SELECT id, user_id, login, rate, apply_sprint,
                    current_sprint, row_number() OVER (
                        PARTITION BY login
                        ORDER BY
                            apply_sprint DESC, capacity_id DESC
                    ) AS row
                    FROM (
                    SELECT he.id, rus.id AS user_id, he.login AS login,
                        hec.production_rate AS rate, hec.id AS capacity_id,
                        CAST(hec.starting_date AS VARCHAR) AS apply_sprint,
                        CAST('{ids}' AS VARCHAR) AS current_sprint

                    FROM hr_employee he
                        JOIN hr_department hd
                        ON he.department_id = hd.id
                        JOIN hr_employee_capacity hec
                        ON hec.employee_id = he.id
                        JOIN resource_resource rr
                        ON rr.id = he.resource_id
                        JOIN res_users rus
                        ON rus.id = rr.user_id
                        JOIN hr_job hjb
                        ON he.job_type_id = hjb.id
                    WHERE
                        hd.name IN ('Production', 'Web') AND
                        hjb.name NOT IN ('Functional Consultant')
                    ) one
                    WHERE apply_sprint <= current_sprint
                ) two WHERE two.row = 1
            ) AS ec
            JOIN (
                /*
                  WORKING HOUR FOR EACH EMPLOYEE (USER),
                  EXCLUDING days off + compensation
                */
                SELECT * FROM (
                    SELECT user_id, login, sum(duration_hour) AS working_hour
                    FROM (
                        SELECT
                            twh.id, twh.user_id, twh.employee_id, twh.date,
                            twh.duration_hour, twh.tms_activity_id, rus.login
                        FROM tms_working_hour twh
                            JOIN tms_activity tac
                            ON twh.tms_activity_id = tac.id
                            JOIN res_users rus
                            ON twh.user_id = rus.id
                            JOIN resource_resource rr
                            ON rr.user_id = rus.id
                            JOIN hr_employee hem
                            ON hem.resource_id = rr.id
                            JOIN hr_department hed
                            ON hem.department_id = hed.id
                            JOIN hr_job hjb ON hem.job_type_id = hjb.id
                        WHERE tac.name NOT IN ('Days Off', 'Compensation')
                            AND hed.name IN ('Production', 'Web')
                            AND twh.sprint IN ('{ids}')
                            AND hjb.name NOT IN ('Functional Consultant')
                    ) one
                    GROUP BY user_id, login
                ) AS two
            ) ed

            ON ec.user_id = ed.user_id;
        """.format(ids=",".join(map(str, [sprint.strftime('%Y-%m-%d')])))
        self._cr.execute(sql_query)
        result = self._cr.fetchall()
        result = (result and result[0] and result[0][0] or 0)
        return int(result)

    @api.model
    def get_target_value(self, target_name):
        return self.env['email.template'].get_target_value(target_name)

    # ticket 3297 - get target for each kpi indicators
    @api.model
    def process_target_kpi_from_sprint(self):
        rs = '<tr><td style="text-align:center;' +\
            'font-weight: bold;">Target</td>'
        try:
            # getting target value for each kpi indicators
            rs += '<td align="right">{0}</td>'.format(
                str(int(self.get_target_value('Net Productivity rate'))) +
                '%' if self.get_target_value('Net Productivity rate')
                else '<span style="color:#F00">Missing</span>')
            rs += '<td align="right">{0}</td>'.format(
                str(int(self.get_target_value('Reopening rate'))) +
                '%' if self.get_target_value('Reopening rate')
                else '<span style="color:#F00">Missing</span>')
            rs += ('<td style="text-align:left;">--</td>' * 7)
        except Exception:
            rs += '<td colspan="10" style="color:#F00;">' +\
                'Error when getting target value (missing or something..),' +\
                'please check.</td>'
        rs += '</tr>'
        return rs

    @api.model
    def get_employee_working_hours_by_theory(self, sprint):

        # Get list of employees, don't care if they are working or not
        sql_query = """
            SELECT hem.id
            FROM res_users rus
                JOIN resource_resource rr
                    ON rr.user_id = rus.id
                JOIN hr_employee hem
                    ON hem.resource_id = rr.id
                JOIN hr_department hed
                    ON hem.department_id = hed.id
                JOIN hr_job hjb
                    ON hem.job_type_id = hjb.id
            WHERE TRUE
                AND hed.name IN ('Production', 'Web')
                AND rus.is_trobz_member = 't'
                AND rus.must_input_working_hour = 't'
                AND hjb.name NOT IN ('Functional Consultant')
            ORDER BY rus.id
        """
        self._cr.execute(sql_query)
        result = self._cr.fetchall()
        employee_ids = [_res[0] for _res in result]
        # get object pool references
        employee_pool = self.env["hr.employee"]

        # get employee whose contract is still valid during current sprint
        employees = employee_pool.browse(employee_ids)
        valid_employees = []
        for _emp in employees:
            for contract in _emp.contract_ids:
                if contract.date_start <= sprint.strftime('%Y-%m-%d') and\
                    (contract.date_end >= sprint.strftime('%Y-%m-%d') or
                     not contract.date_end):
                    valid_employees.append(_emp)
                    break
        # check if current sprint or not
        sprint_curr = self.get_current_sprint()
        current_sprint = sprint == sprint_curr

        # get specific period for sprint
        now_period = datetime.now()

        # working hours total
        wh_total = 0.0

        # get working hour details (attendances)
        for emp in valid_employees:
            working_schedule = emp.contract_id.working_hours
            attendances = working_schedule.attendance_ids or []
            emp_duration = 0.0

            for attendance in attendances:
                duration = attendance.hour_to - attendance.hour_from
                within_range = int(attendance.dayofweek) < int(
                    now_period.weekday())

                if not current_sprint or within_range:
                    emp_duration += duration
                    wh_total += duration
        return wh_total

    def _get_rounded_rate(self, numerator, denominator):
        if not numerator:
            numerator = 0
        if not denominator or denominator == 0:
            return 'na'
        return '%s%%' % str(
            int(round(float(numerator) / float(denominator) * 100)))

    @api.model
    def get_next_sprint(self, sprint_date=None):
        return self._get_neighbour_sprint(True, sprint_date)

    @api.model
    def get_previous_sprint(self, sprint_date=None):
        return self._get_neighbour_sprint(False, sprint_date)

    @api.model
    def get_sprint_by_date(self, date):
        if type(date) is str:
            date = datetime.strptime(date, '%Y-%m-%d')
            sprint_date = date + timedelta(days=(5 - date.weekday()))
        else:
            sprint_date = date + timedelta(days=(5 - date.weekday()))
        if sprint_date:
            return sprint_date

    @api.model
    def get_current_sprint(self):
        return self.get_sprint_by_date(date.today().strftime('%Y-%m-%d'))

    @api.model
    def _get_neighbour_sprint(self, is_get_next=True, sprint_date=None):
        if sprint_date:
            if is_get_next:
                neighbour_sprint_date = sprint_date + timedelta(
                    days=7
                )
            else:
                neighbour_sprint_date = sprint_date - timedelta(
                    days=7
                )
            if not neighbour_sprint_date:
                raise Warning(
                    'Missing sprint!',
                    'No sprint defined for that period, '
                    'you must create a sprint first.')

            return neighbour_sprint_date

        return self.get_next_sprint(self.get_current_sprint())

    @api.multi
    def _compute_forge_indicators(self, cur_sprint):
        forge_ticket_env = self.env['tms.forge.ticket']
        indicators = forge_ticket_env.get_forge_indicators(
            [('sprint', '=', cur_sprint.strftime('%Y-%m-%d'))])
        return indicators['remaining']

    @api.model
    def process_kpi_result_from_sprint(self, current_sprint_date):

        rs = ''  # store html result
        td = '<td align="right">{0}</td>'  # table cell template
        rows = {}  # empty dict to store kpi values
        targets = {}  # empty dict to store target values

        # get target value (for two first indicators only - in percentage unit)
        targets.update(
            {'Net_Productivity_rate':
             int(self.get_target_value('Net Productivity rate'))})
        targets.update(
            {'Reopening_rate':
             int(self.get_target_value('Reopening rate'))})

        # start to operate on the next sprint to get the previous sprint (to
        # including current sprint)
        next_sprint_date = self.get_next_sprint(current_sprint_date)

        # show 5 sprints (including current sprint)
        for i in range(1, 6):
            previous_sprint_date =\
                self.get_previous_sprint(next_sprint_date)
            current_sprint = previous_sprint_date

            # set current sprint (the next sprint) to previous sprint to
            # start operate on the current next time
            next_sprint_date = current_sprint

            # ------------------------------------------ #
            # ------ Get and calculate kpi values ------ #
            # ------------------------------------------ #

            # Total time spent (for all employee (excluding 'Days Off' and
            # 'Compensation')
            net_time_spent_dev = self._get_kpi_from_sql(
                self.SQL_NET_TIME_SPENT,
                (current_sprint.strftime('%Y-%m-%d'), '')) or 0
            net_time_spent_dev = int(round(net_time_spent_dev))
            # Net Productivity
            net_productivity = self._get_kpi_from_sql(
                self.SQL_NET_PRODUCTIVITY,
                (current_sprint.strftime('%Y-%m-%d'), '')) or 0
            net_productivity = int(round(net_productivity))
            # Remaining Todo => current time remaining of a sprint
            remaining_todo = \
                int(math.floor(self._compute_forge_indicators(current_sprint))) or 0
            # Capacity
            capacity = self.get_sprint_capacity(current_sprint)
            # Working hours by theory for current sprint
            theory_wh = self.\
                get_employee_working_hours_by_theory(current_sprint)
            # Missing working hour
            missing_whs = int(theory_wh - net_time_spent_dev)
            # Ticket closed (Number)
            next_sprint_day = current_sprint + timedelta(days=1)
            tickets_closed_domain = [
                ('closing_datetime', '>', (
                    current_sprint - timedelta(days=6)
                ).strftime('%Y-%m-%d')),
                ('closing_datetime', '<', next_sprint_day.strftime('%Y-%m-%d'))]
            tickets_closed =\
                len(self.env['tms.forge.ticket'].
                    search(tickets_closed_domain)) or 0
            # Ticket reopened (Number)+
            tickets_reopened_domain = [
                ('sprint', '=', current_sprint.strftime('%Y-%m-%d')),
                ('reopening_type', '=', 'defect')]
            tickets_reopened = len(
                self.env['forge.ticket.reopening'].
                search(tickets_reopened_domain)) or 0
            # Net productivity %
            # (in case of 'na' check before manipulating with this)
            # Formula = (net_productivity / capacity) * 100
            net_productivity_rate = str(
                self._get_rounded_rate(
                    net_productivity, capacity)).replace('%', '') or 0

            # Reopening % (in case of 'na' check before manipulating with this)
            # Formula = (tickets_reopened /
            #     (tickets_reopened + tickets_closed)) * 100
            reopening_rate = str(self._get_rounded_rate(
                tickets_reopened, tickets_reopened + tickets_closed)).replace(
                '%', '') or 0
            # -------------------------------- #
            # ------ show result as table -----#
            # -------------------------------- #

            # sprint name
            rs += '<tr><td style="text-align:center;' +\
                ' font-weight: bold;">{0}</td>'.format(
                    current_sprint.strftime('%Y-%m-%d'))

            # Net Productivity (%)
            if net_productivity_rate != 'na':
                if targets['Net_Productivity_rate'] and\
                        int(net_productivity_rate):
                    pr_color = self.\
                        color_KPI_value(targets['Net_Productivity_rate'],
                                        int(net_productivity_rate))
                    rs += '<td align="right" style="color:{0};">{1}%</td>'.\
                        format(pr_color, net_productivity_rate)
                else:
                    rs += '<td align="right">{0}%</td>'.\
                        format(net_productivity_rate)
            else:
                rs += '<td align="right">{0}</td>'.\
                    format(net_productivity_rate)

            # Reopening (%)
            if reopening_rate != 'na':
                if targets['Reopening_rate'] and int(reopening_rate):
                    rr_color = self.\
                        color_KPI_value(
                            int(reopening_rate), targets['Reopening_rate'])
                    rs += '<td align="right" style="color:{0};">{1}%</td>'.\
                        format(rr_color, reopening_rate)
                else:
                    rs += '<td align="right">{0}%</td>'.format(reopening_rate)
            else:
                rs += '<td align="right">{0}</td>'.format(reopening_rate)

            # Net Productivity
            rs += td.format(net_productivity)
            # Remaining Todo
            rs += td.format(remaining_todo)
            # Capacity
            rs += td.format(capacity)
            # Working Time (net time spent dev)
            rs += td.format(net_time_spent_dev)
            # Missing working hour based on theory
            rs += td.format(missing_whs)
            # Tickets closed
            rs += td.format(tickets_closed)
            # Tickets reopened
            rs += td.format(tickets_reopened)

            # add current sprint data to dict for calculating average at the
            # end

        # ====================
        # calculate average for 4 sprints (including current sprint)

        # Sort collection before calculating sprint average (to exclude the
        # current sprint from the list which is the first item in list)
        rows = sorted(rows.iteritems())[::-1]
        rs += '<tr><td style="text-align:center;' +\
            ' font-weight: bold;">Average past 4 sprints</td>'

        # For each column in KPI Table
        for i in range(0, 9):

            # Get result of all rows in the i-th column (except the first row -
            # a.k.a current sprint)
            crows = [
                float(item[1][i] if item[1][i] != 'na' else 0)
                for index, item in enumerate(rows) if index != 0
            ]

            # We only calculate the average of 4 sprint (exclude current sprint
            # -> should be len of row - 1)
            avg = int(round(sum(crows) / (len(rows) - 1)))

            if i == 0:
                if targets['Net_Productivity_rate']:
                    target = targets['Net_Productivity_rate']
                    color = self.color_KPI_value(target, avg)
                    rs += '<td align="right" style="color:{0};">{1}%</td>'.\
                        format(color, avg)
                else:
                    rs += '<td align="right">{0}%</td>'.format(avg)
            elif i == 1:
                if targets['Reopening_rate']:
                    target = targets['Reopening_rate']
                    color = self.color_KPI_value(avg, target)
                    rs += '<td align="right" style="color:{0};">{1}%</td>'.\
                        format(color, avg)
                else:
                    rs += '<td align="right">{0}%</td>'.format(avg)
            else:
                rs += td.format(avg)
        rs += '</tr>'

        return rs

    @api.model
    def get_sprint_done_todo_capacity(self):
        try:
            if datetime.today().weekday() == 6:
                current_sprint_date = datetime.today() \
                    + timedelta(days=(6))
            else:
                current_sprint_date = datetime.today() \
                    + timedelta(days=(5 - datetime.today().weekday()))
        except Exception:
            return 'Missing sprint!'
        if not current_sprint_date:
            return 'Missing sprint!'
        # ticket 3297
        rs = '''
            <style type="text/css">
                table#api-table {
                border-collapse: collapse; font-size: 12.5px;}
                table#api-table tr td, table, tr th
                {padding: 5px; border: 1px solid #333;}
                table#api-table tr th, table tr td:first-child
                {font-weight: bold; text-align: center;}
                table#api-table tr th:not(:first-child)
                { background: #CCC; vertical-align: middle; }
                table#api-table tr td:not(:first-child){ text-align: right; }
            </style>
            <table cellpadding="5" border="1"
            style="border-collapse: collapse" id="api-table">
                <tr style="font-weight:bold; background: #DDD">
                    <th width="80"></th>
                    <th>Net Productivity %</th>
                    <th>Reopening %</th>
                    <th>Net Productivity</th>
                    <th>Remaining Todo</th>
                    <th>Capacity</th>
                    <th>Net Time Spent Dev</th>
                    <th>Missing Working Hours Dev</th>
                    <th>Tickets closed</th>
                    <th>Tickets reopened</th>
                </tr>
        '''
        rs += self.process_target_kpi_from_sprint()
        rs += self.process_kpi_result_from_sprint(current_sprint_date)
        rs += '</table>'

        return rs

    @api.model
    def get_remaining_time_on_billable(self):
        rs = self._get_kpi_from_sql(
            self.SQL_BILLABLE_AND_NO_QUOTATION_REMAINING_TIME, ())
        return int(math.floor(rs or 0.0))

    @api.model
    def get_trobz_kpi_developer(self, sprint, sprint_next_day):

        kpi_labels = [
            'Developer',
            'Net Productivity',
            'Net Global Productivity Rate',
            'Ticket re-opening rate',
            'Tickets reopened',
            'Tickets closed',
            'Leave Requests (hours)*',
            'Days off (Working Hours)',
            'Leave Request Status*',
            'Working Hours (excluding Days off, compensation)',
            'Contract Working Hours',
            'Compensation (Working Hours)',
        ]

        developers = self.env['res.users'].search(
            [('must_input_working_hour', '=', True)])
        kpi_header = ''
        for kpi in kpi_labels:
            special_info = ''
            if kpi == 'Leave Requests (hours)*':
                special_info = 'title="This number will be wrong ' \
                               'if the Leave Request is overlapping 2 weeks."'

            if kpi == 'Leave Request Status*':
                special_info = 'title="This status will be wrong ' \
                               'if the Leave Request is overlapping 2 weeks."'

            kpi_header += '<td style="border:solid 1px black;" %s>%s</td>' % (
                special_info, kpi)

        kpi_lines = []

        ticket_reopening_env = self.env['forge.ticket.reopening']
        forge_ticket_env = self.env['tms.forge.ticket']

        for developer in developers:
            kpi_results = {
                'Developer': developer.name,
                'Net Productivity': self._get_kpi_from_sql(
                    self.SQL_NET_PRODUCTIVITY,
                    (sprint, 'AND last_completer_id = %s' % developer.id)),
                'Working Hours (excluding Days off, compensation)':
                self._get_kpi_from_sql(
                    self.SQL_NET_TIME_SPENT,
                    (sprint, 'AND twh.user_id=%s' % developer.id)),
                'Tickets reopened': len(
                    ticket_reopening_env.search(
                        [('sprint', '=', sprint),
                         ('last_completer_id', '=', developer.id),
                         ('reopening_type', '=', 'defect')])),
                'Tickets closed': len(forge_ticket_env.search(
                    [('closing_datetime', '>', sprint),
                     ('closing_datetime', '<', sprint_next_day),
                     ('last_completer_id', '=', developer.id)])),
                'Leave Requests (hours)*': self._get_kpi_from_sql(
                    self.SQL_SUM_HOURS_OF_LR_BY_DEV_OVERLAPING_DATES,
                    (developer.id, sprint,
                     sprint_next_day, sprint, sprint_next_day)),
                'Days off (Working Hours)': self._get_kpi_from_sql(
                    self.SQL_SUM_WORKING_HOURS_BY_SPRINT_AND_TYPE_AND_DEV,
                    (sprint, 'Days Off', developer.id)),
                'Compensation (Working Hours)': self._get_kpi_from_sql(
                    self.SQL_SUM_WORKING_HOURS_BY_SPRINT_AND_TYPE_AND_DEV,
                    (sprint, 'Compensation', developer.id)),
                'Contract Working Hours': self._get_kpi_from_sql(
                    self.SQL_SUM_HOURS_WORKING_SCHEDULE_BY_DEV,
                    (developer.id, sprint)),
            }

            kpi_results['Net Global Productivity Rate'] = \
                self._get_rounded_rate(
                    kpi_results['Net Productivity'],
                    kpi_results[
                        'Working Hours (excluding Days off, compensation)'])
            kpi_results['Ticket re-opening rate'] = self._get_rounded_rate(
                kpi_results['Tickets reopened'],
                kpi_results['Tickets reopened'] +
                kpi_results['Tickets closed'])
            kpi_results['Leave Request Status*'] = \
                (kpi_results['Leave Requests (hours)*'] or 0) == (
                    kpi_results['Days off (Working Hours)'] or 0) and \
                'Good' or 'Unbalanced'

            line = ''
            for kpi in kpi_labels:
                special_style = ''
                special_info = ''
                if kpi == 'Leave Request Status*' and kpi_results[
                        kpi] == 'Unbalanced':
                    special_style = 'color:orange;'
                    special_info = 'title="This status will be wrong ' \
                                   'if the Leave Request is overlapping' \
                                   ' 2 weeks."'

                if kpi == 'Compensation (Working Hours)' and kpi_results[
                        kpi] > 0:
                    special_style = 'color:red;'

                line += '<td style="border:solid 1px black;%s" ' \
                        'align="right" %s>%s</td>' % \
                    (special_style, special_info,
                     kpi in kpi_results and kpi_results[kpi] or '0')
            kpi_lines.append(line)

        kpi_lines_tr = ''
        for line in kpi_lines:
            kpi_lines_tr += '''
                <tr>%s</tr>
            ''' % line

        kpi_table = '''
            <table style="border-collapse:collapse;padding:">
                <tr style="font-weight:bold">%s</tr>
                %s
            </table>
        ''' % (kpi_header, kpi_lines_tr)

        return kpi_table

    @api.model
    def get_trobz_kpi_milestone(self, sprint):
        return 'trobz_kpi_milestone: not available yet'

    @api.model
    def get_trobz_kpi_global(self, sprint, sprint_next_day):

        kpi_results = {
            'Sprint': sprint,
            'Net Productivity': self._get_kpi_from_sql(
                self.SQL_NET_PRODUCTIVITY, (sprint, '')),
            'Total time spent (not days off, not compensation, for dev only)':
            self._get_kpi_from_sql(
                self.SQL_NET_TIME_SPENT,
                (sprint,
                 "and hed.name not in ('Management','Functional Consultant')")
            ),
            'Tickets reopened': len(self.env['forge.ticket.reopening'].search(
                [('sprint', '=', sprint),
                 ('reopening_type', '=', 'defect')])),
            'Time Spent on fixing': self._get_kpi_from_sql(
                self.SQL_TIME_SPENT_FIXING, sprint),
            'Average opening time of current opened Very High priority ticket':
            self._get_kpi_from_sql(self.SQL_VERY_HIGH_OPEN_TICKET_AVG_AGE, ()),
            'Total Number of support ticket': len(
                self.env['tms.support.ticket'].search(
                    [('state', '!=', 'closed')])),
            'Number of support ticket to Trobz': len(
                self.env['tms.support.ticket'].search(
                    [('state', '!=', 'closed'),
                     ('owner_id.is_trobz_member', '=', True),
                     ('project_id.state', '=', 'active'),
                     ('priority', '!=', 'minor')])),
            'Average Opening Time (tickets assigned to '
            'Trobz, not low priority)':
            self._get_kpi_from_sql(
                self.SQL_NOT_LOW_PRIORITY_OPEN_TO_TROBZ_TICKET_AVG_AGE, ()),
            'Max Opening Time (urgent priority)': self._get_kpi_from_sql(
                self.SQL_OPEN_TO_TROBZ_TICKET_MAX_AGE_BY_PRIORITY,
                "('urgent')"),
            'Max Opening Time (major or normal priority)':
            self._get_kpi_from_sql(
                self.SQL_OPEN_TO_TROBZ_TICKET_MAX_AGE_BY_PRIORITY,
                "('normal','major')"),

            'Total remaining time in ending sprint': self._get_kpi_from_sql(
                self.SQL_SPRINT_REMAINING_TIME, (sprint)),
            'Total billable and not quotation remaining time':
            self._get_kpi_from_sql(
                self.SQL_BILLABLE_AND_NO_QUOTATION_REMAINING_TIME, ()),
            'Tickets in qa': len(self.env['tms.forge.ticket'].search(
                [('state', '=', 'in_qa')])),
            'Tickets closed': len(self.env['tms.forge.ticket'].search(
                [('closing_datetime', '>', sprint),
                 ('closing_datetime', '<', sprint_next_day)])),
            'Number of tickets:“assigned,WIP”&'
            ' “without estimated”& “not quotation"':
            len(self.env['tms.forge.ticket'].search(
                [('quotation', '=', 'no'),
                 ('state', 'in', ('assigned', 'wip')),
                 ('development_time', 'in', (None, '0', '0.00', '0.01'))])),
            'Max(Tickets code_completed or ready to deploy per project)':
            self._get_kpi_from_sql(self.SQL_MAX_READY_INTEGRATION, ()),
            'Max (Tickets with deployment status '
            'ready_for_staging per project)':
            self._get_kpi_from_sql(self.SQL_MAX_READY_STAGING, ()),
        }

        kpi_results['Net Global Productivity Rate'] = self._get_rounded_rate(
            kpi_results['Net Productivity'],
            kpi_results['Total time spent (not days off,'
                        ' not compensation, for dev only)'])
        kpi_results['Ticket reopening rate'] = self._get_rounded_rate(
            kpi_results['Tickets reopened'],
            kpi_results['Tickets reopened'] +
            kpi_results['Tickets closed'])

        kpi_groups = ['Sprint', 'Development', 'Support', 'Ticket Status']
        kpi_labels = {
            'Sprint': [
                'Sprint',
            ],
            'Development': [
                'Net Productivity',
                'Total time spent (not days off, '
                'not compensation, for dev only)',
                'Net Global Productivity Rate',
                'Ticket reopening rate',
                'Tickets reopened',
                'Time Spent on fixing',
                'Average opening time of '
                'current opened Very High priority ticket',
            ],
            'Support': [
                'Total Number of support ticket',
                'Number of support ticket to Trobz',
                'Average Opening Time (tickets assigned to Trobz,'
                ' not low priority)',
                'Max Opening Time (urgent priority)',
                'Max Opening Time (major or normal priority)'
            ],
            'Ticket Status': [
                'Total remaining time in ending sprint',
                'Total billable remaining time',
                'Tickets in qa',
                'Tickets closed',
                'Number of tickets:“assigned,WIP”& '
                '“without estimated”& “not quotation"',
                'Max(Tickets code_completed or ready to deploy per project)',
                'Max (Tickets with deployment status '
                'ready_for_staging per project)'
            ],
        }

        header_tds = ''
        kpi_tds = ''
        kpi_values_tds = ''
        for group in kpi_groups:
            header_tds += '<td colspan="%s" style="border:solid 1px black;"' \
                          ' align="center">%s</td>' % \
                (len(kpi_labels[group]), group)
            for kpi in kpi_labels[group]:
                kpi_tds += '<td style="border:solid 1px black;">%s</td>' % kpi
                kpi_values_tds += '<td style="border:solid 1px black;"' \
                                  ' align="right">%s</td>' % \
                    (kpi in kpi_results and kpi_results[kpi] or 'na')

        trobz_kpi_global = '''
            <table style="border-collapse:collapse;padding:">
                <tr style="font-weight:bold">%s</tr>
                <tr>%s</tr>
                <tr>%s</tr>
            </table>
        ''' % (header_tds, kpi_tds, kpi_values_tds)

        return trobz_kpi_global
