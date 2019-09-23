# -*- encoding: UTF-8 -*-
##############################################################################

from openerp.osv import osv
import logging
from datetime import date


class generate_demo_data_hr_employee_wizard(osv.TransientModel):

    _inherit = "generate.demo.data.wizard"
    _name = "generate.demo.data.hr.employee.wizard"

    def generate_employees(self, cr, uid, nb_employee, min_date, max_date,
                           country='fr'):
        hr_employee_obj = self.pool['hr.employee']

        country_ids = self.pool['res.country'].search(
            cr, uid, [('code', '=', country.upper())])
        if not country_ids:
            logging.warning(
                'generate_employees, the country code %s is not recognized by \
                OpenERP (see file res_country_data.xml for list of country \
                and codes)' % country)
        country_id = country_ids[0]

# TODO: Create a mapping to read the csv files because they don't
# have the same columns :(
# List of timezones:
# http://stackoverflow.com/questions/13866926/python-pytz-list-of-timezones

        if country == 'fr':
            mapping = {
                'gender': 0,
                'last_name': 3,
                'first_name': 2,
                'street': 4,
                'city': 5,
                'zip': 6,
                'email': 7,
                'phone': 8,
                'birthday': 9
            }
            people_file = 'people_names_fr_50000.csv'
            separator = ','
            price_divider = 2000
            lang = 'fr_FR'
            tz = 'Europe/Paris'

        elif country == 'us':
            mapping = {
                'gender': 0,
                'last_name': 3,
                'first_name': 2,
                'street': 4,
                'city': 5,
                'zip': 6,
                'email': 8,
                'phone': 9,
                'birthday': 10
            }
            people_file = 'people_names_us_3000.csv'
            separator = '\t'
            price_divider = 2000
            lang = 'en_US'
            tz = 'US/Eastern'

        elif country == 'vn':
            mapping = {
                'gender': 0,
                'last_name': 3,
                'first_name': 2,
                'street': 4,
                'city': 5,
                'zip': 6,
                'email': 8,
                'phone': 9,
                'birthday': 10
            }
            people_file = 'people_names_us_3000.csv'
            separator = '\t'
            price_divider = 1
            lang = 'vi_VN'
            tz = 'Asia/Ho_Chi_Minh'

        else:
            logging.warning(
                'generate_employees, country %s unsuppported' % country)

        persons = self.get_file_content(people_file, separator)
        res_users_model_id = self.pool['ir.model'].search(
            cr, uid, [('model', '=', 'res.users')])[0]

        custom_attribute_dict = {
            'persons': persons,
            'price_divider': price_divider,
            'country_id': country_id,
            'lang': lang,
            'tz': tz,
            'res_users_model_id': res_users_model_id,
            'mapping': mapping,
            'min_date': min_date,
            'max_date': max_date,
        }
        self.insert_in_batch(
            cr, uid, hr_employee_obj, nb_employee, custom_attribute_dict)

        return True

    def get_sql_insert(self, cr, uid, model_pool, index, nb_object,
                       custom_attribute_dict):

        person = custom_attribute_dict['persons'][index]
        price_divider = custom_attribute_dict['price_divider']
        country_id = custom_attribute_dict['country_id']
        res_users_model_id = custom_attribute_dict['res_users_model_id']
        lang = custom_attribute_dict['lang']
        tz = custom_attribute_dict['tz']
        mapping = custom_attribute_dict['mapping']
        min_date = custom_attribute_dict['min_date']
        max_date = custom_attribute_dict['max_date']
        wage = self.get_an_int(
            index, nb_object, 3000000, 50000000) / price_divider
        login = '%s%s%s' % (person[mapping['last_name']][0].lower(), person[
                            mapping['first_name']].lower(), index)
        login = login.replace("'", "")
        birthday_split = person[mapping['birthday']].split('/')
        birthday = date(
            int(birthday_split[2]),
            int(birthday_split[0]),
            int(birthday_split[1]))
        alias_name = '%s%s' % (login, index)
        alias_name = alias_name.replace("'", "")
        first_name = person[mapping['first_name']].replace("'", "''")
        last_name = person[mapping['last_name']].replace("'", "''")
        vals = {
            # fixed special charater in string, ex: D'Arcy Patel
            'name': '%s %s' % (first_name, last_name),
            'lang': lang,
            'street': person[mapping['street']].replace("'", "''"),
            'city': person[mapping['city']].replace("'", "''"),
            'zip': person[mapping['zip']],
            'country_id': country_id,
            'email': person[mapping['email']],
            'phone': person[mapping['phone']],
            'tz': tz,
            'birthday': birthday,
            'identification_id': 1943 * 10000 + index,
            'title': 3 if person[mapping['gender']] == 'female' else 5,
            'gender': person[mapping['gender']],
            'wage': wage,
            'login': login,
            'res_users_model_id': res_users_model_id,
            'alias_name': alias_name,
            'marital': 'single' if index % 2 == 0 else 'married',
            'manager': 't' if index % 8 == 0 else 'f',
            'children': min(index % 7, index % 8, index % 9),
            'write_date': self.get_a_datetime(index,
                                              nb_object,
                                              min_date,
                                              max_date)
        }

        SQL_QUERY = """
                INSERT INTO res_partner (
                    name,
                    lang,
                    company_id,
                    use_parent_address,
                    active,
                    street,
                    supplier,
                    city,
                    zip,
                    title,
                    country_id,
                    employee,
                    type,
                    email,
                    phone,
                    tz,
                    customer,
                    is_company,
                    notification_email_send,
                    opt_out,
                    display_name
                ) VALUES (
                    U&'%(name)s',
                    '%(lang)s',
                    1,
                    'f',
                    't',
                    U&'%(street)s',
                    'f',
                    U&'%(city)s',
                    U&'%(zip)s',
                    %(title)s,
                    %(country_id)s,
                    't',
                    'contact',
                    '%(email)s',
                    '%(phone)s',
                    '%(tz)s',
                    'f',
                    'f',
                    'comment',
                    'f',
                    U&'%(name)s'
                );
                INSERT INTO mail_alias (
                    alias_model_id,
                    alias_defaults,
                    alias_name
                ) VALUES (
                    %(res_users_model_id)s,
                    '{}',
                    '%(alias_name)s'
                );
                INSERT INTO res_users (
                    active,
                    login,
                    password,
                    company_id,
                    partner_id,
                    menu_id,
                    alias_id,
                    share
                ) SELECT
                    't',
                    '%(login)s',
                    'password',
                    1,
                    max(rpa.id),
                    1,
                    (select max(mal.id) from mail_alias mal),
                    'f'
                FROM res_partner rpa;
                INSERT INTO resource_resource (
                    time_efficiency,
                    user_id,
                    name,
                    company_id,
                    active,
                    resource_type
                ) SELECT
                    1,
                    max(id),
                    '%(name)s',
                    1,
                    't',
                    'user'
                FROM res_users;
                INSERT INTO hr_employee (
                    resource_id,
                    color,
                    marital,
                    identification_id,
                    birthday,
                    name_related,
                    gender,
                    manager,
                    children,
                    write_date
                ) SELECT
                    max(rre.id),
                    0,
                    '%(marital)s',
                    '%(identification_id)s',
                    '%(birthday)s',
                    '%(name)s',
                    '%(gender)s',
                    '%(manager)s',
                    %(children)s,
                    '%(write_date)s'
                FROM resource_resource rre;
        """

        """ For next step

                INSERT INTO resource.resource (
                ) Select
        """

        return SQL_QUERY % vals
