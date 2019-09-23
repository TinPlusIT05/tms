# -*- coding: utf-8 -*-

from openerp.osv import osv
#from datetime import datetime,timedelta
from openerp.tools.translate import _

class hr_payslip(osv.osv):
    _inherit = 'hr.payslip'
    
    def get_worked_day_lines(self, cr, uid, contract_ids, date_from, date_to, context=None):
        """ 
        Override Fnct
        Get the salary input from the working hours
            - Expected working days in Month (Month): Base on calendar and the expected working days were calculated after create/update payroll working hours. 
            - Expected working days in Month (Contract): Get the Expected Working Days the set on the advanced working plan template of contract.
            - Minimal flexible days: Get the Minimal Days the set on the advanced working plan template of contract.
            - Payroll working hours group by working activity and flexible days
           
        """
        result = []
        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            if not contract.working_hours:
                #fill only if the contract as a working schedule linked
                continue
            
            worked_days = []
            flex_worked_days = []
            
            #Expected working days
            sql = """
            SELECT days, month_year
            FROM hr_expected_working_day
            WHERE from_date >= '%s'
            AND to_date <= '%s'
            AND contract_id = %s"""%(date_from, date_to, contract.id)
            cr.execute(sql)
            for ex_days in cr.fetchall():
                line_data = {
                             'name': _('Expected Working Days In Month %s'%ex_days[1]),
                             'sequence': 0,
                             'code': 'ExWorkingMonth',
                             'number_of_days': ex_days[0] or 0,
                             'number_of_hours': ex_days[0] * 8,
                             'contract_id': contract.id,
                             }
                worked_days.append(line_data)
            
            #Get from contract: Minimal Flexible Days, Expected Woking Days  
            worked_days += [{
                             'name': _('Expected Working Days In Month (Contract)'),
                             'sequence': 1,
                             'code': 'ExWorkingContract',
                             'number_of_days': contract.working_hours.expected_working_days,
                             'number_of_hours': contract.working_hours.expected_working_days * 8,
                             'contract_id': contract.id,
                            },
                            ]
            if contract.working_hours.min_flexible_days > 0:
                worked_days += [
                            {
                             'name': _('Minimal Flexible Days'),
                             'sequence': 2,
                             'code': 'MinFlex',
                             'number_of_days': contract.working_hours.min_flexible_days,
                             'number_of_hours': contract.working_hours.min_flexible_days * 8,
                             'contract_id': contract.id,
                            }]
            
            #Get from the payroll working hours group by working activity and flexible day
            cr.execute("""SELECT SUM(COALESCE(working_hour,0)), COUNT(date), wa.name, wa.code, wa.sequence, wh.is_flexible
                               FROM hr_payroll_working_hour wh
                                   LEFT JOIN hr_working_activity wa
                                       ON wa.id = wh.activity_id
                               WHERE employee_id = %s 
                                   AND contract_id = %s
                                   AND date >= '%s'
                                   AND date <= '%s'
                                   AND state = 'approve'
                               GROUP BY wa.name, wa.code, wa.sequence, wh.is_flexible
                               ORDER BY wa.sequence
                        """%(contract.employee_id.id, contract.id, date_from, date_to))
            
            for hours, days, ac_name, ac_code, sequence, is_flexible in cr.fetchall():
                line_data = {
                             'name': _(ac_name),
                             'sequence': sequence,
                             'code': ac_code,
                             'number_of_days': round(days,2) or 0,
                             'number_of_hours': round(hours,2) or 0,
                             'contract_id': contract.id,
                             }
                if is_flexible:
                    line_data.update({'name': _(ac_name + ' (Flexible days)'),
                                      'code': 'Flex'+ac_code,
                                      'sequence': line_data['sequence'] + 10})
                worked_days.append(line_data)
            
            result += worked_days + flex_worked_days
        return result

hr_payslip()
