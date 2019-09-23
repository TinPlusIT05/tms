# -*- encoding: UTF-8 -*-
##############################################################################

from openerp.osv import osv, fields
from datetime import datetime, timedelta
import openerp
import csv
import math
import logging


class generate_demo_data_wizard(osv.TransientModel):

    _name = "generate.demo.data.wizard"
    _description = 'Wizard to generate demo data.'
    _columns = {
        'min_date': fields.date('Min date'),
        'max_date': fields.date('Max date'),
        'configuration': fields.text('Configuration'),
    }
    _defaults = {
        'configuration': 'The default value for this field should be \
        over-writen by the module actually generating the data.'
    }

    def update_number(self, cr, model, field, multiplier, max_value):
        model_obj = self.pool[model]
        table = model_obj._table
        params = {
            'table': table,
            'field': field,
            'multiplier': multiplier,
            'max_value': max_value
        }
        sql = "UPDATE %(table)s set %(field)s = %(field)s * %(multiplier)s\
            where %(field)s > %(max_value)s" % params
        logging.info("Running: %s" % sql)
        cr.execute(sql)
        return True

    def get_a_date(self, index, total_nb, min_date, max_date):
        '''
            The purpose to use this instead of random function is to be able to
            generate twice the same database
            on 2 instances to facilitate the debug.
        '''
        range_size = (max_date - min_date).days
        # This is rounded to an int value automatically
        step = math.ceil(float(range_size) / total_nb)
        # We use the power to simulate more randomness
        position = (pow((index + 2 * step) / 2, 2)) % range_size
        return min_date + timedelta(position)

    def get_a_datetime(self, index, total_nb, min_date, max_date):
        '''
            The purpose to use this instead of random function is to be able to
            generate twice the same database
            on 2 instances to facilitate the debug.
        '''

        return datetime.combine(self.get_a_date(index, total_nb,
                                                min_date, max_date),
                                datetime.min.time())

    def get_an_int(self, index, total_nb, min_int, max_int):
        '''
            The purpose to use this instead of random function is to be able to
            generate twice the same database
            on 2 instances to facilitate the debug.
        '''
        range_size = max_int - min_int
        step = int(math.ceil(float(range_size) / total_nb))
        # We use the power to simulate more randomness
        position = pow((index * step), 2) % range_size

        return int(min_int + position)

    def get_a_percentage(self, index, total_nb, min_percentage,
                         max_percentage):
        '''
            The purpose to use this instead of random function is to be able to
            generate twice the same database
            on 2 instances to facilitate the debug.
        '''
        range_size = max_percentage - min_percentage
        # This is rounded to an int value automatically
        step = range_size / total_nb
        position = float((index * step * 100) % int(range_size * 100)) / 100

        return min_percentage + position

    def get_file_content(self, file_name, separator='\t'):
        module_path = openerp.modules.get_module_path('trobz_base_demo')
        file_path = '%s/data/%s' % (module_path, file_name)
        res = []

        with open(file_path, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=separator, quotechar='"')
            first_line = True
            for line in reader:
                if first_line:
                    first_line = False
                    continue
                res.append(line)
        return res

    def insert_in_batch(self, cr, uid, model_pool, nb_object,
                        custom_attribute_dict):
        logging.info('insert_in_batch: %s start' % (model_pool._name))
        batch_queries = ''
        i = 0
        batch_count = 0
        while i <= nb_object:
            i += 1
            batch_count += 1
            if i >= nb_object:
                break

            batch_queries += self.get_sql_insert(
                cr, uid, model_pool, i, nb_object, custom_attribute_dict)
            if batch_count > 1000 or len(batch_queries) > 100000:
                batch_count = 0
                cr.execute(batch_queries)
                logging.info('executing batch...')
                batch_queries = ''

        if batch_queries:
            cr.execute(batch_queries)
        logging.info('insert_in_batch: %s end' % (model_pool._name))
        return True

    def unlink_all_from_id(self, cr, uid, model, min_id):
        logging.info('Unlink %s with id >= %s' % (model, min_id))
        model_obj = self.pool[model]
        delete_ids = model_obj.search(cr, uid, [('id', '>=', min_id)])
        model_obj.unlink(cr, uid, delete_ids)
        return True

    def button_generate_demo_data(self, cr, uid, ids, context=None):
        '''
             You must override this function to make it match your context.
        '''
        return {'type': 'ir.actions.act_window_close'}

    def button_flush_demo_data(self, cr, uid, view_id=None, view_type='form',
                               context=None, toolbar=False, submenu=False):
        '''
             You must override this function to make it match your context.
        '''
        return {'type': 'ir.actions.act_window_close'}

    def button_flush_generate_demo_data(self, cr, uid, ids, context=None):
        self.button_flush_demo_data(cr, uid, ids, context)
        self.button_generate_demo_data(cr, uid, ids, context)
        return {'type': 'ir.actions.act_window_close'}
