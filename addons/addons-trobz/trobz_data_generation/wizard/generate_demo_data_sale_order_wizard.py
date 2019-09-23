# -*- encoding: UTF-8 -*-
##############################################################################

from openerp.osv import osv


class generate_demo_data_sale_order_wizard(osv.TransientModel):

    _inherit = "generate.demo.data.wizard"
    _name = "generate.demo.data.sale.order.wizard"

    SALE_ORDER_STATES = ['draft', 'progress', 'manual', 'cancel', 'done']

    def generate_sale_orders(self, cr, uid, nb_sale, min_date, max_date):

        sale_order_obj = self.pool['sale.order']
        product_obj = self.pool['product.product']

        product_ids = product_obj.search(cr, uid, [])
        product_datas = product_obj.read(
            cr, uid, product_ids, ['list_price', 'name', 'id'])

        partner_ids = self.pool['res.partner'].search(cr, uid, [])
        user_ids = self.pool['res.users'].search(cr, uid, [])
        shop_id = self.pool['sale.shop'].search(cr, uid, [])[0]
        pricelist_id = self.pool['product.pricelist'].search(
            cr, uid, [('type', '=', 'sale')])[0]

        custom_attribute_dict = {
            'products': product_datas,
            'partner_ids': partner_ids,
            'user_ids': user_ids,
            'shop_id': shop_id,
            'pricelist_id': pricelist_id,
            'min_date': min_date,
            'max_date': max_date,
        }

        self.insert_in_batch(
            cr, uid, sale_order_obj, nb_sale, custom_attribute_dict)

    def get_sql_insert(self,
                       cr,
                       uid,
                       model_pool,
                       index,
                       nb_object,
                       custom_attribute_dict):

        min_date = custom_attribute_dict['min_date']
        max_date = custom_attribute_dict['max_date']
        products = custom_attribute_dict['products']
        user_ids = custom_attribute_dict['user_ids']
        partner_ids = custom_attribute_dict['partner_ids']
        shop_id = custom_attribute_dict['shop_id']
        nb_lines = min(index % 15, index % 21, index % 17) + 1
        pricelist_id = custom_attribute_dict['pricelist_id']

        params = {
            'name': 'DD-' + str(index),
            'shop_id': shop_id,
            'date_order': self.get_a_date(index,
                                          nb_object,
                                          min_date,
                                          max_date),
            'partner_id': partner_ids[self.get_an_int(index, nb_object, 0,
                                                      len(partner_ids) - 1)],
            'user_id': user_ids[self.get_an_int(index,
                                                nb_object,
                                                0,
                                                len(user_ids) - 1)],
            'state': self.SALE_ORDER_STATES[max(index % 4,
                                                min(index % 5, 4),
                                                min(index % 6, 4),
                                                min(index % 7, 4))],
            'pricelist_id': pricelist_id
        }

        SQL_QUERY = """
                INSERT INTO sale_order (
                    origin,
                    shop_id,
                    date_order,
                    partner_id,
                    user_id,
                    company_id,
                    state,
                    pricelist_id,
                    name,
                    order_policy,
                    partner_invoice_id,
                    partner_shipping_id,
                    invoice_quantity,
                    picking_policy

                    )
                VALUES (
                    'demo_data',
                    '%(shop_id)s',
                    '%(date_order)s',
                    '%(partner_id)s',
                    '%(user_id)s',
                    1,
                    '%(state)s',
                    '%(pricelist_id)s',
                    '%(name)s',
                    'manual',
                    '%(partner_id)s',
                    '%(partner_id)s',
                    'order',
                    'direct'
                );
        """

        SQL_QUERY_LINES = ''

        for i in range(nb_lines):
            product = products[
                self.get_an_int(index + i, nb_object, 0, len(products) - 1)]
            param_lines = {
                'sequence': i,
                'price_unit': product['list_price'],
                'product_uom_qty': min(index + i % 15, index + i % 16) + 1,
                'name_product': product['name'],
                'product_id': product['id']
            }
            SQL_QUERY_LINES += '''
                INSERT INTO sale_order_line (
                    product_uos_qty,
                    product_uom,
                    sequence,
                    order_id,
                    price_unit,
                    product_uom_qty,
                    discount,
                    name,
                    company_id,
                    salesman_id,
                    state,
                    product_id,
                    order_partner_id,
                    invoiced,
                    type,
                    delay
                ) SELECT
                    1,
                    1,
                    %(sequence)s,
                    sor.id,
                    %(price_unit)s,
                    %(product_uom_qty)s,
                    0,
                    '%(name_product)s',
                    company_id,
                    user_id,
                    state,
                    %(product_id)s,
                    partner_id,
                    'f',
                    'make_to_stock',
                    0
                from sale_order sor
                order by sor.id desc limit 1;
            ''' % param_lines

        sql = SQL_QUERY % params + SQL_QUERY_LINES
        return sql
