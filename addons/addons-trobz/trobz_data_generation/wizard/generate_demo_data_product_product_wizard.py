# -*- encoding: UTF-8 -*-
##############################################################################

from openerp.osv import osv
import logging


class generate_demo_data_product_product_wizard(osv.TransientModel):
    _inherit = "generate.demo.data.wizard"
    _name = "generate.demo.data.product.product.wizard"

    def generate_products(self, cr, uid, nb_products=10, context=None):

        product_obj = self.pool['product.product']
        category_obj = self.pool['product.category']

        price_divider = 1
        if context and context.get('price_divider', False):
            price_divider = context['price_divider']
            logging.warning(
                'All product prices will be divided by %s.' % (price_divider))

        products = self.get_file_content('product_product.csv', ',')
        category_ids = category_obj.search(cr, uid, [])
        categories = category_obj.read(cr, uid, category_ids, ['name'])
        category_dict = {}

        for category in categories:
            category_dict[category['name']] = category['id']

        custom_attribute_dict = {'products': products,
                                 'category_dict': category_dict,
                                 'price_divider': price_divider}

        self.insert_in_batch(
            cr, uid, product_obj, nb_products, custom_attribute_dict)

        return True

    def get_sql_insert(self,
                       cr,
                       uid,
                       model_pool,
                       index,
                       nb_object,
                       custom_attribute_dict):

        category_dict = custom_attribute_dict['category_dict']
        product = custom_attribute_dict['products'][index]
        price_divider = custom_attribute_dict['price_divider']
        # FirstName,LastName,Company,Address,City,County,State,ZIP,Phone,
        # Fax,Email,Web
        percentage = self.get_a_percentage(index,
                                           nb_object, 0.4, 0.8) / price_divider

        standard_price = float(product[2]) * percentage
        vals = {
            'name': product[0],
            'categ_id': category_dict[product[1]],
            'list_price': float(product[2]) / price_divider,
            'standard_price': standard_price
        }

        SQL_QUERY = """
                INSERT INTO product_template (
                    name,
                    list_price,
                    standard_price,
                    mes_type,
                    uom_id,
                    cost_method,
                    categ_id,
                    uos_coeff,
                    sale_ok,
                    company_id,
                    uom_po_id,
                    type,
                    supply_method,
                    procure_method,
                    purchase_ok
                ) VALUES (
                    '%(name)s',
                    '%(list_price)s',
                    '%(standard_price)s',
                    'fixed',
                    1,
                    'standard',
                    '%(categ_id)s',
                    1,
                    't',
                    1,
                    1,
                    'product',
                    'buy',
                    'make_to_stock',
                    't'
                );
                INSERT INTO product_product (
                    product_tmpl_id,
                    name_template,
                    active,
                    valuation
                ) select
                    max(id),
                    '%(name)s',
                    't',
                    'manual_periodic'
                from product_template;
        """
        sql = SQL_QUERY % vals
        return sql
