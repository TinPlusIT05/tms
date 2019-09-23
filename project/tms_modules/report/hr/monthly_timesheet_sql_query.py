from openerp import tools
from openerp import models, fields


class MonthlyTimesheetSqlView(models.Model):
    _name = "monthly.timesheet.sqlview"
    _auto = False

    employee_id = fields.Many2one('hr.employee')
    date = fields.Date()
    day = fields.Integer(string='Day')
    month = fields.Integer(string='Month')
    year = fields.Integer(string='Year')
    working_time = fields.Float(string='Working Time')

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'monthly_timesheet_sqlview')
        cr.execute("""
            CREATE or REPLACE VIEW monthly_timesheet_sqlview as (
                SELECT
                    ROW_NUMBER() OVER(ORDER BY tb.employee_id) id,
                    tb.employee_id,
                    wk.date,
                    "day",
                    sum(duration_hour) AS working_time,
                    EXTRACT(MONTH FROM date) "month",
                    EXTRACT(YEAR FROM date) "year"

                FROM (
                    SELECT
                        ru.id, ru.employee_id, rs.name
                    FROM
                        res_users ru INNER JOIN resource_resource rs
                            ON rs.user_id = ru.id
                    WHERE
                        ru.must_input_working_hour = TRUE and
                        rs.active = TRUE
                    ) tb INNER JOIN tms_working_hour wk
                        ON tb.employee_id = wk.employee_id
                WHERE
                    wk.name != 'Days Off'
                GROUP BY
                    tb.employee_id, date, day, month, year
                ORDER BY
                    tb.employee_id, date
           )""")
