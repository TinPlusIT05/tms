# -*- encoding: UTF-8 -*-
##############################################################################

from openerp.osv import osv


class generate_demo_data_res_partner_wizard(osv.TransientModel):

    '''
        Data Source: http://www.briandunning.com/sample-data/
    '''

    _inherit = "generate.demo.data.wizard"

    def generate_partners_by_sql_batch(self, cr, uid, nb_partner):

        res_partner_obj = self.pool.get('res.partner')

        partners = self.get_file_content('res_partner_us_500.csv', ',')

        custom_attribute_dict = {'partners': partners}
        self.insert_in_batch(
            cr, uid, res_partner_obj, nb_partner, custom_attribute_dict)
        return True

    def get_sql_insert(self,
                       cr,
                       uid,
                       model_pool,
                       index, nb_object,
                       custom_attribute_dict):

        partner = custom_attribute_dict['partners'][index]
        # FirstName,LastName,Company,Address,City,County,State,ZIP,Phone,Fax,
        # Email,Web
        vals = {
            'contact_name': '%s %s' % (partner[0], partner[1]),
            'name': partner[2],
            'street': partner[3],
            'city': partner[4],
            # I guess the country_ids are always the same. 235 is for USA
            'country': 235,
            # This returns the id of a state in USA
            'state': self.get_an_int(index, 51, 1, 51),
            'zip': partner[7],
            'phone': partner[8],
            'fax': partner[9],
            'email': partner[10],
            'website': partner[11],
        }

        SQL_QUERY = """
        INSERT INTO res_partner
        (name,display_name, street, city, country_id,state_id,zip,phone,fax,
        email,website,is_company,notification_email_send,active,customer)

        VALUES ('%(name)s','%(name)s','%(street)s','%(city)s','%(country)s',
        '%(state)s','%(zip)s','%(phone)s','%(fax)s','%(email)s','%(website)s',
        't','none','t','t');

        INSERT into res_partner
        (parent_id, name,display_name,notification_email_send,is_company,
        use_parent_address,active)

        select max(id),'%(contact_name)s','%(contact_name)s','none','f','t','t'
        from res_partner;
        """

        sql = SQL_QUERY % vals

        return sql
