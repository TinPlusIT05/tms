# -*- encoding: UTF-8 -*-
##############################################################################

from openerp.osv import osv
from datetime import timedelta
import logging
from random import choice


class generate_demo_data_booking_resource(osv.TransientModel):

    _inherit = "generate.demo.data.wizard"
    _name = "generate.demo.data.booking.resource.wizard"

    def generate_booking_resource(self, cr, uid, min_date, max_date,
                                  booking_chart_name='Employee Booking Chart'):

        ir_model_obj = self.pool.g['ir.model']
        booking_chart_obj = self.pool['booking.chart']
        booking_resource_obj = self.pool['booking.resource']
        hr_employee_obj = self.pool['hr.employee']

        hr_employee_model_ids = ir_model_obj.search(
            cr, uid, [('model', '=', 'hr.employee')])
        hr_employee_model_id = hr_employee_model_ids and hr_employee_model_ids[
            0] or False

        booking_chart_ids = booking_chart_obj.search(
            cr, uid, [('name', '=', booking_chart_name)])
        booking_chart_id = booking_chart_ids and booking_chart_ids[0] or False
        nb_record = float((max_date - min_date).days) * float(1) / 14

        if not booking_chart_id:
            logging.error(
                'The booking chart %s could not be found' % booking_chart_name)

        custom_attribute_dict = {
            'min_date': min_date,
            'max_date': max_date,
            'booking_chart_id': booking_chart_id,
            'hr_employee_model_id': hr_employee_model_id
        }

        employee_ids = hr_employee_obj.search(cr, uid, [])
        for employee_id in employee_ids:
            custom_attribute_dict['employee_id'] = employee_id
            self.insert_in_batch(
                cr, uid, booking_resource_obj,
                nb_record, custom_attribute_dict)

    def get_sql_insert(self, cr, uid, model_pool, index, nb_object,
                       custom_attribute_dict):

        i = index

        min_date = custom_attribute_dict['min_date']
        max_date = custom_attribute_dict['max_date']
        employee_id = custom_attribute_dict['employee_id']
        booking_chart_id = custom_attribute_dict['booking_chart_id']
        hr_employee_model_id = custom_attribute_dict['hr_employee_model_id']

        color_list = [
            'red', 'orange', 'yellow', 'blue',
            'brown', 'green', 'gray', 'pink']

        date_start = self.get_a_date(
            i * pow(employee_id, 2), nb_object, min_date, max_date)
        duration = self.get_an_int(i * employee_id, nb_object, 1, 15)
        date_end = date_start + timedelta(days=duration)

        params = {
            'name': 'R - ' + str(i),
            'chart': booking_chart_id,
            'resource_id': employee_id,
            'date_start': date_start,
            'date_end': date_end,
            'css_class': choice(color_list),  # random color
            'message': '###',
            # In the reality, it should be something like holidays, meetings
            # ...
            'origin_model': hr_employee_model_id,
            'origin_id': employee_id,
        }

        SQL_QUERY = """
                INSERT INTO booking_resource (
                    name,
                    chart,
                    resource_id,
                    date_start,
                    date_end,
                    css_class,
                    message,
                    origin_model,
                    origin_id)
                VALUES (
                    '%(name)s',
                    '%(chart)s',
                    '%(resource_id)s',
                    '%(date_start)s',
                    '%(date_end)s',
                    '%(css_class)s',
                    '%(message)s',
                    '%(origin_model)s',
                    '%(origin_id)s');
        """
        sql = SQL_QUERY % params

        return sql
