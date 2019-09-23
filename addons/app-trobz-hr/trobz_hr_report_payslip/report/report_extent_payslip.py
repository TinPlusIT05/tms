from openerp.osv import osv
from openerp.report import report_sxw
from datetime import datetime, timedelta
from babel.numbers import format_number


class report_extent_payslip_print(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(report_extent_payslip_print, self).__init__(cr, uid, name,
                                                          context=context)
        self.localcontext.update({
            'get_company_address': self._get_company_address,
            'get_employee_address': self._get_employee_address,
            'get_line_categs': self._get_line_categs,
            'get_line_details': self._get_line_details,
            'get_annual_leaves': self._get_annual_leaves,
            'get_net_income_to_pay': self._get_net_income_to_pay,
            'get_format_number': self._get_format_number,
        })

    def _get_format_number(self, number):
        if type(number) == type(''):
            return number
        return format_number(number, locale='en_US')

    def _get_line_categs(self, payslip_id):
        '''
        Return Payslip Line Categories of the current payslip
        '''
        res = []
        sql = '''
        select pg.name, pg.code, pg.id 
        from hr_payslip_line as pl
        join hr_salary_rule_category as pg on pl.category_id = pg.id
        where pl.slip_id = %s and pg.code != 'NET' and
        exists (select 1 from hr_payslip_line where category_id = pg.id
        and appears_on_payslip = 't')
        order by pl.sequence;
        ''' % payslip_id
        self.cr.execute(sql)
        for x in self.cr.fetchall():
            res.append(x)
        return list(set(res))

    def _get_line_details(self, payslip_id, category_id):
        '''
        Return Payslip Line defails of the current category rule
        '''
        res = []
        payslip_line_pool = self.pool['hr.payslip.line']
        line_ids = payslip_line_pool.search(
            self.cr, self.uid, [('slip_id', '=', payslip_id),
                                ('category_id', '=', category_id),
                                ('appears_on_payslip', '=', True)])
        lines = payslip_line_pool.browse(self.cr, self.uid, line_ids)
        for line in lines:
            res.append(
                (line.code, line.name, line.amount,
                 float(line.quantity) / line.rate * 100, line.total)
            )
        return res

    def compute_allo_days(self, cr, uid, employee_id, hol_status_ids,
                          date_from=False, date_to=False):
        """
        Calculate the allocation request which was approved
        """
        if not hol_status_ids:
            return 0
        sql = """
        SELECT
            CASE
                WHEN SUM(h.number_of_days) > 0 THEN SUM(h.number_of_days)
                ELSE 0
            END as allo_days
            FROM
                hr_holidays h
                join hr_holidays_status s on (s.id=h.holiday_status_id)
            WHERE
                h.type='add' AND
                h.state='validate' AND
                s.limit=False AND
                h.employee_id = %s AND
                h.holiday_status_id in (%s)
        """ % (employee_id, ','.join(map(str, hol_status_ids)),)
        if date_from and date_to:
            sql += """ AND h.allo_date >= '%s'
                       AND h.time_of_allocation_date <= '%s'
                       """ % (date_from, date_to)
        elif not date_from and date_to:
            sql += " AND h.allo_date <= '%s'" % (date_to)
        elif date_from and not date_to:
            sql += " AND h.allo_date >= '%s'" % (date_from)
        cr.execute(sql)
        res = cr.fetchone()
        return res and res[0] or 0

    def compute_leave_days(self, cr, uid, employee_id, hol_status_ids,
                           date_from=False, date_to=False):
        """
        Calculate the number of leave days in the indicated period of time
        """

        if not hol_status_ids:
            return 0
        condition = """
            FROM
                hr_holidays h
                join hr_holidays_line hl on (h.id=hl.holiday_id)
            WHERE
                h.type='remove' AND
                h.state='validate' AND
                h.employee_id = %s AND
                hl.holiday_status_id in (%s)
            """ % (employee_id, ','.join(map(str, hol_status_ids)))

        sql = "SELECT sum(hl.number_of_days)" + condition
        other_sql = """SELECT hl.first_date, hl.last_date, hl.first_date_type,
                        hl.last_date_type""" + condition
        line_obj = self.pool['hr.holidays.line']
        contract_obj = self.pool['hr.contract']

        if date_from and date_to:
            # first date > date from and last date < date to
            sql += """AND hl.last_date < '%s'
                      AND hl.first_date > '%s'""" % (date_to, date_from)
            cr.execute(sql)
            res = cr.fetchone()
            # first date <= date from and last date >= date from
            # OR first date <= date to and last date >= date to
            other_sql += """
            AND (( hl.first_date <= '%s' AND hl.last_date >= '%s')
            OR (hl.first_date <= '%s' AND hl.last_date >= '%s')
            )
            """ % (date_from, date_from, date_to, date_to)
            cr.execute(other_sql)
            other_res = cr.fetchall()

        elif not date_from and date_to:
            # NOT date from and last date < date to
            sql += "AND hl.last_date < '%s'" % (date_to)
            cr.execute(sql)
            res = cr.fetchone()

            # OR first date <= date to and last date >= date to
            other_sql += """AND (hl.first_date <= '%s'
                            AND hl.last_date >= '%s')""" % (date_to, date_to)
            cr.execute(other_sql)
            other_res = cr.fetchall()

        elif date_from and not date_to:
            # first date > date from and NOT date to
            sql += "AND hl.first_date > '%s'" % (date_from)
            cr.execute(sql)
            res = cr.fetchone()

            # first date <= date from and last date >= date from
            other_sql += """AND ( hl.first_date <= '%s'
                            AND hl.last_date >= '%s')
                            """ % (date_from, date_from)
            cr.execute(other_sql)
            other_res = cr.fetchall()
        else:
            cr.execute(sql)
            res = cr.fetchone()
            return res and res[0] or 0

        """Calculate number of days"""
        number_of_days = res and res[0] or 0
        employee = self.pool['hr.employee'].browse(cr, uid, employee_id)

        company = employee.company_id
        country_id = False
        if company and company.country_id:
            country_id = company.country_id.id

        for line in other_res:
            str_start_date = date_from and max(line[0], date_from) or line[0]
            start_date = datetime.strptime(str_start_date, DF).date()
            str_date_end = date_to and min(line[1], date_to) or line[1]
            end_date = datetime.strptime(str_date_end, DF).date()
            # Get the valid contract in (start_date, end_date)
            # Get the latest valid contract
            # Get the working schedule of this contract
            working_hours = False
            contract_ids = contract_obj.get_contract(
                cr, uid, employee.id, start_date, end_date)
            if contract_ids:
                contract = contract_obj.browse(cr, uid, contract_ids[-1])
                if contract.working_hours:
                    working_hours = contract.working_hours.id

            while start_date <= end_date:
                dayofweek = start_date.weekday()
                date_type = 'full'
                if start_date == datetime.strptime(line[0], '%Y-%m-%d').date():
                    date_type = line[2]
                if start_date == datetime.strptime(line[1], '%Y-%m-%d').date():
                    date_type = line[3]
                number_of_days += line_obj.plus_day(cr, uid, working_hours,
                                                    start_date, dayofweek,
                                                    date_type, country_id)
                start_date = start_date + timedelta(1)
        return number_of_days

    def _get_annual_leaves(self, employee_id, payslip):
        '''
        Return leaves of the Employee
        - Paid leaves available
        - Paid leaves taking during the period
        - Remaining leaves
        '''
        cr = self.cr
        uid = self.uid
        hol_status_obj = self.pool['hr.holidays.status']
        hol_status_ids = hol_status_obj.search(
            cr, uid, [('payment_type', '=', 'paid')])
        leaves_available = self.compute_allo_days(
            cr, uid, employee_id, hol_status_ids,
            date_from=False, date_to=False)
        leaves_taken = self.compute_leave_days(
            cr, uid, employee_id, hol_status_ids,
            date_from=payslip.date_from, date_to=payslip.date_to)
        remaining_leaves = leaves_available - leaves_taken
        return [leaves_available, leaves_taken, remaining_leaves]

    def _get_net_income_to_pay(self, payslip_id):
        '''
        Return Net Income to Pay
        '''
        res = 0
        payslip_line_pool = self.pool['hr.payslip.line']
        line_ids = payslip_line_pool.search(
            self.cr, self.uid, [('slip_id', '=', payslip_id),
                                ('code', '=', 'NetInc')])
        if not line_ids:
            return 0
        line = payslip_line_pool.browse(self.cr, self.uid, line_ids[0])
        res = line.total
        return res

    def _get_company_address(self, company_obj):
        res = []
        if company_obj.street:
            res.append(company_obj.street)
        if company_obj.street2:
            res.append(company_obj.street2)
        if company_obj.city:
            res.append(company_obj.city)
        if company_obj.country_id:
            res.append(company_obj.country_id.name)
        res = ", ".join(res)
        return res

    def _get_employee_address(self, employee_obj):
        res = [employee_obj.name.upper()]
        address = employee_obj.address_home_id
        if address:
            res.append(address.street)
            res.append(address.street2)
            res.append(address.city)
            res.append(address.country_id.name)
        else:
            res += ['', '', '', '']
        return res


class report_extent_payslip_abstract(osv.AbstractModel):
    # _name must be "report." + "module name" + "report xml template id"
    _name = 'report.trobz_hr_report_payslip.report_extent_payslip_template'
    _inherit = 'report.abstract_report'
    _template = 'trobz_hr_report_payslip.report_extent_payslip_template'
    _wrapped_report_class = report_extent_payslip_print
