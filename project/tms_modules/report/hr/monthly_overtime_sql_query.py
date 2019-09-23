from openerp import tools
from openerp import SUPERUSER_ID
from openerp import models, fields, api


class MonthlyOTSqlView(models.Model):
    _name = "monthly.overtime.sqlview"
    _auto = False

    employee_id = fields.Many2one('hr.employee')
    overtime_type_id = fields.Many2one('hr.overtime.type')
    ot_month = fields.Integer(string='Month')
    ot_year = fields.Integer(string='Year')
    duration = fields.Float(string='Working Time')

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'monthly_overtime_sqlview')
        cr.execute("""
            CREATE or REPLACE VIEW monthly_overtime_sqlview as (
                SELECT 
                    ROW_NUMBER() OVER(ORDER BY employee_id) id,
                    employee_id,
                    overtime_type_id,
                    EXTRACT(MONTH FROM date_ot) ot_month,
                    EXTRACT(YEAR FROM date_ot) ot_year,
                    sum(total_wh) duration 
                FROM 
                    hr_input_overtime
                WHERE 
                    state = 'approved'

                GROUP BY employee_id, overtime_type_id, ot_month, ot_year
           )""")
