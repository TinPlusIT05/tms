# -*- encoding: UTF-8 -*-
##############################################################################

from openerp.osv import osv
import logging


class generate_demo_data_res_users_wizard(osv.osv_memory):

    _inherit = "generate.demo.data.wizard"

    '''
        Data Source: http://www.fakenamegenerator.com/
    '''

    def generate_users(self, cr, uid, nb_users):
        logging.info('generate_users: start')
        user_obj = self.pool['res.users']

        user_ids = user_obj.search(cr, uid, [])
        users = user_obj.read(cr, uid, user_ids, ['login'])
        logins = []
        for user in users:
            logins.append(user['login'])

        users = self.get_file_content('people_names_us_3000.csv')

        i = 0
        for user in users:
            i += 1
            if i >= nb_users:
                break

            first = user[2]
            last = user[3]
            login = '%s%s' % (first[0].lower(), last.lower())

            if login in logins:
                logging.info('The user %s already exists' % login)
                continue
            vals = {
                'name': '%s %s' % (first, last),
                'login': login, 'password': 'password',
                'email': user[8],
                'signature': 'trobz_base_demo_data'
            }
            user_obj.create(cr, uid, vals)

        logging.info('generate_users: end')
        return True
