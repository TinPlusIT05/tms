# -*- encoding: UTF-8 -*-
##############################################################################

from openerp.osv import osv
from datetime import date
from openerp import tools
import logging


class generate_demo_data_hr_attendance_wizard(osv.TransientModel):

    _inherit = "generate.demo.data.wizard"
    _name = "generate.demo.data.hr.attendance.wizard"

    def generate_attendances_in_out_by_sql_batch(self,
                                                 cr,
                                                 uid,
                                                 nb_attendance,
                                                 min_date,
                                                 max_date):

        if nb_attendance > 0:
            logging.warning(
                'One attendance is generated for each weekday from the min \
                date to the max date.')
        nb_attendance = (max_date - min_date).days + 1

        logging.info('generate_attendances_in_out: start')

        hr_attendance_obj = self.pool['hr.attendance']
        hr_employee_obj = self.pool['hr.employee']

        custom_attribute_dict = {
            'min_date': min_date,
            'max_date': max_date
        }

        employee_ids = hr_employee_obj.search(cr, uid, [])
        for employee_id in employee_ids:
            custom_attribute_dict['employee_id'] = employee_id
            self.insert_in_batch(
                cr,
                uid,
                hr_attendance_obj,
                nb_attendance,
                custom_attribute_dict)

        logging.info('generate_attendances_in_out: end')

    def get_sql_insert(self, cr, uid, model_pool, index, nb_object,
                       custom_attribute_dict):
        nb_attendance = nb_object
        i = index

        min_date = custom_attribute_dict['min_date']
        max_date = custom_attribute_dict['max_date']
        employee_id = custom_attribute_dict['employee_id']

        date = self.get_a_date(i, nb_attendance, min_date, max_date)

        datetime_in_utc = '%s 2:00:00' % date.strftime(
            tools.misc.DEFAULT_SERVER_DATE_FORMAT)
        datetime_out_utc = '%s 10:00:00' % date.strftime(
            tools.misc.DEFAULT_SERVER_DATE_FORMAT)

        SQL_QUERY = """
                INSERT INTO hr_attendance (name, employee_id, action,day)
                VALUES ('%s', '%s', '%s','%s');
        """

        sql = ''
        sql += SQL_QUERY % (datetime_in_utc, employee_id,
                            'sign_in', datetime_in_utc[0:10])
        sql += SQL_QUERY % (datetime_out_utc, employee_id,
                            'sign_out', datetime_out_utc[0:10])

        return sql

    def generate_attendances_in_out(self, cr, uid, nb_attendance, min_date,
                                    max_date):
        logging.info('generate_attendances_in_out: start')
        hr_attendance_obj = self.pool['hr.attendance']
        hr_employee_obj = self.pool['hr.employee']

        employee_ids = hr_employee_obj.search(cr, uid, [])
        i = 0
        while i < nb_attendance:
            i += 1
            date = self.get_a_date(i, nb_attendance, min_date, max_date)

            datetime_in_utc = '%s 2:00:00' % date.strftime(
                tools.misc.DEFAULT_SERVER_DATE_FORMAT)
            datetime_out_utc = '%s 10:00:00' % date.strftime(
                tools.misc.DEFAULT_SERVER_DATE_FORMAT)

            attendance_ids_in = hr_attendance_obj.search(
                cr, uid, [('name', '=', datetime_in_utc)])
            attendance_ids_out = hr_attendance_obj.search(
                cr, uid, [('name', '=', datetime_out_utc)])

            empoloyee_id = employee_ids[self.get_an_int(i,
                                                        nb_attendance,
                                                        0,
                                                        len(employee_ids))]
            vals = {'name': datetime_in_utc,
                    'empoloyee_id': empoloyee_id}

            if not attendance_ids_in:
                vals.update({'action': 'sign_in'})
                hr_attendance_obj.create(cr, uid, vals)

            if not attendance_ids_out:
                vals.update({'action': 'sign_out'})
                hr_attendance_obj.create(cr, uid, vals)
        logging.info('generate_attendances_in_out: end')
