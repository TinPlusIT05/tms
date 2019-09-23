# -*- encoding: UTF-8 -*-
##############################################################################

from openerp.osv import osv
import logging


class generate_demo_data_product_category_wizard(osv.TransientModel):

    _inherit = "generate.demo.data.wizard"
    _name = "generate.demo.data.product.category.wizard"

    def generate_product_categories(self, cr, uid):
        product_category_obj = self.pool['product.category']
        product_categories = self.get_file_content('product_category.csv')

        custom_attribute_dict = {'product_categories': product_categories}
        self.insert_in_batch(
            cr,
            uid,
            product_category_obj,
            len(product_categories),
            custom_attribute_dict)

        return True

    def get_sql_insert(self,
                       cr,
                       uid,
                       model_pool,
                       index,
                       nb_object,
                       custom_attribute_dict):

        product_categories = custom_attribute_dict['product_categories'][index]
        # FirstName,LastName,Company,Address,City,County,State,ZIP,Phone,Fax,
        # Email,Web
        vals = {'name': product_categories[0]}

        SQL_QUERY = """
                INSERT INTO product_category (name)
                    VALUES ('%(name)s');
        """
        sql = SQL_QUERY % vals
        return sql

    def generate_product_categories_orm(self, cr, uid):
        logging.info('generate_product_categories: start')
        product_category_obj = self.pool['product.category']

        product_categories = self.get_file_content('product_category.csv')
        for category in product_categories:
            product_category_obj.create(cr, uid, {'name': category[0]})

        logging.info('generate_category: end')
