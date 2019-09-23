from openerp import models
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging


class trobz_hr_employee_image_post_object(models.TransientModel):
    _name = "trobz.hr.employee.image.post.object"

    def run_store_image_file(self, cr, uid, context=None):
        logging.info(
            "====== START: STORING EMPLOYEE IMAGES IN FILE SYSTEM =======")
        if context is None:
            context = {}
        employee_obj = self.pool['hr.employee']
        ids = employee_obj.search(cr, uid, [])

        if not ids:
            return True

        no_of_record = len(ids)
        count = 0
        emps = employee_obj.read(cr, uid, ids, ['image'])
        for emp in emps:
            employee_obj.write(
                cr, uid, [emp['id']],
                {'image_medium': emp['image'],
                 'image_small': emp['image']
                 },
                context=context
            )
            count += 1
            logging.info('>>> STORED file %s/%s' % (count, no_of_record))
            if count % 50 == 0:
                cr.commit()
        cr.commit()

        cr.execute('''
            UPDATE hr_employee SET image = Null;
            ''')

        logging.info(
            "====== END: STORING EMPLOYEE IMAGES IN FILE SYSTEM =======")

        return True
