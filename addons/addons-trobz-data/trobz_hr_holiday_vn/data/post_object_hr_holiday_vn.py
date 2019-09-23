# -*- encoding: utf-8 -*-
from openerp import models, api
import logging
from openerp.tools.safe_eval import safe_eval


class post_object_hr_holiday_vn(models.TransientModel):
    _name = "post.object.hr.holiday.vn"
    _log_access = True

    @api.model
    def start(self):
        return True

    @api.model
    def _add_translation_public_holiday(self, parameter):
        """
        Add translations for public holidays
        """
        translation_obj = self.env['ir.translation']
        param_obj = self.env['ir.config_parameter']
        # Read parameters
        translations = param_obj.get_param(parameter)
        if not translations:
            logging.info('No translations was defined.')
            return True
        # translations should be a dictionary
        translations = safe_eval(translations)
        # Detect available languages in the system
        lang_obj = self.env['res.lang']
        langs = lang_obj.search([])
        lang_codes = []
        for lang in langs:
            if lang.code and lang.code not in lang_codes:
                lang_codes.append(lang.code)
        # For each term, check current translation
        holiday_obj = self.env['hr.public.holiday']
        for lang_code, trans_dict in translations.iteritems():
            # If this language is not available in the system,
            # continue to next language.
            if lang_code not in lang_codes:
                continue
            # For each keyword and translated keyword
            for keyword, trans_keyword in trans_dict.iteritems():
                # Search for all translations of this keyword
                trans = translation_obj.search(
                    [('lang', '=', lang_code),
                     ('name', '=', 'hr.public.holiday,name'),
                     ('src', '=', keyword)]
                )
                if trans:
                    trans.write({'value': trans_keyword})
                else:
                    common_vals = {
                        'lang': lang_code,
                        'name': 'hr.public.holiday,name',
                        'src': keyword,
                        'value': trans_keyword,
                        'type': 'model'
                    }
                    holidays = holiday_obj.search([('name', '=', keyword)])
                    for holiday in holidays:
                        vals = {'res_id': holiday.id}
                        vals.update(common_vals)
                        test = translation_obj.create(vals)
                        print '==== CREATED', test
        return True

    @api.model
    def add_vn_translation_public_holiday(self):
        """
        Add translations for public holidays of Vietnam
        """
        logging.info('=== START add_vn_translation_public_holiday')
        self._add_translation_public_holiday('public_holiday_vi_translations')
        logging.info('=== END add_vn_translation_public_holiday')
        return True

    @api.model
    def update_leave_type_xml_id(self):
        """
        Update XML-ID of leave type
        # TODO: remove after status of 2.5_no_new_feature is 'done'
        """
        logging.info('=== START update_leave_type_xml_id')
        sql = """
        UPDATE ir_model_data
        SET module='trobz_hr_holiday_vn',
            name = replace(name, 'trobz_holiday', 'hr_holiday')
        WHERE module='trobz_hr_holiday'
            AND model='hr.holidays.status'
            AND name ilike 'trobz_holiday_%'
        RETURNING id;
        """
        self._cr.execute(sql)
        logging.info('=== END update_leave_type_xml_id %s'
                     % str(self._cr.fetchall()))
        return True
