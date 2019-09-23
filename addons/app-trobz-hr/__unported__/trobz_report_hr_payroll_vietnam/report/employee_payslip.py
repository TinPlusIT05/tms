# -*- coding: utf-8 -*-

from trobz_report_base.report import trobz_report_base
import logging


class Parser(trobz_report_base.Parser):

    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.report_name = 'trobz_report_hr_payroll_vietnam'
        self.common_init(context=context)
        if self.obj_partner and self.obj_partner.id:
            self.use_user_lang = False
            self.obj_model = 'res.partner'
            self.obj_id = self.obj_partner.id
            self.lang_field = 'lang'
        # Language
        self.lang_init(
            self.use_user_lang, self.obj_model, self.obj_id, self.lang_field)
        com_partner_info = self.addr_get(
            partner_id=self.com_partner and self.com_partner.id or False)
        self.payslip = self.get_payslip_info(context)
        lines = self.get_payslip_line()
        self.localcontext.update({
            'com_partner_info': com_partner_info,
            'payslip': self.payslip,
            'lines': lines
        })

    def get_payslip_info(self, context):
        payslip_id = False
        if type(context) != dict:
            return False
        if context.get('active_id', False):
            payslip_id = context['active_id']
        elif context.get('active_ids', False):
            payslip_id = context['active_ids'][0]
        if not payslip_id:
            return False
        payslip = self.pool.get('hr.payslip').read(
            self.cr, self.uid, payslip_id,
            ['employee_id', 'date_from',
             'date_to', 'contract_id', 'number',
             'struct_id', 'name', 'line_ids'], context=context)
        return payslip

    def get_payslip_line(self):
        if not self.payslip['line_ids']:
            return []
        hr_salary_rule_obj = self.pool.get('hr.salary.rule')
        payslip_lines = []
        lines = self.pool.get('hr.payslip.line').read(
            self.cr, self.uid, self.payslip['line_ids'],
            ['salary_rule_id', 'total']
        )
        for payslip_line in lines:
            salary_rule = hr_salary_rule_obj.read(
                self.cr, self.uid, payslip_line['salary_rule_id'][0],
                ['code', 'note', 'amount_python_compute'])
            formula = salary_rule \
                and salary_rule['amount_python_compute'] or ''
            if len(formula) < 9 or formula.find('result = ') != 0:
                logging.error('The formula (amount_python_compute) "%s" \
                    of the salary rule %s should start with \
                    "result = ".' % (formula, salary_rule['code']))
            else:
                formula = formula[9:]
            payslip_line.update({
                'code': salary_rule and salary_rule['code'] or '',
                'note': salary_rule and salary_rule['note'] or '',
                'formula': formula
            })
            payslip_lines.append(payslip_line)
        return payslip_lines

    def dummy_function(self):
        """
        The only purpose of this function is to make the listed terms appear
        in the translation.
        No need to call this function.
        """
        _('PAYSLIP')
        _('From')
        _('To')
        _('Reference')
        _('Employee')
        _('Contract')
        _('Description')
        _('Code')
        _('Name')
        _('Formula')
        _('Total')
        return True
