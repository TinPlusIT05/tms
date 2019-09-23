# -*- coding: utf-8 -*-

from openerp.report import report_sxw
from openerp import pooler
from openerp.osv import osv
from openerp.tools.translate import _
from datetime import datetime
from openerp.tools.safe_eval import safe_eval
import pytz
import logging
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class Parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        # Initialize common variables
        self.trobz_base = pooler.get_pool(self.cr.dbname).get('trobz.base')
        self.user_obj = pooler.get_pool(self.cr.dbname).get('res.users')
        self.partner_obj = pooler.get_pool(self.cr.dbname).get('res.partner')
        self.company_obj = pooler.get_pool(self.cr.dbname).get('res.company')
        self.currency_obj = pooler.get_pool(self.cr.dbname).get('res.currency')
        self.user_partner = False  # Partner of current user
        # Partner (customer or supplier) of the active object (sale order,
        # invoice, ...)
        self.obj_partner = False
        # Partner of the company of the active object (sale order, invoice,
        # ...)
        self.com_partner = False
        self.next_number = 0
        self.context = context
        self.amount_converted = False
        # Language control
        self.use_user_lang = True
        self.obj_model = False
        self.obj_id = False
        self.lang_field = False
        self.report_name = ''
        self.dual_language = False
        self.primary_lang = False
        self.secondary_lang = False

        self.localcontext.update({
            'dual_language': self.dual_language,
            't': self.t,
            'next_number': self.get_next_number,
            'set_next_number': self.set_next_number,
            'yy': self.yy,
            'to_text': self.to_text,
            'convert_amount': self.convert_amount,
            'get_amount_converted': self.get_amount_converted,
            'addr_get': self.addr_get,
            'bank_get': self.bank_get,
            'get_company_name': self.get_company_name,
            'get_logo': self.get_logo,
            'get_date_printed': self.get_date_printed,
            'get_date_printed_tz': self.get_date_print_tz,
            'get_user_printed': self.get_user_printed,
            'get_user_criteria': self.get_user_criteria,
            'logo_size': self.logo_size,
            'get_company': self.get_company,
            'get_date': self.get_date,
        })

    def get_object_partner_company_info(self, partner_field='partner_id', company_field='company_id', context=None):
        """
        Use this function only for objects that have company_id, partner_id.
        """
        if not context.get('active_model', False)\
                or not context.get('active_ids', False):
            return True
        active_obj = pooler.get_pool(self.cr.dbname).get(context['active_model']).read(self.cr, self.uid, context['active_ids'][0],
                                                                                       [company_field, partner_field], context=context)
        # TODO: Take into account the contacts of this partner.
        if active_obj.get(partner_field, False):
            self.obj_partner = self.partner_obj.browse(self.cr, self.uid, active_obj[partner_field][0],
                                                       fields_process=['name', 'street', 'street2', 'city', 'country_id', 'phone',
                                                                       'fax', 'email', 'bank_ids', 'vat', 'company_id'])
        company_info = self.company_obj.read(
            self.cr, self.uid, active_obj[company_field][0], ['partner_id'], context=context)
        if company_info and company_info['partner_id']:
            self.com_partner = self.partner_obj.browse(self.cr, self.uid, company_info['partner_id'][0],
                                                       fields_process=['name', 'street', 'street2', 'city', 'country_id', 'phone',
                                                                       'fax', 'email', 'bank_ids', 'vat', 'company_id'])
        return True

    def get_user_partner_company_info(self, context=None):
        """
        Get the partner and company info of current user.
        """
        # Prepare the partner information to get address information, bank
        # accounts information.
        partner_id = self.user_obj.get_company_partner_id(self.cr, self.uid)
        self.user_partner = self.partner_obj.browse(self.cr, self.uid, partner_id,
                                                    fields_process=['name', 'street', 'street2', 'city', 'country_id', 'phone',
                                                                    'fax', 'email', 'bank_ids', 'company_id'])
        return True

    def common_init(self, partner_field='partner_id', company_field='company_id', context=None):
        """
        Initialize common objects used in reports: Main company, main partner.
        """
        self.get_object_partner_company_info(
            partner_field=partner_field, company_field=company_field, context=context)
        # User reported
        self.reported_user = self.user_obj.read(
            self.cr, self.uid, self.uid, ['name'], context=context)
        self.reported_user = self.reported_user['name']
        return True

    def set_lang(self, lang):
        self.context['lang'] = lang
        self.localcontext['lang'] = lang
        return True

    def logo_size(self):
        """
        Get image logo size from paramater
        """
        report_logo_size = safe_eval(self.pool.get('ir.config_parameter').get_param(self.cr, self.uid,
                                                                                    'report_logo_size',
                                                                                    'False'))
        return report_logo_size

    def lang_init(self, use_user_lang=True, obj_model=False, obj_id=False, lang_field=False):
        """
        dual_lang, primary_lang, secondary_lang
        """
        report_languages = safe_eval(self.pool.get('ir.config_parameter').get_param(self.cr, self.uid,
                                                                                    'report_languages',
                                                                                    'False'))
        report_lang = report_languages and report_languages.get(
            self.report_name, False) or False
        if not report_lang:
            report_lang = {
                'primary_lang': False
            }

        # Process the Primary Language to be displayed in the report
        if report_lang.get('primary_lang', False):
            self.primary_lang = report_lang['primary_lang']
        elif not use_user_lang:
            if not obj_model:
                obj_model = self.context.get('active_model', False)
            if not obj_id:
                obj_id = self.context.get('active_id', False)
            if not lang_field:
                lang_field = 'lang'  # special field
            if obj_model and obj_id and lang_field:
                try:
                    self.primary_lang = self.pool.get(obj_model).read(
                        self.cr, self.uid, obj_id, [lang_field], context=self.context)[lang_field]
                except:
                    logging.warning("Cannot get field '%s' of the object %s (%s)" % (
                        lang_field, str(obj_id), obj_model))
        if not self.primary_lang:
            self.primary_lang = self.localcontext.get(
                'lang', self.context.get('lang', 'en_US'))  # current user's language
        self.set_lang(self.primary_lang)

        # Dual Language control
        if report_lang.get('dual_lang', False):
            self.dual_language = True
        # Secondary Language (be only displayed when dual_lang is True)
        # The default is en_US  due to all Trobz report templates are written
        # in English
        self.secondary_lang = report_lang.get('secondary_lang', 'en_US')
        if self.primary_lang == self.secondary_lang:
            self.dual_language = False
        return report_lang

    def _translate(self, source_string, name=None):
        """
        Customize translation in aeroo report:
        - In the right way report translation, we shoud define the type is 'report' in po file: 
            e.g:
                #: report:sale.order:0
                msgid "Offer"
                msgstr "Offerte"
        - but we used the type is 'python code' for a long time
          To keep backward compatibility with old report, 
          In _get_source function:
              + use type ('code','model','report')
              + use 'name' paramater if you need to specific where the source_string comes from ?
        """
        lang = self.localcontext['lang']
        transl_obj = self.pool.get('ir.translation')
        translated_string = source_string
        if lang and source_string:
            # note:
            # In report, we use the type in ('code','model','report')
            translated_string = transl_obj._get_source(
                self.cr, 1, name, ('code', 'model', 'report'), lang, source_string)
        return translated_string

    def t(self, keyword, name=None):
        """
        Translate words into current user's language.
        If dual_language is True, the words will be translated into this form "User's language word (word in English)".
        """
        # Dual Language displayed in report
        if self.dual_language:
            return_keyword = self._translate(keyword, name)
            # If no specific secondary language is indicated, simply display
            # the keyword as inputed
            if not self.secondary_lang:
                return return_keyword + ' (' + str(keyword) + ')'
            # Translate the inputed keyword into desired secondary language
            self.set_lang(self.secondary_lang)
            return_keyword += ' (' + self._translate(keyword, name) + ')'
            self.set_lang(self.primary_lang)
            return return_keyword
        return self._translate(keyword, name)

    def yy(self, date):
        """
        Get the year of given date without century as a decimal number [00, 99].
        """
        if not date:
            return '--'
        d = datetime.strptime(date, '%Y-%m-%d')
        yy = d.strftime('%y')
        return yy

    def get_next_number(self):
        """
        Number the lines in report.
        """
        self.next_number += 1
        return self.next_number

    def set_next_number(self, value, print_value=True):
        """
        Set next number to a desired value.
        """
        self.next_number = value

        # if no need to print new value
        if not print_value:
            return

        return self.next_number

    def to_text(self, amount, currency='VND'):
        """
        Convert an amount to words based on the lang and currency.
        """
        if self.dual_language:
            return '%s (%s)' % (self.trobz_base.amount_to_text(int(amount), self.primary_lang, currency),
                                self.trobz_base.amount_to_text(int(amount), self.secondary_lang, currency))
        return self.trobz_base.amount_to_text(int(amount), self.primary_lang, currency)

    def convert_amount(self, date, amount, from_currency_id, to_currency_id=None):
        """
        Convert an amount between two currencies.
        """
        if not to_currency_id:
            # Get VND id
            to_currency_id = self.get_currency_id('VND')
        context = {'date': date}
        self.amount_converted = self.currency_obj.compute(
            self.cr, self.uid, from_currency_id, to_currency_id, amount, context=context)
        self.amount_converted = self.currency_obj.round(
            self.cr, self.uid, amount=self.amount_converted, currency=to_currency_id)
        return self.amount_converted

    def get_amount_converted(self, amount):
        """
        Get the result just returned by convert_amount function.
        """
        if self.amount_converted and isinstance(self.amount_converted, (int, float)):
            return self.amount_converted
        return amount

    def get_currency_id(self, name):
        """
        Get id of a currency from its name.
        """
        currency_ids = self.currency_obj.search(
            self.cr, self.uid, [('name', '=', name)])
        if not currency_ids:
            raise osv.except_osv(
                _('Error!'), _('Cannot find %s currency!' % name))
        return currency_ids[0]

    def get_exchange_rate(self, date, from_currency_id, to_currency_id=None):
        """
        Get the exchange rate from from_currency to to_currency.
        """
        if not to_currency_id:
            to_currency_id = self.get_currency_id('VND')
        context = {'date': date}
        rate = self.currency_obj._get_conversion_rate(
            self.cr, self.uid, from_currency_id, to_currency_id, context=context)
        # Round up to 6 digits after the decimal point (see the definition of
        # the rate column in res_currency)
        return round(rate, 6)

    def addr_get(self, partner_id, address_type='default'):
        """
        Get the address information of a partner.
        """
        result = {
            'name': '',
            'street': '',
            'street2': '',
            'city': '',
            'country_id': '',
            'phone': '',
            'fax': '',
            'email': '',
            'address': ''
        }
        if not partner_id:
            return result
        if self.com_partner and partner_id == self.com_partner.id:
            partner_info = self.com_partner
        elif self.obj_partner and partner_id == self.obj_partner.id:
            partner_info = self.obj_partner
        elif self.user_partner and partner_id == self.user_partner.id:
            partner_info = self.user_partner
        else:
            partner_info = self.partner_obj.browse(self.cr, self.uid, partner_id,
                                                   fields_process=['name', 'street', 'street2', 'city', 'state_id',
                                                                   'country_id', 'phone', 'fax', 'email', 'child_ids'])
        result = {
            'name': '',
            'street': '',
            'street2': '',
            'city': '',
            'country_id': '',
            'phone': '',
            'fax': '',
            'email': '',
            'address': ''
        }
        if not partner_info:
            return result
        if not partner_info.street and not partner_info.street2 \
                and not partner_info.city and not partner_info.country_id  \
                and not partner_info.phone and not partner_info.fax \
                and not partner_info.email:
            # find address_type or first contact of partner
            contacts = partner_info.child_ids
            if contacts:
                partner_info = ''
                for contact in contacts:
                    if contact.type == address_type:
                        partner_info = contact
                        break
                if not partner_info:
                    partner_info = contacts[0]

        if partner_info:
            result['name'] = partner_info.name
            result['street'] = partner_info.street
            result['street2'] = partner_info.street2
            result['zip'] = partner_info.zip
            # partner_info.state_id and partner_info.state_id.name
            result['city'] = partner_info.city
            result[
                'country_id'] = partner_info.country_id and partner_info.country_id.name or ''
            result['phone'] = partner_info.phone
            result['fax'] = partner_info.fax
            result['email'] = partner_info.email
            result['address'] = self._addr_get_str(result)
        return result

    def _addr_get_str(self, address_info):
        """
        Return address information as a whole string.
        """
        if not address_info:
            return ''
        addr_str = ''
        if address_info['street']:
            addr_str += address_info['street'] + "\r\n"
        if address_info['street2']:
            addr_str += address_info['street2'] + "\r\n"
        # City and Country are on same line
        if address_info['zip']:
            addr_str += address_info['zip'] + ' '
        if address_info['city']:
            addr_str += address_info['city']
            if address_info['country_id']:
                addr_str += ' - '
            else:
                addr_str += "\r\n"
        if address_info['country_id']:
            addr_str += address_info['country_id'] + "\r\n"
        # Phone and Fax are on same line
        if address_info['phone']:
            addr_str += self.t('Phone') + ': ' + address_info['phone']
            if address_info['fax']:
                addr_str += '  '
            else:
                addr_str += "\r\n"
        if address_info['fax']:
            addr_str += self.t('Fax') + ': ' + address_info['fax'] + "\r\n"
        if address_info['email']:
            addr_str += self.t('Email') + ': ' + address_info['email']
        return addr_str

    def bank_get(self, partner_id, index=-1):
        """
        Get bank information of a partner.
        """
        if not partner_id:
            raise osv.except_osv(_('Error'), _('No partner defined!'))
        if self.com_partner and partner_id == self.com_partner.id:
            partner_info = self.com_partner
        elif self.obj_partner and partner_id == self.obj_partner.id:
            partner_info = self.obj_partner
        elif self.user_partner and partner_id == self.user_partner.id:
            partner_info = self.user_partner
        else:
            partner_info = self.partner_obj.browse(
                self.cr, self.uid, partner_id, fields_process=['bank_ids'])
        result = {
            'name': '',
            'street': '',
            'street2': '',
            'city': '',
            'country': '',
            'bic': '',
            'bank_owner': '',
            'account_number': '',
            'owner_street': '',
            'owner_city': '',
            'owner_country': '',
            'bank_addr': '',
            'owner_addr': ''
        }
        if not partner_info.bank_ids:
            return result
        if index < 0:
            index = 0
        elif index > len(partner_info.bank_ids):
            index = len(partner_info.bank_ids) - 1
        bank_acc = partner_info.bank_ids[0]
        result['name'] = bank_acc.bank_name or (
            bank_acc.bank and bank_acc.bank.name)
        result['street'] = bank_acc.bank.street
        result['street2'] = bank_acc.bank.street2
        result['city'] = bank_acc.bank.city
        result[
            'country'] = bank_acc.bank.country and bank_acc.bank.country.name or ''
        result['bic'] = bank_acc.bank.bic
        result[
            'bank_owner'] = bank_acc.partner_id and bank_acc.partner_id.name or ''
        result['account_number'] = bank_acc.acc_number or ''
        result['owner_street'] = bank_acc.street
        result['owner_city'] = bank_acc.city
        result[
            'owner_country'] = bank_acc.country_id and bank_acc.country_id.name or ''
        result['bank_addr'] = self._bank_get_addr(result)
        result['owner_addr'] = self._bank_get_addr({
            'street': result['owner_street'],
            'city': result['owner_city'],
            'country': result['owner_country'],
            'street2': '',
            'bic': ''
        })
        return result

    def _bank_get_addr(self, bank_info):
        """
        Get the address information of a partner's bank as a whole string.
        """
        if not bank_info:
            return ''
        addr_str = ''
        if bank_info.get('name'):
            addr_str += bank_info['name'] + '\r\n'
        if bank_info['street']:
            addr_str += bank_info['street'] + '\r\n'
        if bank_info['street2']:
            addr_str += bank_info['street2'] + '\r\n'
        if bank_info['city']:
            addr_str += bank_info['city']
            if bank_info['country']:
                addr_str += ' - '
            else:
                addr_str += '\r\n'
        if bank_info['country']:
            addr_str += bank_info['country'] + '\r\n'
        if bank_info.get('bic', False):
            addr_str += self.t('Swift') + ': ' + bank_info['bic']
        # remove enter line
        if addr_str[-2:] == '\r\n':
            addr_str = addr_str[:-2]
        return addr_str

    def get_company_name(self, company_id):
        """
        Get name of given company.
        """
        if not company_id:
            return self.localcontext.get('company', False) and self.localcontext['company'].name or ''
        if self.com_partner and company_id == self.com_partner.company_id.id:
            company_info = self.com_partner.company_id
        elif self.obj_partner and company_id == self.obj_partner.company_id.id:
            company_info = self.obj_partner.company_id
        elif self.user_partner and company_id == self.user_partner.company_id.id:
            company_info = self.user_partner.company_id
        else:
            company_info = self.company_obj.browse(
                self.cr, self.uid, company_id, fields_process=['name'])
        return company_info.name or ''

    def get_logo(self, company_id):
        """
        Get logo of given company.
        """
        if not company_id:
            return self.localcontext.get('logo', False)
        if self.com_partner and company_id == self.com_partner.company_id.id:
            company_info = self.com_partner.company_id
        elif self.obj_partner and company_id == self.obj_partner.company_id.id:
            company_info = self.obj_partner.company_id
        elif self.user_partner and company_id == self.user_partner.company_id.id:
            company_info = self.user_partner.company_id
        else:
            company_info = self.company_obj.browse(
                self.cr, self.uid, company_id, fields_process=['logo'])
        return company_info.logo or False

    def get_date_printed(self):
        """
        Get datetime when this report was printed.
        """
        return self.formatLang(datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT), date_time=True)

    def get_date_print_tz(self):
        today = datetime.now()
        context_today = None
        if self.context and self.context.get('tz'):
            tz_name = self.context['tz']
        if tz_name:
            try:
                utc = pytz.timezone('UTC')
                context_tz = pytz.timezone(tz_name)
                utc_today = utc.localize(today, is_dst=False)  # UTC = no DST
                context_today = utc_today.astimezone(context_tz)
            except Exception:
                logging.debug("failed to compute context/client-specific today date, "
                              "using the UTC value for `today`",
                              exc_info=True)
        return (context_today or today).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    def get_user_printed(self):
        """
        Get the user who triggered the printing of this report.
        """
        return self.reported_user or '???'

    def get_user_criteria(self, name):
        """
        The user's criteria to filter data in this report. 
        This function is useful when this report is called by a wizard.
        """
        if not ('data' in self.localcontext and 'form' in self.localcontext['data']):
            return ''
        wizard_form = self.localcontext['data']['form']
        if name in wizard_form:
            return wizard_form[name]
        return ''

    def get_company(self):
        res = self.pool.get('res.users').browse(self.cr, self.uid, self.uid)
        name = res.company_id.name
        address_list = [res.company_id.street or '',
                        res.company_id.street2 or '',
                        res.company_id.city or '',
                        res.company_id.state_id and res.company_id.state_id.name or '',
                        res.company_id.country_id and res.company_id.country_id.name or '',
                        ]
        address_list = filter(None, address_list)
        address = ', '.join(address_list)
        vat = res.company_id.vat
        return {'name': name, 'address': address, 'vat': vat}

    def get_date(self):
        wizard_data = self.get_wizard_data()
        res = {}
        obj_fiscalyear = self.pool.get('account.fiscalyear').browse(
            self.cr, self.uid, wizard_data['fiscalyear'][0])
        if wizard_data['filter'] == 'filter_period':
            period_pool = self.pool.get('account.period')
            period_start = period_pool.browse(
                self.cr, self.uid, wizard_data['period_from'][0])
            period_end = period_pool.browse(
                self.cr, self.uid, wizard_data['period_to'][0])
            res.update({
                'date_from': period_start.date_start,
                'date_to': period_end.date_stop,
            })
        elif wizard_data['filter'] == 'filter_date':
            res.update({
                'date_from': wizard_data['date_from'],
                'date_to': wizard_data['date_to'],
            })
        else:

            res.update({
                'date_from': obj_fiscalyear.date_start,
                'date_to': obj_fiscalyear.date_stop,
            })
        if res:
            res['date_from_date'] = res['date_from']
            res['date_to_date'] = res['date_to']
            res['date_from'] = datetime.strptime(
                res['date_from'], DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y')
            res['date_to'] = datetime.strptime(
                res['date_to'], DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y')
        return res

    def dummy_function(self):
        """
        The only purpose of this function is to make the listed terms appear in the translation.
        No need to call this function.
        """
        _('Address')
        _('Phone')
        _('Email')
        _('Fax')
        _('Printing Date')
        _('Printed By')
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
