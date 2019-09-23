# -*- encoding: utf-8 -*-
##############################################################################

from openerp.osv import osv
import logging

class post_object(osv.TransientModel):
    
    _name = 'post.default.fr.data'
    _description = 'Defaul France Data > Post Object '


    def start(self, cr, uid, context=None):
        if context is None:
            context = {}
        
        self.set_number_separator(cr, uid, context=context)
        self.pool['trobz.base'].load_language(cr, uid)
        return True
    

    def set_number_separator(self, cr, uid, context=None):
        """
            The thousand separator should be the space character.
            The Decimal separator should be the space comma.
            EX: 2 361 950,35
        """
        if context is None:
            context = {}
        
        logging.info('Start set_number_separator ...')
        
        res_lang_obj = self.pool.get('res.lang')
        res_lang_ids = res_lang_obj.search(cr, uid, [('code','=','fr_FR')], context=context)
        res_lang_obj.write(cr, uid, res_lang_ids, {'thousands_sep': ' ', 'decimal_point': ','}, context=context) 
        
        logging.info('End set_number_separator ...')
        
        return True
    
post_object()
