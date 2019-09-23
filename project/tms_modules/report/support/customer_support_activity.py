#!/usr/bin/env python
# coding: utf8
from openerp.report import report_sxw
from openerp.osv import osv
from datetime import datetime, date
import locale
import logging


class report_support_activity_common(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(report_support_activity_common, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_today': self.get_today,
            'get_format_date': self.get_format_date,
            'get_previous_status_date': self.get_previous_status_date,
            'get_support_tickets': self.get_support_tickets,
            'get_total_workload': self.get_total_workload,
            '_format_workload_number': self._format_workload_number
        })

    # Definition Function
    def get_today(self):
        return date.today()

    def get_suffix_day_en(self, day):
        if day in (11, 12, 13):
            return 'th'
        last = day % 10
        if last == 1:
            return 'st'
        if last == 2:
            return 'nd'
        if last == 3:
            return 'rd'
        return 'th'

    def get_suffix_day_fr(self, day):
        suffix_day = 'e'
        if day == 1:
            suffix_day = 'er'
        return suffix_day

    def get_covert_month_to_french(self, month):
        comp_lst = {
            "January": "janvier",
            'February': "février",
            "March": "mars",
            "April": "avril",
            "May": "mai",
            "June": "juin",
            "July": "juillet",
            "August": "août",
            "September": "septembre",
            "October": "octobre",
            "November": "novembre",
            "December": "décembre"
        }
        res = comp_lst[month]
        return res

    def get_previous_status_date(self, date_input, lang, customer):
        if not date_input:
            sql = """
            SELECT date FROM tms_support_ticket
            Where date is not null and customer_id=%s
            ORDER BY date
            limit 1
            """
            self.cr.execute(sql, (customer.id,))
            res = self.cr.fetchone()
            date_input = res and res[0] or False
        date_input = datetime.strptime(date_input, '%Y-%m-%d')
        previous_status_date = self.get_format_date(date_input, lang)

        return previous_status_date

    def get_format_date(self, date_input, lang):
        frm_date = False
        if date_input:
            day = date_input.day
            if lang != 'fr_FR':
                suffix_day = self.get_suffix_day_en(day)
                frm_date = str(day) + suffix_day + ' of ' + \
                    date_input.strftime('%B %Y')
            else:
                month = date_input.strftime('%B')
                year = date_input.year
                # TODO: use standard python function to convert Date into
                # strings with proper lang formating
                frm_date = str(day) + ' ' + \
                    self.get_covert_month_to_french(month) + " " + str(year)
        return frm_date

    def get_support_tickets(self, params, activity_type):
        customer_id = params['customer_id'][0]
        act_pool = self.pool['tms.activity']
        anal_secondaxis_pool = self.pool['analytic.secondaxis']
        support_ticket_pool = self.pool['tms.support.ticket']
        anal_secondaxis_ids = False
        if activity_type == 'Other':
            anal_secondaxis_ids = anal_secondaxis_pool.search(
                self.cr, self.uid,
                [('name', 'not in', ['Consulting', 'Evolution'])])
        else:
            anal_secondaxis_ids = anal_secondaxis_pool.search(
                self.cr, self.uid,
                [('name', '=', activity_type)])

        tms_activity_ids = act_pool.search(
            self.cr, self.uid, [('analytic_secondaxis_id',
                                 'in',
                                 anal_secondaxis_ids)])
        support_ticket_ids = support_ticket_pool.search(
            self.cr, self.uid,
            [('customer_id', '=', customer_id),
             ('date', '=', False),
                ('quotation_approved', '=', True),
                ('tms_activity_id', 'in', tms_activity_ids)],
            order='id asc')
        return support_ticket_pool.browse(
            self.cr, self.uid, support_ticket_ids)

    def get_total_workload(self, params, ticket_type):
        total_workload = 0
        tst_obj = self.get_support_tickets(params, ticket_type) or False
        if tst_obj:
            for line in tst_obj:
                total_workload += float(line.workload_char)
        return total_workload

    # TODO: use trobz_report_base functions to format number
    def _format_workload_number(self, number_unicode, digits=2, separator=',',
                                dec='.'):
        number = float(number_unicode)
        default_locale = 'en_US.UTF-8'
        config_param = 'Locale used for reports'
        try:
            sql = '''
                    SELECT value
                    FROM ir_config_parameter
                    WHERE key = %s
                '''
            self.cr.execute(sql, (config_param,))
            if self.cr.rowcount:
                default_locale = self.cr.fetchone()[0] or ''
                default_locale = str(default_locale)
                locale.setlocale(locale.LC_ALL, default_locale)
            else:
                logging.warn(
                    'Cannot find config parameter "%s". '
                    'Using "%s" as locale for reports.' % (
                        config_param, default_locale))
        except Exception, e:
            default_locale = 'en_US.UTF-8'
            logging.error(
                "Error when trying to set locale using value of \
                config parameter '%s': %s.\nUsing '%s' as locale \
                for reports. To see all supported locales of the \
                system, run this command in Terminal: locale -a"
                % (config_param, str(e), default_locale))
        locale.setlocale(locale.LC_ALL, default_locale)
        res = locale.format('%.' + str(digits) + 'f', number, 1)
        parts = res.split('.')
        parts[0] = parts[0].replace(',', separator)
        res = dec.join(parts)
        return res


class customer_support_activity(osv.AbstractModel):
    _name = 'report.tms_modules.report_customer_support_activity_template'
    _inherit = 'report.abstract_report'
    _template = 'tms_modules.report_customer_support_activity_template'
    _wrapped_report_class = report_support_activity_common


class customer_support_activity_html(osv.AbstractModel):
    _name = 'report.tms_modules.report_customer_support_activity_template_html'
    _inherit = 'report.abstract_report'
    _template = 'tms_modules.report_customer_support_activity_template'
    _wrapped_report_class = report_support_activity_common
