# -*- coding: utf-8 -*-
##############################################################################

from openerp.osv import osv
from openerp import models, api
import amount_to_text_vn
from openerp.tools.amount_to_text import amount_to_text, amount_to_text_fr
from openerp.tools import amount_to_text_en
from openerp.tools.translate import _
from openerp.tools.safe_eval import safe_eval
from openerp.modules.module import get_module_resource
from dateutil import tz
from pytz import timezone
import os
import re
import cStringIO
import csv
import codecs
import base64
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as default_time
import logging


_logger = logging.getLogger(__name__)


class trobz_base(models.AbstractModel):

    '''
    Implement general functions at Trobz
    '''
    _name = "trobz.base"
    _description = "Trobz Base"

    def install_translation_po_files(self, cr, uid, module_name, config):
        """
        Load and update all po files in the directory i18n
        EX:
         - module_name: 'sr_module'
         - config = {'fr_FR': [
                                'fr_base.po',
                                'fr_hr.po',
                                'fr_sr_module.po',
                                ]
                    }
        """

        # step 1: read po files
        base_language_import_obj = self.pool['base.language.import']
        module_directory_path = get_module_resource(module_name.strip())
        i18n_directory_path = module_directory_path + '/i18n'
        for key, value in config.iteritems():
            # key is language code
            data = {}
            for po_file_name in value:
                dir_entry_path = i18n_directory_path + '/' + po_file_name
                if os.path.isfile(dir_entry_path):
                    with open(dir_entry_path, 'rb') as my_file:
                        binary_string = my_file.read().encode('base64')
                        data[po_file_name] = binary_string

            # step 2: for each po file, create a record of model
            # base.language.import
            base_language_import_ids = []
            for po_data in data.values():
                vals = {
                    'code': key,
                    'data': po_data,
                    'name': key,
                    'overwrite': True
                }
                new_id = base_language_import_obj.create(cr, uid, vals)
                if new_id:
                    base_language_import_ids.append(new_id)

            # step 3: for each record of model base.language.import, call
            # function import_lang
            for base_language_import_id in base_language_import_ids:
                base_language_import_obj.import_lang(
                    cr, uid, [base_language_import_id])

        return True

    def update_config(self, cr, uid, config_setting_model_name, config_data,
                      context=None):
        '''
        Can be used to update the application setting at
        Settings > Configuration > xxx
        '''
        if not context:
            context = {}
        # get configure setting object
        config_obj = self.pool[config_setting_model_name]
        # create a osv memory object
        config_id = config_obj.create(cr, uid, config_data, context)
        # run execute function to update the changes
        config_obj.execute(cr, uid, [config_id], context)
        return True

    def unlink_object_by_xml_id(self, cr, uid, module, xml_id):
        try:
            _logger.info(
                'unlink_object_by_xml_id, module: %s, xml_id: %s'
                % (module, xml_id))
            obj = self.pool['ir.model.data'].get_object_reference(
                cr, uid, module, xml_id)
            model_obj = self.pool[obj[0]]
            # Note: unlink also deletes ir_values and ir.model.data
            model_obj.unlink(cr, uid, [obj[1]])
        except (ValueError, TypeError):
            _logger.warning(
                'The xml_id "%s" of module "%s" could not be found. Maybe it \
                has already been deleted or the wrong module/xml_id is used.'
                % (xml_id, module))
        return True

    def delete_default_products(self, cr, uid, products_to_remove):
        '''
        '''
        product_obj = self.pool['product.product']
        product_ids = product_obj.search(
            cr, uid, [('name', 'in', products_to_remove)])
        # set product as inactive instead of delete it forever.
        # this will help to ignore error when upgrade "base"
        if product_ids:
            product_obj.write(cr, uid, product_ids, {'active': False})
        return True

    def no_none_values_list(self, list_list):
        """
        Replace None values by False (XMLRPC does not allow None values).
        """
        for idx in range(0, len(list_list)):
            list_list[idx] = list(list_list[idx])
            child_list = list_list[idx]
            for idx2 in range(0, len(child_list)):
                if child_list[idx2] is None:
                    child_list[idx2] = False
        return list_list

    def no_none_values_dict(self, list_dict):
        """
        Replace None values by False (XMLRPC does not allow None values).
        """
        for idx in range(0, len(list_dict)):
            child_dict = list_dict[idx]
            for k in child_dict:
                if child_dict[k] is None:
                    child_dict[k] = False
        return list_dict

    def run_sql_script(self, cr, uid, sql, dict_result=False):
        real_sql = sql
        if sql.startswith(u'\ufeff'):
            real_sql = sql[1:]
        cr.execute(real_sql)
        try:
            if not dict_result:
                result = cr.fetchall()
                if result:
                    result = self.no_none_values_list(result)
            else:
                result = cr.dictfetchall()
                if result:
                    result = self.no_none_values_dict(result)
        except:
            return True
        return result

    def get_ean13_oorpc(self, cr, uid, base_number):
        """
        This function is used by OORPC.
        """
        return self.get_ean13(base_number)

    def get_ean13(self, base_number):
        if len(str(base_number)) > 12:
            raise osv.except_osv(_('Error!'),
                                 _('Invalid input base number for EAN13 code!')
                                 )
        # weight number
        ODD_WEIGHT = 1
        EVEN_WEIGHT = 3
        # Build a 12 digits base_number_str by adding 0 for missing first
        # characters
        base_number_str = '%s%s' % (
            '0' * (12 - len(str(base_number))), str(base_number))
        # sum_value
        sum_value = 0
        for i in range(0, 12):
            if i % 2 == 0:
                sum_value += int(base_number_str[i]) * ODD_WEIGHT
            else:
                sum_value += int(base_number_str[i]) * EVEN_WEIGHT
        # calculate the last digit
        sum_last_digit = sum_value % 10
        calculated_digit = 0
        if sum_last_digit != 0:
            calculated_digit = 10 - sum_last_digit
        barcode = base_number_str + str(calculated_digit)
        return barcode

    def check_ean13(self, ean13_num):
        ean13_num = str(ean13_num)
        if not ean13_num or len(ean13_num) != 13 or not ean13_num.isdigit():
            return False

        base_number = ean13_num[:12]
        ean13_number_test = ''
        if base_number:
            ean13_number_test = self.get_ean13(base_number)

        if not ean13_number_test or ean13_number_test != ean13_num:
            return False

        return True

    def amount_to_text(self, nbr, lang='vi_VN', currency='USD'):
        if lang and ('vi' in lang or 'vn' in lang):
            text = amount_to_text_vn.amount_to_text(nbr, currency) + u' đồng'
        elif 'fr' in lang:
            text = amount_to_text_fr(nbr, currency)
        elif 'en' in lang:
            text = amount_to_text_en.amount_to_text(nbr, currency)
        else:
            text = amount_to_text(nbr, currency)
        if text:
            text = text[0].upper() + text[1:]
        return text

    def get_selection_value(self, selection_list, selected_key):
        '''
        This fucntion help to return selected value associated with selected
        key.
        Example:
            - Selection list: [('assigned', 'Assigned'),
                               ('test', 'Test'),
                               ('close', 'Close')]
            - Selected key: 'test'
        After calling the function, the return value is 'Test'
        '''

        if not selection_list or not selected_key:
            raise osv.except_osv(_('Error!'),
                                 _('Invalid input parameters!'))

        selected_value = None
        selection_dict = dict(selection_list)
        if selection_dict:
            selected_value = selection_dict.get(selected_key)
            if not selected_value:
                raise osv.except_osv(_('Error!'),
                                     _("Can not find associated value with \
                                     selected key '" + selected_key + "'!"))

        return selected_value

    def get_selection_value_from_field(self, cr, uid, model_name,
                                       selection_field_name, selected_key):
        '''
        This fucntion help to return selected value associated with selected
        key of a selection field in a model.
        Example:
            Input:
                - model_name: model_person
                - selection_field_name: gender [('male', 'Male'),
                                                ('female', 'Female')]
                - selected_key: 'male'
            Output: 'Male'
        '''

        if not model_name or not selection_field_name or not selected_key:
            raise osv.except_osv(_('Error!'),
                                 _('Invalid input parameters!'))

        # to make sure we can access any object, I set uid = 1 (Administrator
        # user)
        uid = 1
        # get model
        model_obj = self.pool[model_name]
        if not model_obj:
            raise osv.except_osv(_('Error!'),
                                 _("Can not find model '" + model_name + "'!"))
        # get selection field
        selection_field = model_obj.fields_get(
            cr, uid, allfields=[selection_field_name])
        if not selection_field:
            raise osv.except_osv(_('Error!'),
                                 _('Can not find selection field %s \
                                 in model %s'
                                   % (selection_field_name, model_name)))
        # get selected value
        selection_list = selection_field[selection_field_name] and\
            selection_field[selection_field_name]['selection'] or False
        if selection_list:
            selection_dict = dict(selection_list)
            if selection_dict:
                selected_value = selection_dict.get(selected_key)
                if not selected_value:
                    raise osv.except_osv(_('Error!'),
                                         _("Can not find associated value \
                                         with selected key %s !"
                                           % (selected_key)))
        return selected_value

    def convert_from_utc_to_current_timezone(self,
                                             cr,
                                             uid,
                                             date,
                                             current_time_zone=None,
                                             datetime_format=default_time,
                                             get_str=False,
                                             context=None):
        """
        Convert from UTC to current time zone
        """
        if not current_time_zone:
            if context:
                current_time_zone = context.get('tz', False)
            if not current_time_zone:
                current_time_zone = self.pool['ir.config_parameter'].get_param(
                    cr, uid, 'Default Timezone')
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz(current_time_zone)
        if isinstance(date, (str, unicode)):
            # Convert date from str to datetime
            date = datetime.strptime(date, datetime_format)

        if datetime_format != default_time:
            from_zone_obj = timezone(current_time_zone)
            date = from_zone_obj.localize(date)

        date_zone = date.replace(tzinfo=from_zone)
        date_current = date_zone.astimezone(to_zone)
        date_current = date_current.strftime(datetime_format)
        if get_str:
            return date_current
        return datetime.strptime(date_current, datetime_format)

    def convert_from_current_timezone_to_utc(self,
                                             cr,
                                             uid,
                                             date,
                                             current_time_zone=None,
                                             datetime_format=default_time,
                                             get_str=False,
                                             context=None):
        """
        Convert from current time zone to UTC
        """
        if context is None:
            context = {}
        if not current_time_zone:
            current_time_zone = context.get('tz', False)
            if not current_time_zone:
                current_time_zone = self.pool['ir.config_parameter'].get_param(
                    cr, uid, 'Default Timezone')
        from_zone = tz.gettz(current_time_zone)
        to_zone = tz.gettz('UTC')
        if isinstance(date, (str, unicode)):
            # Convert date from str to datetime
            date = datetime.strptime(date, datetime_format)

        if datetime_format != default_time:
            from_zone_obj = timezone(current_time_zone)
            date = from_zone_obj.localize(date)

        date_zone = date.replace(tzinfo=from_zone)
        date_utc = date_zone.astimezone(to_zone)
        date_utc = date_utc.strftime(datetime_format)
        if get_str:
            return date_utc
        return datetime.strptime(date_utc, datetime_format)

    def get_all_group_full_name(self, cr, uid):
        '''
        '''
        result = {}
        group_obj = self.pool['res.groups']
        all_group_ids = group_obj.search(cr, uid, [])
        for group in group_obj.browse(cr, uid, all_group_ids):
            result[group.full_name] = group.id
        return result

    def create_model_access_rights(self, cr, uid, model_access_rights,
                                   context=None):
        '''
         * Purpose: Create model access right
         ** How to use:
            1. Create data in file security_set_up.py in each project:
                - [1,1,1,1]: present 4 permissions: "perm_read","perm_write",
                "perm_create","perm_unlink"
                Ex:
                    g_hr_employee = "Employee"
                    g_user = "User"
                    g_manuf_user = "Manufacturing / Manager"
                    g_all = '' (all groups)

                    MODEL_ACCESS_RIGHTS = {
                                        ('nationality','accident.type.category',
                                        'accident.type.rate',
                                         'activity.naf','admin.activity.type',
                                         'admin.skill.activity','admin.skill',
                                         'autonomy.level'):
                                         {(g_hr_employee,g_user) : [0,1,1,1]
                                          (g_all):[1,1,1,1]},
                                ...
                                }
                or MODEL_ACCESS_RIGHTS = {
                                           'mrp.bom': {
                                                    g_hr_employee: [1,1,0,1],
                                                    g_manuf_user: [1,0,0,1],
                                                    g_all: [1,1,1,1]
                                       },
                                       'hr.employee': {
                                                    g_hr_employee : [1,1,0,1],
                                                    g_manuf_user: [1,0,0,1],
                                                    g_all: [1,1,1,1]
                                       }
                                       ....
                                    }
            2. Update context:
                context.update({'module_name': 'your_module_name'})

            3. Call Function
                self.pool['trobz.base'].create_model
                _access_rights(cr, uid, MODEL_ACCESS_RIGHTS, context)
        '''
        _logger.info('********** START CREATE MODEL ACCESS RIGHT **********')
        res = False
        ir_module_access_pool = self.pool['ir.model.access']
        if not context.get('module_name', False):
            raise osv.except_osv(_('Error'), _('Cannot find module name '))
        model_access_ids = ir_module_access_pool.search(
            cr, uid, [('name', 'like', context.get('module_name', False))])
        ir_module_access_pool.unlink(
            cr, uid, model_access_ids, context=context)

        # HOANG
        dict_groups_name_ids = self.get_all_group_full_name(cr, uid)
        ir_pool = self.pool['ir.model.access']
        # Model_acess {(A,B,C):{(a,b):[1,1,1,0],(b,c):[0,0,1,1]}}
        key_model_access_right = ()
        for k, v in model_access_rights.iteritems():
            # key_model_access_right = (A,B,C)
            # val_model_access_right = {(a,b):[1,1,1,0],(b,c):[0,0,1,1]}
            if not isinstance(k, (tuple)):
                key_model_access_right = (k,)

            for model in key_model_access_right:
                model_ids = self.pool['ir.model'].search(
                    cr, uid, [('model', '=', model)])
                if not model_ids:
                    raise osv.except_osv(
                        _('Error'), _('Cannot find model %s in systems!!!'
                                      % (model)))
                model_id = model_ids[0]

                for groups, permissions in v.iteritems():
                    # groups= (a,b)
                    # permissions = [1,1,1,0]
                    if not isinstance(groups, (tuple)):
                        groups = (groups,)

                    for group in groups:
                        group_id = None
                        name = "%s_%s_ALL_%s" % (
                            context.get('module_name', False),
                            model, permissions)
                        if group:
                            group_id = dict_groups_name_ids.get(group, False)
                            if not group_id:
                                raise osv.except_osv(
                                    _('Error'), _('Cannot find group %s in \
                                                    systems!!!' % (group)))
                            name = "%s_%s_%s_%s" % (
                                context.get('module_name', False),
                                model, group, permissions)
                        ir_ids = ir_pool.search(cr,
                                                uid,
                                                [('model_id', '=', model_id),
                                                 ('group_id', '=', group_id)])
                        vals = {
                            'model_id': model_id,
                            'name': name,
                            'perm_read': permissions[0],
                            'perm_write': permissions[1],
                            'perm_create': permissions[2],
                            'perm_unlink': permissions[3],
                            'active': True,
                            'group_id': group_id,
                        }
                        if ir_ids:
                            res = self.pool['ir.model.access'].write(
                                cr, uid,
                                ir_ids,
                                vals,
                                context=context)
                        else:
                            res = self.pool['ir.model.access'].create(
                                cr, uid, vals, context=context)
        _logger.info('********** END CREATE MODEL ACCESS RIGHT **********')
        return res

    def convert_datetime_format(self, datetime_string, current_format,
                                expected_format):
        '''
            use: This function is used to change format for datetime object

            @datetime_string: datetime string that you want to change format
            @current_format: current format of the input_datetime string
            @expected_format: the format that you want to change the current
                            datetime string format to

            @return: datetime expected formatted string
        '''
        if isinstance(datetime_string, str):
            return datetime.strptime(datetime_string,
                                     current_format).strftime(expected_format)
        else:
            raise osv.except_osv(
                ('Error !'), ("convert_datetime_format(....) function receive \
                                string as it parameter"))

    def check_valid_content_and_detect_delimeter(self,
                                                 cr,
                                                 uid,
                                                 content,
                                                 number_of_columns,
                                                 header_comma,
                                                 header_semicolon,
                                                 context=None):
        if not content:
            raise osv.except_osv(_('Error!'), _('Invalid content!'))

        delimeter_expected = ';'

        csv_input = cStringIO.StringIO(content)
        encoding = 'iso-8859-15'
        codecs_reader = codecs.getreader(encoding)(csv_input)
        header = None
        for row in codecs_reader:
            header = row
            break
        header = header.strip()
        if header == header_comma:
            delimeter_expected = ','
        elif header == header_semicolon:
            delimeter_expected = ';'
        else:
            csv_input = cStringIO.StringIO(content)
            encoding = 'utf-8'
            codecs_reader = codecs.getreader(encoding)(csv_input)
            header = None
            for row in codecs_reader:
                header = row
                break
            header = header.strip()
            # eliminate quote and double quote in header ,header_comma and
            # header_semicolon then compare them
            not_quote_header = re.sub('["\']', '', header)
            not_quote_header_comma = re.sub('["\']', '', header_comma)
            not_quote_header_semicolon = re.sub('["\']', '', header_semicolon)
            if not_quote_header == not_quote_header_comma:
                delimeter_expected = ','
            elif not_quote_header == not_quote_header_semicolon:
                delimeter_expected = ';'
            else:
                raise osv.except_osv(_('Error!'), _(
                    'The header of the CSV file is not correct! It must be: %s \
                                                    ') % header_semicolon)

        delimeter_detected = ';'

        csv_input = cStringIO.StringIO(content)
        reader = csv.reader(csv_input, quotechar='"', delimiter=';')
        header = reader.next()
        first_row = None
        try:
            first_row = reader.next()
        except:
            pass
        correct_row = True
        if first_row is not None:
            if len(first_row) != number_of_columns:
                correct_row = False
            else:
                delimeter_detected = ';'

        if not correct_row:
            csv_input = cStringIO.StringIO(content)
            reader = csv.reader(csv_input, quotechar='"', delimiter=',')
            header = reader.next()
            if not correct_row:
                first_row = None
                try:
                    first_row = reader.next()
                except:
                    pass
                if first_row is not None:
                    if len(first_row) != number_of_columns:
                        raise osv.except_osv(
                            _('Error!'), _('The structure of the CSV file is \
                                            not correct!'))
                    else:
                        delimeter_detected = ','

        if delimeter_detected != delimeter_expected:
            raise osv.except_osv(_('Error!'), _(
                'It seems that the separator being used is not consistent in \
                the file you are trying to import.'))

        return delimeter_detected

    def update_company_logo(self, cr, uid):
        _logger.info('Post Object: Updating company logo has been started.')
        company_path = self.pool['ir.config_parameter'].get_param(
            cr, uid, 'Company logo path', False)
        if not company_path:
            _logger.error(
                'Could not find configure parameter: Company logo path.')
            return True

        # When it's dict string
        if '{' in company_path and '}' in company_path:
            company_path = safe_eval(company_path)

        company_args = []
        company_names = None
        if isinstance(company_path, dict):
            company_names = company_path.keys()
            company_args = [('name', 'in', company_names)]
        company_obj = self.pool['res.company']
        all_company_ids = company_obj.search(cr, uid, company_args)
        companies = company_obj.browse(cr, uid, all_company_ids)

        for company in companies:
            if company_names:
                if company.name and company_path.get(company.name):
                    img_path = company_path[company.name]
                else:
                    continue
            else:
                img_path = company_path
            module_path = img_path.split(',')
            if len(module_path) == 2:
                path = get_module_resource(
                    module_path[0].strip(), module_path[1].strip())
                if path and os.path.isfile(path):
                    try:
                        f = open(path)
                        content = base64.encodestring(f.read())
                        company_obj.write(
                            cr, uid, company.id, {'logo': content})
                    except Exception, e:
                        _logger.error(
                            'Error when updating company logo: "%s".' % (e,))
                else:
                    _logger.info('File does not exist: "%s".' % (path,))
            else:
                _logger.info('Invalid value: "%s".' % (company_path,))

        _logger.info('Post Object: Updating company logo has been done.')
        return True

    def load_language(self, cr, uid):
        """
        Auto load a language on the install of a project's module, for example, drm_modules, qrvr_modules...
        """
        logging.info('Start loading default Translation...')
        language_to_load = self.pool.get(
            'ir.config_parameter').get_param(cr, uid, 'language_to_load')
        if not language_to_load:
            logging.info('No default Translation was defined.')
            return False
        languages = language_to_load.split(',')
        modobj = self.pool.get('ir.module.module')
        mids = modobj.search(cr, uid, [('state', '=', 'installed')])
        for language_to_load in languages:
            language_to_load = language_to_load.strip()
            sql = "SELECT id, active FROM res_lang WHERE code = '%s'" % language_to_load
            cr.execute(sql)
            if cr.rowcount:
                language = cr.fetchone()
                if not language[1]:
                    self.pool.get('res.lang').write(
                        cr, uid, [language[0]], {'active': True})
                logging.info('Default Translation of %s was loaded.' %
                             language_to_load)
            modobj.update_translations(
                cr, uid, mids, language_to_load, context={})
        logging.info('Finish loading default Translation.')
        return True

    @api.model
    def run_post_object_one_time(self, object_name, list_functions=[]):
        """
        Generic function to run post object one time
        Input:
            + Object name: where you define the functions
            + List functions: to run
        Result:
            + Only functions which are not run before will be run
        """
        _logger.info('==START running one time functions for post object: %s'
                     % object_name)
        if isinstance(list_functions, (str, unicode)):  # @UndefinedVariable
            list_functions = [list_functions]
        if not list_functions\
                or not isinstance(list_functions, (list)):
            _logger.warning('Invalid value of parameter list_functions.\
                            Exiting...')
            return False

        ir_conf_para_env = self.env['ir.config_parameter']
        post_object_env = self.env[object_name]
        ran_functions = \
            ir_conf_para_env.get_param(
                'List_post_object_one_time_functions', '[]')
        ran_functions = safe_eval(ran_functions)
        if not isinstance(ran_functions, (list)):
            ran_functions = []
        for function in list_functions:
            if (object_name + ':' + function) in ran_functions:
                continue
            getattr(post_object_env, function)()
            ran_functions.append(object_name + ':' + function)
        if ran_functions:
            ir_conf_para_env.set_param('List_post_object_one_time_functions',
                                       str(ran_functions))
        _logger.info('==END running one time functions for post object: %s'
                     % object_name)
        return True

    @api.model
    def get_chart_template_data(self, chart_template_id=False):
        generate_account_obj = self.env['wizard.multi.charts.accounts']
        res = generate_account_obj.onchange_chart_template_id(
            chart_template_id
        )
        if chart_template_id:
            chart_template = self.env['account.chart.template'].browse(
                chart_template_id
            )
            # Do not generate default bank / cash account and set the
            # code digit to 0 when installing VAS
            if chart_template.name == 'VN - Chart of Accounts':
                res['value']['bank_accounts_id'] = []
                res['value']['code_digits'] = 0

        return res

    @api.model
    def set_config_wizard_status(self, name, state='open'):
        """
        Set the configuration wizard to Done
        """
        action_todo_obj = self.env['ir.actions.todo']
        configure_wizards = action_todo_obj.search(
            [('state', '=', state),
             '|', ('name', '=', name), ('action_id.name', '=', name)]
        )
        if configure_wizards:
            configure_wizards.write({'state': 'done'})
        return True

    @api.model
    def _check_exist_coa(self, company_id, company_name):
        """
        Check whether the Chart of Accounts is installed.
        """
        account_obj = self.env['account.account']
        exist_coas = account_obj.search(
            [('parent_id', '=', False),
             ('name', '!=', 'Chart For Automated Tests'),
             ('company_id', '=', company_id)],
            limit=1
        )
        if exist_coas:
            _logger.info('COA is already configured for company %s.'
                         % company_name.decode('utf8'))
            return True
        return False

    @api.model
    def configure_chart_of_accounts(self, data={}):
        """
        Configure Chart of Accounts
            + data will have this format
            {'company name1': 'module_name.coa_template_xml_id',
            'company name2': 'module_name.coa_template_xml_id'}
        """
        _logger.info('Configuring chart of accounts has been started.')
        config_param_obj = self.env['ir.config_parameter']
        company_obj = self.env['res.company']
        ir_model_data_obj = self.env['ir.model.data']
        generate_account_obj = self.env['wizard.multi.charts.accounts']

        if not data:
            # Get the configuration of companies
            # and charts of accounts to setup.
            chart_data = config_param_obj.get_param(
                key='Chart of Accounts', default=False
            )
            if not chart_data:
                _logger.warning('Cannot find the param Chart of Accounts!')
                return True
            data = eval(chart_data)
            _logger.warning('The way to configure COA automatically is'
                            'deprecated. Use real post object instead.')
        # Get list of available charts
        account_installer_obj = self.env['account.installer']
        all_available_charts = account_installer_obj._get_charts()
        all_available_charts = [x[0] for x in all_available_charts]

        # For each company, coa_xml_id
        for company_name, chart in data.iteritems():
            # Find the company name
            companies = company_obj.search(
                [('name', '=', company_name)], limit=1
            )
            if not companies:
                raise Warning(
                    _('Error when automatically configuring COA!'),
                    _('Could not find company: "%s".')
                    % company_name.decode('utf8'))
            if self._check_exist_coa(companies[0].id, company_name):
                continue
            # The chart's XML ID must have format "l10n_xx.name_of_chart"
            chart = chart.split('.')
            if len(chart) < 2:
                _logger.error('Format of COA of company %s is not correct.'
                              % (company_name,))
                _logger.error('chart: %s' % chart)
                continue

            if chart[0] not in all_available_charts:
                _logger.error('Chart "%s" is not available.' % (chart[1],))
                continue

            # Install COA
            vals = {'charts': chart[0], 'company_id': companies[0].id}
            installer = account_installer_obj.create(vals)
            _logger.info('Installing template chart of accounts: "%s".'
                         % (chart[0],))
            installer.execute()

            # Generate COA
            chart_templates = ir_model_data_obj.search(
                [('model', '=', 'account.chart.template'),
                 ('module', '=', chart[0]),
                 ('name', '=', chart[1])],
                limit=1, order='id desc'
            )
            if not chart_templates:
                _logger.error('Could not find chart template of module: "%s"'
                              % (chart[1],))
                continue

            chart_template = chart_templates[0]
            if not chart_template.res_id:
                _logger.error('No res_id defined in the chart template.')
                continue
            multi_chart_data = {
                'company_id': companies[0].id,
                'chart_template_id': chart_template.res_id,
                'code_digits': 6
            }
            chart_template_data = self.get_chart_template_data(
                chart_template.res_id
            )
            if chart_template_data.get('value', False):
                multi_chart_data.update(chart_template_data['value'])

            _logger.info('Generating COA from template chart: "%s".'
                         % (chart[0],))
            wizard = generate_account_obj.create(multi_chart_data)
            wizard.execute()

        # Update status of the configuration wizard to Done
        self.set_config_wizard_status('Configure Accounting Data', 'open')
        self.set_config_wizard_status('Set Your Accounting Options', 'open')
        _logger.info('Configuring chart of accounts has been done.')
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
