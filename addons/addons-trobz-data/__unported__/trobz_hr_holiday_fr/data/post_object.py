# -*- encoding: utf-8 -*-

from openerp.osv import osv
import logging

class post_object_hr_holiday_fr(osv.osv_memory):
    _name = "post.object.hr.holiday.fr"
    _description = "Post Deployment "
    _auto = False
    _log_access = True

    def start(self, cr, uid, context=None):
        self.add_fr_translation_public_holiday(cr, uid, context=context)
        return True

    def add_fr_translation_public_holiday(self, cr, uid, context=None):
        """
        Add translations for public holidays of France
        """
        logging.info('Start loading translations for the public holidays of France...')
        self.pool.get('post.hr.holiday').add_translation_public_holiday(cr, uid, 'public_holiday_fr_translations')
        logging.info('End loading translations for the public holidays of France.')
        return True
    
post_object_hr_holiday_fr()
