# -*- encoding: utf-8 -*-
from openerp.osv import osv

class hr_working_activity(osv.osv):
    _inherit = 'hr.working.activity'
    
    def update_xml_id_hr_working_activity(self, cr, uid, context=None):
        """
        Update XML ID of working activity data
        We moved this category from trobz_hr_payroll_working_hour to trobz_hr_payroll_working_hour_vn
        """
        sql = """
            UPDATE ir_model_data
            SET module = 'trobz_hr_payroll_working_hour_vn',
                write_date = NOW() AT TIME ZONE 'UTC',
                date_update = NOW() AT TIME ZONE 'UTC'
            WHERE 
                model = 'hr.working.activity'
                AND module = 'trobz_hr_payroll_working_hour';
        """
        cr.execute(sql)
        return True