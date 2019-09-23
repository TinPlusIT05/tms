from openerp import models, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp.tools.safe_eval import safe_eval
from openerp.tools import float_utils
import logging


class tms_modules_post_object(models.TransientModel):
    _name = "tms.modules.post.object"
    _description = "TMS Modules Post Object"

    @api.model
    def monthly_remind_review_emp_email(self):
        logging.info("====== START: MONTHLY REMIND REIVEW EMP EMAIL =======")

        ir_cron = self.env['ir.cron']
        base = self.env['trobz.base']

        ir_cron_recs = ir_cron.search(
            [('model', '=', 'hr.contract'),
             ('function', '=',
              'send_email_hr_manager_remind_review_emp'),
             '|', ('active', '=', True), ('active', '=', False)],
        ) or False
        now = datetime.now().date()
        first_date_of_next_month = (
            now + relativedelta(day=0, months=1, days=0)).replace(day=1)
        str_fdate_next_month = datetime.strftime(first_date_of_next_month,
                                                 '%Y-%m-%d') + ' 00:00:00'
        fdate_next_month = base.convert_from_current_timezone_to_utc(
            str_fdate_next_month, get_str=False)

        if not ir_cron_recs:
            value = {
                'name': 'Monthly Remind Review Performance of Employee to'
                'HR Manager',
                'interval_number': 1,
                'interval_type': 'months',
                'nextcall': fdate_next_month,
                'numbercall': 1,
                'active': True,
                'doall': True,
                'model': 'hr.contract',
                'function': 'send_email_hr_manager_remind_review_emp'
            }
            ir_cron.create(value)

        logging.info("====== END: MONTHLY REMIND REIVEW EMP EMAIL =======")

    @api.model
    def update_timezone_for_host(self):
        logging.info(
            "====== START: UPDATE TIMEZONE FOR TMS HOST =======")
        tms_host_rec = self.env['tms.host'].search([])
        for host_rec in tms_host_rec:
            temp = host_rec.config.copy()
            node_add = host_rec.physical_host_id and \
                host_rec.physical_host_id.host_address or False
            if node_add:
                if 'eu' in node_add:
                    temp['timezone'] = 'Europe/Berlin'
                    host_rec.config = temp
                else:
                    temp['timezone'] = 'Asia/Ho_Chi_Minh'
                    host_rec.config = temp
        logging.info("====== END: UPDATE TIMEZONE FOR TMS HOST =======")
        return True

    @api.model
    def update_company_id(self):
        logging.info("====== START: UPDATE COMPANY_ID FOR THE WEBSITE =======")
        sql = '''
            update website set company_id = 1
            where id = 1
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE COMPANY_ID FOR THE WEBSITE =======")
        return True

    @api.model
    def update_is_trobz_member(self):
        logging.info(
            "====== START: UPDATE IS_TROBZ_MEMBER FOR THE USERS =======")
        for user in self.env['res.users'].search([]):
            group_user = self.env.ref('base.group_user')
            profile_ids = group_user.profile_ids and \
                group_user.profile_ids.ids or False
            user.is_trobz_member = True if (
                profile_ids and user.group_profile_id and
                user.group_profile_id.id in profile_ids) else False
        logging.info(
            "====== END: UPDATE IS_TROBZ_MEMBER FOR THE USERS =======")
        return True

    @api.model
    def update_employee_id(self):
        logging.info(
            "====== START: UPDATE WH > EMPLOYEE_ID =======")
        working_hours = self.env['tms.working.hour'].search([])
        employee_obj = self.env['hr.employee']
        for wh in working_hours:
            if not wh.employee_id or \
                    (wh.employee_id and
                     wh.user_id.id != wh.employee_id.user_id.id):
                employee = employee_obj.search(
                    [('user_id', '=', wh.user_id.id)])
                wh.employee_id = employee and employee.id or False
        logging.info("====== END: UPDATE WH > EMPLOYEE_ID =======")
        return True

    @api.model
    def update_partner_computed_id(self):
        logging.info("====== START: UPDATE WH > PARTNER COMPUTED =======")
        contract_obj = self.env['hr.dedicated.resource.contract']
        working_hours = self.env['tms.working.hour'].search([])
        for wh in working_hours:
            contract = contract_obj.search(
                [('employee_id.user_id', '=', wh.user_id.id),
                 ('start_date', '<=', wh.date),
                 '|', ('end_date', '=', False),
                 ('end_date', '>=', wh.date)], order='start_date DESC'
            )
            if contract:
                wh.partner_computed_id = contract[0].name and \
                    contract[0].name.id or False
            else:
                wh.partner_computed_id = wh.project_id and \
                    wh.project_id.trobz_partner_id and \
                    wh.project_id.trobz_partner_id.id or False
        logging.info("====== END: UPDATE WH > PARTNER COMPUTED =======")
        return True

    @api.model
    def update_calendar_event_global(self):
        logging.info(
            "====== START: UPDATE CALENDAR_EVENT_GLOBAL =====")
        sql = '''
            UPDATE ir_rule SET active=False WHERE name='Hide Private Meetings';
        '''
        self._cr.execute(sql)
        logging.info(
            "====== END: UPDATE CALENDAR_EVENT_GLOBAL =======")
        return True

    @api.model
    def update_milestone_number(self):
        logging.info(
            "====== START: UPDATE MILESTONE_NUMBER FOR THE WEBSITE =======")
        sql = '''
            UPDATE tms_support_ticket SET milestone_number =
            (SELECT number FROM tms_milestone
            WHERE id = tms_support_ticket.milestone_id)
        '''
        self._cr.execute(sql)
        logging.info(
            "====== END: UPDATE MILESTONE_NUMBER FOR THE WEBSITE =======")
        return True

    @api.model
    def update_wrong_workload_support_ticket(self):
        logging.info(
            "====== START: UPDATE WRONG WORKLOAD FOR TMS SUPPORT TICKET =====")
        sql = '''
            UPDATE tms_support_ticket SET workload =
            CAST(workload_char as numeric)
            WHERE workload != CAST(workload_char AS numeric)
        '''
        self._cr.execute(sql)
        logging.info(
            "====== END: UPDATE WRONG WORKLOAD FOR TMS SUPPORT TICKET ======")
        return True

    @api.model
    def remove_subscriber_admin_on_support_tickets(self):
        logging.info("====== START: DELETE SUBSCRIBER WHEN UID IS "
                     "ADMINISTRATOR  =======")
        sql = '''
            DELETE FROM tms_support_ticket_subscriber_rel
            WHERE subscriber_id =1
        '''
        self._cr.execute(sql)
        logging.info("====== END: DELETE SUBSCRIBER WHEN UID IS "
                     "ADMINISTRATOR  =======")
        return True

    @api.model
    def notification_preferences_inital_data(self):
        logging.info(
            "====== START: Create Notification Preferences Data =======")

        notif = self.env['notification.preferences']
        model_field = self.env['ir.model.fields']

        datas = [{'name': 'Receive all',
                  'use_by_subscribe_me': True,
                  'receive_notif_for_my_action': True,
                  'forge_fields': ['summary',
                                   'description',
                                   'tms_forge_ticket_comment_ids',
                                   'reporter_id',
                                   'project_id',
                                   'milestone_id',
                                   'ticket_sprint_id',
                                   'tms_activity_id',
                                   'state',
                                   'priority',
                                   'development_time',
                                   'owner_id',
                                   'resolution'],
                  'support_fields': ['tms_activity_id',
                                     'summary',
                                     'description',
                                     'tms_support_ticket_comment_ids',
                                     'reporter_id',
                                     'milestone_id',
                                     'state',
                                     'priority',
                                     'workload',
                                     'owner_id',
                                     'ticket_type',
                                     'resolution',
                                     'quotation_approved']},
                 {'name': 'Receive only most important',
                  'use_by_subscribe_me': False,
                  'forge_fields': ['summary',
                                   'description',
                                   'project_id',
                                   'state',
                                   'development_time',
                                   'owner_id',
                                   'resolution'],
                  'support_fields': ['summary',
                                     'description',
                                     'state',
                                     'priority',
                                     'owner_id',
                                     'ticket_type',
                                     'quotation_approved']},
                 {'name': 'Minimal',
                  'use_by_subscribe_me': False,
                  'forge_fields': [],
                  'support_fields': []},
                 ]

        for data in datas:
            forge_fields = data['forge_fields'] or []
            support_fields = data['support_fields'] or []
            forge_field_ids = []
            support_field_ids = []

            if forge_fields:
                forge_field_ids = model_field.search(
                    [('name', 'in', forge_fields),
                     ('model', '=', 'tms.forge.ticket')]).ids

            if support_fields:
                support_field_ids = model_field.search(
                    [('name', 'in', support_fields),
                     ('model', '=', 'tms.support.ticket')]).ids
            value = {
                'name': data['name'],
                'use_by_subscribe_me': data['use_by_subscribe_me'],
                'forge_field_ids': [[6, False, forge_field_ids]],
                'support_field_ids': [[6, False, support_field_ids]],
            }
            notif.create(value)

        logging.info(
            "====== END: Create Notification Preferences Data  =======")

    @api.model
    def set_notification_preferences_per_profiles(self):
        logging.info(
            "====== START:set_notification_preferences_per_profiles =======")

        notif_env = self.env['notification.preferences']
        res_group_env = self.env['res.groups']

        datas = [('Minimal', ['Admin Profile']),
                 ('Receive all',
                  ['FC and Admin Profile', 'FC+CRM Profile',
                   'Functional Consultant Profile', 'QC Profile',
                   'Technical Consultant Profile',
                   'Technical Project Manager Profile',
                   'TMS Partner Profile']),
                 ('Receive only most important',
                  ['TMS Customer Profile',
                   'TMS Customer Reporter Only Profile',
                   'TMS Customer Viewer Profile'])]

        for data in datas:
            n_name = data[0]
            g_name = data[1]
            notifs = notif_env.search([('name', '=', n_name)])
            notif_id = notifs and notifs.ids[0] or False
            if notif_id:
                res_groups = res_group_env.search([('name', 'in', g_name)])
                res_groups.write({'notif_pref_id': notif_id})

        logging.info(
            "====== END:set_notification_preferences_per_profiles =======")

    @api.model
    def migrate_project_notification_preferences(self):
        logging.info(
            "====== START:migrate_project_notification_preferences =======")
        # Delete wrong subscribers created from this wrong script
        self.env.cr.execute("DELETE FROM project_subscriber;")
        sql = '''
            SELECT tms_project_id, subscriber_id
            FROM tms_project_support_subscriber_rel
            WHERE subscriber_id NOT IN
                (SELECT id FROM res_users WHERE active = FALSE)
            GROUP BY tms_project_id, subscriber_id
        '''
        self.env.cr.execute(sql)
        datas = self.env.cr.fetchall()

        subscriber_env = self.env['project.subscriber']
        for data in datas:
            project_id = data[0]
            user_id = data[1]
            logging.info(
                '====== project %s, subscriber%s' % (project_id, user_id))
            # Calculate the notif_pref_id
            user = self.env['res.users'].browse(user_id)
            notif_id = False
            if user.notif_pref_id:
                # The Notification Preference of the User
                notif_id = user.notif_pref_id.id
            elif user.group_profile_id and \
                    user.group_profile_id.notif_pref_id:
                # The Notification Preference of the Profile
                notif_id = user.group_profile_id.notif_pref_id.id
            # Create project subscriber
            subscriber_env.create(
                {'name': user_id,
                 'tms_project_id': project_id,
                 'notif_pref_id': notif_id})
        logging.info(
            "====== END: migrate_project_notification_preferences =======")

    @api.model
    def migrate_forge_ticket_notification_preferences(self):
        logging.info(
            "====== START:migrate_forge_ticket_notification_preferences ====")
        sql = '''
            SELECT tms_forge_ticket_id, subscriber_id
            FROM tms_forge_ticket_subscriber_rel WHERE subscriber_id NOT IN
            (SELECT id FROM res_users WHERE active = FALSE)
            GROUP BY tms_forge_ticket_id, subscriber_id
        '''
        self.env.cr.execute(sql)
        datas = self.env.cr.fetchall()

        tms_subscriber_env = self.env['tms.subscriber']
        for data in datas:
            forge_id = data[0]
            user_id = data[1]
            tms_subscriber_env.create({'name': user_id,
                                       'forge_id': forge_id})
        logging.info(
            "====== END:migrate_forge_ticket_notification_preferences =====")

    @api.model
    def migrate_support_ticket_notification_preferences(self):
        logging.info(
            "====== START:migrate_support_ticket_notification_preferences ===")
        sql = '''
            SELECT tms_support_ticket_id, subscriber_id
            FROM tms_support_ticket_subscriber_rel WHERE subscriber_id NOT IN
            (SELECT id FROM res_users WHERE active = FALSE)
            GROUP BY tms_support_ticket_id, subscriber_id
        '''
        self.env.cr.execute(sql)
        datas = self.env.cr.fetchall()

        tms_subscriber_env = self.env['tms.subscriber']
        for data in datas:
            support_id = data[0]
            user_id = data[1]
            tms_subscriber_env.create({'name': user_id,
                                       'support_id': support_id})
        logging.info(
            "====== END:migrate_support_ticket_notification_preferences ===")

    # F#13298 - remove invalid subscribers in support ticket
    @api.model
    def remove_invalid_subscribers_in_support_ticket(self):
        """
        Remove subscribers not defined in the supporters for:
        - Default subscribers of project
        - Subscribers of support ticket
        """
        logging.info("====== START: REMOVE INVALID SUBSCRIBERS =======")
        # Delete invalid subscribers of ticket
        invalid_subscribers_sql = """
        DELETE FROM tms_subscriber ts
        WHERE ts.name NOT IN (
            SELECT rel.user_id from tms_project_supporter_rel rel
            WHERE rel.project_id = (
                SELECT project_id
                FROM tms_support_ticket ti
                WHERE ti.id = ts.support_id
            )
        );
        DELETE FROM project_subscriber ps
        WHERE name NOT IN (
            SELECT user_id FROM tms_project_supporter_rel
            WHERE project_id = ps.tms_project_id
        );
        """
        # Delete invalid default subscribers of project
        self._cr.execute(invalid_subscribers_sql)
        logging.info("====== START: REMOVE INVALID SUBSCRIBERS =======")

    @api.model
    def fix_action_id(self):
        """
        281: ACTION_ID OF "Support Tickets" --> don't need
        284: ACTION_ID OF "Support Tickets"

        283: ACTION_ID OF "Trobz Support Tickets"

        193: ACTION_ID OF "Leads" --> don't need
        184: ACTION_ID OF "Leads"

        259: ACTION_ID OF "Forge Tickets" --> don't need
        257: ACTION_ID OF "Forge Tickets"

        196: ACTION_ID OF "Opportunities Analysis" --> don't need
        187: ACTION_ID OF "Opportunities Analysis"

        244: ACTION_ID OF "My Open Leads"
        293: ACTION_ID OF "Working Hours"
        261: ACTION_ID OF "My Tickets in this sprint"

        """

        logging.info("====== START: UPDATE ACTION_ID FROM DATABASE ======")

        sql = '''
            DELETE FROM ir_actions WHERE id = 281;
            DELETE FROM ir_actions WHERE id = 193;
            DELETE FROM ir_actions WHERE id = 259;
            DELETE FROM ir_actions WHERE id = 196;


            UPDATE res_groups SET action_id = 284
            WHERE name IN ('TMS Customer', 'TMS Customer Profile',
            'TMS Customer Reporter Only Profile',
            'TMS Customer Viewer', 'TMS Customer Viewer Profile',
            'TMS Partner Profile');

            UPDATE res_groups SET action_id = 283
            WHERE name IN ('Admin Profile', 'FC and Admin Profile',
            'Functional Consultant Profile');

            UPDATE res_groups SET action_id = 293
            WHERE name IN ('Employee Profile');

            UPDATE res_groups SET action_id = 244
            WHERE name IN ('FC+CRM Profile');

            UPDATE res_groups SET action_id = 261
            WHERE name IN ('Technical Consultant Profile');

            UPDATE res_groups SET action_id = 257
            WHERE name IN ('QC Profile', 'Technical Project Manager Profile');

            UPDATE res_users SET action_id = 284
            WHERE group_profile_id IN
            (SELECT id FROM res_groups WHERE name IN
            ('TMS Customer', 'TMS Customer Profile',
            'TMS Customer Reporter Only Profile',
            'TMS Customer Viewer', 'TMS Customer Viewer Profile',
            'TMS Partner Profile'));

            UPDATE res_users SET action_id = 244
            WHERE group_profile_id IN
            (SELECT id FROM res_groups WHERE name IN ('FC+CRM Profile'));
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE ACTION_ID FROM DATABASE ======")
        return True

    @api.model
    def update_forge_ticket_ids(self):
        logging.info("====== START: UPDATE FORGE TICKET IDS =======")
        sql = '''
            UPDATE tms_forge_ticket
            SET name = id;
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE FORGE TICKET IDS =======")
        return True

    @api.model
    def update_support_ticket_ids(self):
        logging.info("====== START: UPDATE SUPPORT TICKET IDS =======")
        sql = '''
            UPDATE tms_support_ticket
            SET name = id;
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE SUPPORT TICKET IDS =======")
        return True

    @api.model
    def fix_wrong_period_allocation_request(self):
        logging.info("====== START: FIX WRONG PERIOD ALLOCATION REQUEST =====")
        hr_holidays_obj = self.env['hr.holidays']
        hot_fix_datas = [('177', '10/2013'), ('178', '10/2013'),
                         ('398', '09/2013'), ('171', '09/2013'),
                         ('180', '09/2013'), ('87', '05/2013'),
                         ('58', '06/2013'), ('167', '08/2013'),
                         ('172', '05/2013'), ('17', '02/2013'),
                         ('269', '10/2013'), ('57', '12/2013'),
                         ('336', '01/2013'), ('214', '08/2013'),
                         ('401', '11/2013'), ('126', '08/2013'),
                         ('256', '10/2013'), ('402', '09/2013'),
                         ('400', '09/2013'), ('254', '07/2013'),
                         ('38', '07/2013'), ('60', '09/2013'),
                         ('56', '05/2013'), ('113', '10/2013'),
                         ('12', '11/2013'), ('148', '10/2013'),
                         ('39', '03/2013'), ('271', '10/2013'),
                         ('274', '12/2013'), ('122', '07/2013'),
                         ('41', '10/2013'), ('258', '09/2013'),
                         ('344', '10/2013'), ('173', '10/2013'),
                         ('10', '01/2013'), ('83', '08/2013'),
                         ('127', '08/2013'), ('119', '04/2013'),
                         ('349', '08/2013'), ('53', '02/2013'),
                         ('19', '01/2013'), ('355', '02/2013'),
                         ('42', '04/2013'), ('37', '03/2013'),
                         ('361', '05/2013'), ('346', '07/2013'),
                         ('264', '07/2013'), ('88', '09/2013'),
                         ('21', '04/2013'), ('118', '08/2013'),
                         ('120', '06/2013'), ('59', '10/2013'),
                         ('22', '07/2013'), ('114', '06/2013'),
                         ('759', '05/2014'), ('27', '04/2013'),
                         ('40', '01/2013'), ('86', '02/2013'),
                         ('124', '06/2013'), ('255', '06/2013'),
                         ('207', '08/2013'), ('89', '08/2013'),
                         ('357', '02/2013'), ('340', '04/2013'),
                         ('341', '04/2013'), ('165', '04/2013'),
                         ('84', '08/2013'), ('166', '09/2013'),
                         ('203', '05/2013'), ('337', '10/2013'),
                         ('36', '05/2013'), ('216', '09/2013'),
                         ('121', '06/2013'), ('26', '06/2013'),
                         ('405', '11/2013'), ('170', '07/2013'),
                         ('115', '10/2013'), ('25', '04/2013'),
                         ('116', '07/2013'), ('11', '03/2013'),
                         ('266', '09/2013'), ('335', '10/2013'),
                         ('345', '07/2013'), ('403', '09/2013'),
                         ('204', '05/2013'), ('28', '11/2013'),
                         ('169', '07/2013'), ('360', '10/2013'),
                         ('205', '09/2013'), ('348', '08/2013'),
                         ('9', '09/2013'), ('206', '03/2013'),
                         ('240', '09/2013'), ('218', '10/2013'),
                         ('210', '08/2013'), ('267', '09/2013'),
                         ('406', '10/2013'), ('351', '10/2013'),
                         ('215', '09/2013'), ('261', '07/2013'),
                         ('100', '07/2013'), ('208', '08/2013'),
                         ('260', '07/2013'), ('342', '06/2013'),
                         ('181', '10/2013'), ('347', '07/2013'),
                         ('85', '05/2013'), ('20', '01/2013'),
                         ('265', '09/2013'), ('350', '09/2013'),
                         ('960', '07/2014'), ('961', '07/2014'),
                         ('986', '10/2014'), ('987', '10/2014'),
                         ('988', '10/2014'), ('989', '10/2014'),
                         ('990', '10/2014'), ('991', '10/2014'),
                         ('992', '10/2014'), ('993', '10/2014'),
                         ('994', '10/2014'), ('995', '10/2014'),
                         ('996', '10/2014'), ('997', '10/2014'),
                         ('998', '10/2014'), ('999', '10/2014'),
                         ('1000', '10/2014'), ('1001', '10/2014'),
                         ('1002', '10/2014'), ('1003', '10/2014'),
                         ('1004', '10/2014'), ('1005', '10/2014'),
                         ('1006', '10/2014'), ('1033', '10/2014'),
                         ('1068', '10/2014'), ('1069', '11/2014'),
                         ('1070', '11/2014'), ('1073', '10/2014'),
                         ('1074', '10/2014'), ('1075', '10/2014'),
                         ('1076', '10/2014'), ('1077', '11/2014'),
                         ('1079', '08/2014'), ('1271', '02/2015'),
                         ('376', '12/2013')]
        for data in hot_fix_datas:
            hot_fix_holiday_id = data[0]
            hot_fix_month_year = data[1]
            holiday = hr_holidays_obj.search([('id', '=', hot_fix_holiday_id)])
            if holiday and holiday.month_year != hot_fix_month_year:
                holiday.month_year = hot_fix_month_year
        logging.info("====== END: FIX WRONG PERIOD ALLOCATION REQUEST ======")
        return True

    @api.model
    def remove_wizard_merge_convert_oppotunity(self):
        self.env.ref('crm.action_merge_opportunities').unlink()
        self.env.ref('crm.action_crm_send_mass_convert').unlink()

    @api.model
    def implied_mailman_unsubscribe_me_to_group_user(self):
        logging.info("====== START: "
                     "implied_mailman_unsubscribe_me_to_group_user =======")
        group_user = self.env.ref('base.group_user')
        group_mailman_unsubscribe_me = \
            self.env.ref('tms_modules.group_tms_mailman_unsubsribe_me')
        if group_mailman_unsubscribe_me:
            current_implied_ids = group_user.implied_ids.ids
            current_implied_ids.append(group_mailman_unsubscribe_me.id)
            group_user.implied_ids = [(6, 0, current_implied_ids)]
        logging.info("====== END:"
                     "implied_mailman_unsubscribe_me_to_group_user =======")
        return True

    @api.model
    def update_sysadmin_access_users(self):
        logging.info("=== START: update sysadmin access on users ===")
        update_sql = """
            UPDATE res_users rus
            SET is_sysadmin = True
            WHERE active = True
                AND EXISTS (
                    SELECT 1
                    FROM res_groups rgr
                    WHERE rgr.is_sysadmin = True
                        AND rgr.id = rus.group_profile_id
                );
            UPDATE res_users rus
            SET has_full_sysadmin_access = True
            WHERE active = True
                AND group_profile_id IN (
                    SELECT id
                    FROM res_groups
                    WHERE name = 'Admin Profile'
                        AND is_profile = True
                );
            UPDATE res_users
            SET is_sysadmin = True
                AND has_full_sysadmin_access = True
            WHERE id = 1;
        """
        self._cr.execute(update_sql)
        logging.info("=== END: update sysadmin access on users ===")
        return True

    @api.model
    def update_sysadmin_profile(self):
        logging.info("=== START: update sysadmin profile ===")
        # Notification Preference
        noti_obj = self.env['notification.preferences']
        noti_rec = noti_obj.search([('name', '=', 'Minimal')],
                                   limit=1, order='id')
        if not noti_rec:
            logging.warning('Cannot find the Minimal notification preference!')
            noti_rec = False
        # Home Action
        act_window = self.env.ref('tms_modules.action_view_tms_instance')
        if not act_window:
            logging.warning('Cannot find the Instance (OpenERP) menu!')
            act_window = False
        # Update sysadmin profile
        sysadmin_prof = self.env.ref('tms_modules.group_profile_tms_sysadmin')
        if not sysadmin_prof:
            logging.error('Cannot find the Sysadmin profile!')
            return False
        sysadmin_prof.write({
            'notif_pref_id': noti_rec and noti_rec.id or False,
            'action_id': act_window and act_window.id or False
        })
        logging.info("=== END: update sysadmin profile ===")
        return True

    @api.model
    def update_tms_activity(self):
        logging.info("====== START: UPDATE CODE IN TMS_ACTIVITY =======")

        update_sql = '''
            UPDATE tms_activity ts SET code = p.name || ' - ' || ts.name
            FROM tms_project p where p.id = ts.project_id;
        '''
        self._cr.execute(update_sql)
        logging.info("====== END: UPDATE CODE IN TMS_ACTIVITY =======")
        return True

    @api.model
    def update_functional_block_for_tickets_uma7_and_delete_functional_block(
            self):
        logging.info("====== START: "
                     "update_functional_block_for_tickets_uma7"
                     "_and_delete_functional_block =======")

        functional_block_find = False
        functional_block_replace = False

        tms_functional_block_obj = self.env['tms.functional.block']
        tms_forge_ticket_obj = self.env['tms.forge.ticket']
        tms_support_ticket_obj = self.env['tms.support.ticket']

        project_uma7 = self.env['tms.project'].search([('name', '=', 'uma7')])
        if not project_uma7:
            return True
        functional_blocks = tms_functional_block_obj.search(
            [('name', '=', 'HR')])
        if not functional_blocks:
            return True
        for x in functional_blocks:
            if len(x.project_ids) == 1:
                functional_block_find = x
            if len(x.project_ids) > 1:
                functional_block_replace = x
        uma7_forge_tickets = tms_forge_ticket_obj.search(
            [('tms_functional_block_id', '=', functional_block_find.id),
             ('project_id', '=', project_uma7.id)])
        uma7_forge_tickets.write(
            {'tms_functional_block_id': functional_block_replace.id})

        uma7_support_tickets = tms_support_ticket_obj.search(
            [('tms_functional_block_id', '=', functional_block_find.id),
             ('project_id', '=', project_uma7.id)])
        uma7_support_tickets.write(
            {'tms_functional_block_id': functional_block_replace.id})

        functional_block_find.unlink()

        logging.info("====== END:"
                     "update_functional_block_for_tickets_uma7"
                     "_and_delete_functional_block =======")

    @api.model
    def function_update_working_hours_require_ticket(self):
        logging.info('====START Update Working Hour Require Ticket ====')
        sql = """
            UPDATE res_groups SET wh_tickets_required = FALSE
            WHERE is_profile = TRUE
            AND NAME IN ('Admin Profile', 'FC and Admin Profile',
                'FC+CRM Profile', 'Functional Consultant Profile',
                'Team Manager Profile');
            UPDATE res_groups SET wh_tickets_required = TRUE
            WHERE is_profile = TRUE
            AND NAME NOT IN ('Admin Profile', 'FC and Admin Profile',
                'FC+CRM Profile', 'Functional Consultant Profile',
                'Team Manager Profile');
        """
        self._cr.execute(sql)
        logging.info('====END Update Working Hour Require Ticket ====')
        return True

    @api.model
    def function_update_active_tms_activity(self):
        logging.info('====START Update Active TMS Activity ====')
        sql = """
            UPDATE tms_activity SET active = FALSE
            WHERE state IN ('closed', 'canceled')
        """
        self._cr.execute(sql)
        logging.info('====END Update Active TMS Activity ====')
        return True

    def install_translation_po_files(self, cr, uid):
        """
        Load and install po files in the directory i18n
        """
        trobz_base_object = self.pool.get('trobz.base')
        module_name = 'tms_modules'
        config = {'fr_FR': [
            'fr.po',
        ]
        }
        trobz_base_object.install_translation_po_files(
            cr, uid, module_name, config)
        return True

    @api.model
    def update_is_forget_ticket_status(self):
        logging.info(
            "====== START: UPDATE STATUS FOR FORGE TICKET =======")
        sql = '''
            update tms_forge_ticket set state = 'wip'
            where state='accepted';
        '''
        self._cr.execute(sql)
        logging.info(
            "====== END: UPDATE UPDATE STATUS FOR FORGE TICKET =======")

    @api.model
    def update_resolution_for_missing_comment(self):
        logging.info("==== START: UPDATE RESOLUTION FOR MISSING COMMENT ====")
        sql = '''
            SELECT ttc.*, tft.resolution AS forge, tst.resolution AS support
            FROM
                (SELECT id, comment, tms_forge_ticket_id, tms_support_ticket_id
                FROM tms_ticket_comment
                WHERE comment ILIKE '%Status%=> Closed,%'
                    AND comment NOT ILIKE '%Resolution%') AS ttc
                LEFT JOIN tms_forge_ticket AS tft
                    ON ttc.tms_forge_ticket_id = tft.id
                LEFT JOIN tms_support_ticket AS tst
                    ON ttc.tms_support_ticket_id = tst.id
            WHERE tft.state = 'closed' OR tst.state = 'closed'
            ORDER BY ttc.tms_forge_ticket_id, ttc.tms_support_ticket_id
        '''
        self._cr.execute(sql)
        datas = self.env.cr.fetchall()
        for data in datas:
            message = data[1]
            if data[2] and not data[3]:
                message += '\n\t field Resolution: Empty => %s, ' % (data[4])
            elif data[3] and not data[2]:
                message += '\n\t field Resolution: Empty => %s, ' % (data[5])
            else:
                continue

            sql = '''UPDATE tms_ticket_comment
                    SET comment= '%s' WHERE id =%s''' % (message, data[0])
            self._cr.execute(sql)

        logging.info("==== END: UPDATE RESOLUTION FOR MISSING COMMENT ====")

        return True

    # F#12640
    @api.model
    def function_update_use_parent_address(self):
        logging.info('====START Update use_parent_address ====')
        sql = """
            UPDATE res_partner SET use_parent_address = True
            WHERE type = 'contact' AND is_company = False;
        """
        self._cr.execute(sql)
        logging.info('====END Update use_parent_address ====')
        return True

    # F#13206
    @api.model
    def update_employer_for_existed_partners(self):
        logging.info(
            '====START Update employer for all partners of existing users ===')

        users = self.env['res.users'].search([('partner_id', '!=', False)])
        for user in users:
            if not user.partner_id.parent_id and user.employer_id:
                user.partner_id.parent_id = user.employer_id.id
        logging.info(
            '====END Update employer for all partners of existing users ====')
        return True

    @api.model
    def update_group_sale_salesman(self):
        logging.info("====== START: UPDATE GROUP_SALE_SALESMAN =======")
        sql = """
            UPDATE ir_model_data
            SET noupdate = False
            WHERE model= 'res.groups' AND res_id = %s
            """ % self.env.ref('base.group_sale_salesman').id
        self._cr.execute(sql)
        logging.info("====== END: UPDATE GROUP_SALE_SALESMAN =======")
        return True

    @api.model
    def update_number_of_days_request_leaves(self):
        logging.info("==== START: UPDATE NUMBER OF DAYS REQUEST LEAVES ====")
        sql = """
            UPDATE hr_holidays hr
            SET number_of_days_temp = (Select SUM(number_of_days)
                                        From hr_holidays_line hhl
                                        where hr.id=hhl.holiday_id)
            WHERE type = 'remove'
            """
        self._cr.execute(sql)
        logging.info("==== END: UPDATE NUMBER OF DAYS REQUEST LEAVES ====")
        return True

    @api.model
    def update_allocation_request(self):
        logging.info(
            "====== START: UPDATE ALLOCATION REQUEST =======")

        sql = """
            SELECT id
            FROM hr_holidays
            WHERE month_year notnull
                AND month_year != concat(
                    LPAD(date_part('month', allo_date)::TEXT, 2, '0'), '/',
                    date_part('year', allo_date))
                AND type = 'add'
            """
        self.env.cr.execute(sql)
        datas = self.env.cr.fetchall()
        for data in datas:
            allo_obj = self.env['hr.holidays'].search([('id', '=', data[0])])

            allo_obj.allo_date = datetime.strptime(
                '01/' + allo_obj.month_year, "%d/%m/%Y").date()

        logging.info(
            "====== END: UPDATE ALLOCATION REQUEST =======")
        return True

    @api.model
    def function_update_extra_annual_leaves(self):
        logging.info("====== START: update_date_end_of_conflict_contract")
        sql = """
            update hr_job
            SET extra_annual_leaves_for_work_seniority = 0.5,
            work_seniority_interval = 1;
        """
        self._cr.execute(sql)
        logging.info("====== END: update_date_end_of_conflict_contract")
        return True

    @api.model
    def function_remove_duplicate_leave_type(self):
        logging.info("===== START: REMOVE DUPLICATE LEAVE TYPE =====")
        hr_holidays_line_obj = self.env['hr.holidays.line']
        sql = """
          SELECT res_id
          FROM ir_model_data
          WHERE model = 'hr.holidays.status'
        """
        self._cr.execute(sql)
        status_mdata_ids = [status_id[0] for status_id in self._cr.fetchall()]
        duplicate_holidays_status = self.search(
            [('id', 'not in', status_mdata_ids)])
        if duplicate_holidays_status:
            bearing_holidays_lines = hr_holidays_line_obj.search(
                [('holiday_status_id', 'in', duplicate_holidays_status.ids)])
            for bearing_holidays_line in bearing_holidays_lines:
                duplicate_holidays_status_name = \
                    bearing_holidays_line.holiday_status_id.name
                holidays_status_id = self.search(
                    [('name', '=', duplicate_holidays_status_name),
                     ('id', 'not in', duplicate_holidays_status.ids)])
                if holidays_status_id:
                    bearing_holidays_line.write(
                        {'holiday_status_id': holidays_status_id.id})
            duplicate_holidays_status.unlink()
        logging.info("===== END: REMOVE DUPLICATE LEAVE TYPE =====")
        return True

    @api.model
    def function_update_hire_date(self):
        logging.info("====== START: function_update_hire_date =======")
        contracts = self.search([])
        for contract in contracts:
            contract.write({'is_trial': contract.is_trial})
        logging.info("====== END: function_update_hire_date =======")
        return True

    @api.model
    def function_update_leave_manager(self):
        logging.info("===== START: function_update_leave_manager =====")
        self._cr.execute("""
            UPDATE hr_employee SET leave_manager_id = parent_id
                WHERE parent_id IS NOT NULL
                    AND leave_manager_id IS NULL
            """)
        logging.info("===== END: function_update_leave_manager =====")
        return True

    @api.model
    def function_update_monthly_paid_leaves(self):
        """
        Function to update monthly paid leaves
        for any contracts which monthly paid leaves are not set
        """
        logging.info("====== START: function_update_hire_date =======")
        self._cr.execute("""
        UPDATE hr_contract set monthly_paid_leaves =1
        WHERE id IN (SELECT con.id
            FROM hr_contract con
                JOIN hr_employee emp ON emp.id = con.employee_id
                JOIN resource_resource res ON res.id = emp.resource_id
            WHERE monthly_paid_leaves IS NULL
                AND is_trial=False
                AND res.active=True
            )""")
        logging.info("====== END: function_update_hire_date =======")
        return True

    @api.model
    def function_update_date_end_of_conflict_contract(self):
        """
        Function to update date end of conflict contracts (Contracts are
        overlapped)
        """
        logging.info("=== START: function_update_date_end_of_conflict_contract"
                     "===")
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        employees = employee_obj.search([])
        for employee in employees:
            contract_id = employee.contract_id.id
            contracts = contract_obj.search([
                ('date_end', '=', False),
                ('id', '!=', contract_id),
                ('is_trial', '=', False),
                ('employee_id', '=', employee.id)])
            date_start_latest_contract = \
                employee.contract_id.date_start and \
                datetime.strptime(employee.contract_id.date_start,
                                  '%Y-%m-%d') or False
            if contracts and date_start_latest_contract:
                vals = {
                    'date_end': date_start_latest_contract - timedelta(days=1)
                }
                contracts.write(vals)
        logging.info("=== END: function_update_date_end_of_conflict_contract"
                     "===")
        return True

    @api.model
    def function_update_login_for_contract(self):
        """
        update login information for each contract missing this value
        """
        sql = """
            UPDATE hr_contract SET login=(
              SELECT rus.login
                FROM hr_contract hrc
                  JOIN hr_employee hre ON hre.id = hrc.employee_id
                  JOIN resource_resource rr ON rr.id = hre.resource_id
                  JOIN res_users rus ON rus.id = rr.user_id
              WHERE hr_contract.id = hrc.id
            )
        """
        self._cr.execute(sql)
        return True

    @api.model
    def function_update_login_for_employee(self):
        """
        update login information for each employee missing this value
        """
        sql = """
            UPDATE hr_employee SET login=(
              SELECT rus.login
                FROM hr_employee hre
                  JOIN resource_resource rr ON rr.id = hre.resource_id
                  JOIN res_users rus ON rus.id = rr.user_id
              WHERE hre.id = hr_employee.id
            )
        """
        self._cr.execute(sql)
        return True

    @api.model
    def function_update_custom_params_data(self):
        """
        Update custom params data on instance to adapt the Json parser
        + Change True/False -> true/false
        + Change single quote to double quote
        """
        logging.info("=== START: UPDATE Custom Params on instance")
        sql = """
        UPDATE tms_instance
        SET custom_parameter = replace(custom_parameter, 'False', 'false')
        WHERE id in
        (SELECT id FROM tms_instance where custom_parameter LIKE '%False%');

        UPDATE tms_instance
        SET custom_parameter = replace(custom_parameter, 'True', 'true')
        WHERE id in
        (SELECT id FROM tms_instance where custom_parameter LIKE '%True%');

        UPDATE tms_instance
        SET custom_parameter = replace(custom_parameter, '''', '"')
        WHERE id in
        (SELECT id FROM tms_instance where custom_parameter LIKE '%''%');
        """
        self._cr.execute(sql)
        logging.info("=== END: UPDATE Custom Params on instance")

    @api.model
    def update_support_ticket_type_on_forge_ticket(self):
        """
        Update support ticket type on forge tickets for the case that
        support ticket is updated on forge ticket.
        """
        logging.info("=== START: Update support ticket type ===")
        sql = """
            UPDATE tms_forge_ticket tft
            SET support_ticket_type = tst.ticket_type,
                write_uid = %s,
                write_date = NOW() AT TIME ZONE 'UTC'
            FROM tms_support_ticket tst
            WHERE tft.tms_support_ticket_id IS NOT NULL
                AND tst.id = tft.tms_support_ticket_id
                AND (tft.support_ticket_type IS NULL
                    OR tst.ticket_type != tft.support_ticket_type);
        """
        logging.info("=== END: Update support ticket type ===")
        return self._cr.execute(sql, (self._uid,))

    @api.model
    def update_htpasswd_file_on_instance(self):
        logging.info("=== START: Update Field htpasswd_file On Instance ===")
        sql = """
            UPDATE tms_instance Ins
            SET htpasswd_file = '/usr/local/var/auth/htpasswd_'
             || Pro.name || '_' || Ins.server_type
            FROM tms_project Pro
            WHERE Pro.name != ''
            AND Ins.server_type != ''
            AND Ins.project_id = Pro.id ;
            """
        self._cr.execute(sql)

        logging.info("=== END: Update Field htpasswd_file On Instance ===")
        return True

    # F#13248
    @api.model
    def migration_field_last_completer_id(self):
        logging.info(
            "====== START: MIGRATION FROM FIRST COMPLETER "
            "TO LAST COMPLETER =======")
        sql = """
            UPDATE tms_forge_ticket
            SET last_completer_id = developer_id;"""
        self._cr.execute(sql)
        logging.info(
            "====== END: MIGRATION FROM FIRST COMPLETER "
            "TO LAST COMPLETER =======")
        return True

    # F#14084
    @api.model
    def update_parameter_tickets_markdown_color_map(self):
        logging.info(
            "====== START: UPDATE VALUE FOR PARAMETER "
            "TICKETS MARKDOWN COLOR MAP =======")
        sql = """
            UPDATE ir_config_parameter
            SET value = '{"forge": { "assigned": "#333", "wip": "#C4730C",
                                    "code_completed": "#337CDA",
                                    "ready_to_deploy": "#3B9213",
                                    "in_qa": "#9715B8", "closed": "#888" },
                          "support": { "assigned": "#333",
                                       "planned_for_delivery": "#337CDA",
                                       "delivered": "#9715B8",
                                       "ok_for_production": "#3B9213",
                                       "ok_to_close": "#3B9213",
                                       "closed": "#888" }
                         }'
            WHERE key='tickets_markdown_color_map';"""
        self._cr.execute(sql)
        logging.info(
            "====== END: UPDATE VALUE FOR PARAMETER "
            "TICKETS MARKDOWN COLOR MAP =======")
        return True

    @api.model
    def update_tms_delivery_name(self):
        logging.info("====== START: update_tms_delivery_name =======")
        sql = '''
            update tms_delivery set name = create_date;
        '''
        self._cr.execute(sql)
        logging.info("====== END: update_tms_delivery_name =======")
        return True

    @api.model
    def update_employee_id_on_res_users(self):
        logging.info(
            "====== START: update_employee_id_on_res_users =======")
        employee_env = self.env['hr.employee']
        employees = employee_env.search([])
        for employee in employees:
            if employee.user_id:
                sql = '''
                update res_users
                set employee_id = %s
                where id = %s;
                '''
                self._cr.execute(sql, (employee.id, employee.user_id.id))
        logging.info("====== END: update_employee_id_on_res_users =======")
        return True

    @api.model
    def update_milestone_id_on_tms_instance(self):
        logging.info(
            "====== START: update_milestone_id_on_tms_instance =======")
        instance_env = self.env['tms.instance']
        milestone_env = self.env['tms.milestone']
        instances = instance_env.search([
            '|', ('active', '=', True),
            ('active', '=', False),
            ('milestone_id', '=', False)
        ])
        for instance in instances:
            milestone = milestone_env.search([
                '|', ('active', '=', True),
                ('active', '=', False),
                ('project_id', '=', instance.project_id.id),
            ], order='name desc', limit=1)
            if not milestone:
                continue
            instance.write({'milestone_id': milestone.id})

        logging.info("====== END: update_milestone_id_on_tms_instance =======")
        return True

    @api.model
    def remove_unnessecery_home_action(self):
        # F#15193
        """
        Update users related to home action we need to delete,
        Remove home action is not correct:
            The correct action_id list:
            289: 'Employees'
            146: 'Meetings'
            141: 'Sales Teams'
            185: 'Opportunities'
            149: 'Contracts'
            257: "Forge Tickets"
            296: "Activities"
            60:  "Customers"

        @from Hieu:
        We should not delete duplicated actions, it will break the database
        with this warning message:

        'One of the documents you are trying to access has been deleted,
        please try again after refreshing.'
        """
        logging.info("====== START: remove_unnessecery_home_action =======")

        update_sql = """
            UPDATE res_users SET action_id = 289
                WHERE action_id IN (
                    SELECT id FROM ir_actions
                    WHERE type = 'ir.actions.act_window'
                    AND name = 'Employees');

            UPDATE res_users SET action_id = 146
                WHERE action_id IN (
                    SELECT id FROM ir_actions
                    WHERE type = 'ir.actions.act_window'
                    AND name = 'Meetings');

            UPDATE res_users SET action_id = 141
                WHERE action_id IN (
                    SELECT id FROM ir_actions
                    WHERE type = 'ir.actions.act_window'
                    AND name = 'Sales Teams');

            UPDATE res_users SET action_id = 185
                WHERE action_id IN (
                    SELECT id FROM ir_actions
                    WHERE type = 'ir.actions.act_window'
                    AND name = 'Opportunities');

            UPDATE res_users SET action_id = 149
                WHERE action_id IN (
                    SELECT id FROM ir_actions
                    WHERE type = 'ir.actions.act_window'
                    AND name = 'Contracts');

            UPDATE res_users SET action_id = 257
                WHERE action_id IN (
                    SELECT id FROM ir_actions
                    WHERE type = 'ir.actions.act_window'
                    AND name = 'Forge Tickets');

            UPDATE res_users SET action_id = 296
                WHERE action_id IN (
                    SELECT id FROM ir_actions
                    WHERE type = 'ir.actions.act_window'
                    AND name = 'Activities');

            UPDATE res_users SET action_id = 60
                WHERE action_id IN (
                    SELECT id FROM ir_actions
                    WHERE type = 'ir.actions.act_window'
                    AND name = 'Customers');
        """
        self._cr.execute(update_sql)
        logging.info("====== END: remove_unnessecery_home_action =======")
        return True

    @api.model
    def update_release_dates_on_tms_milestone(self):
        logging.info(
            "====== START: Update release dates on Tms Milestone =======")
        milestone_env = self.env['tms.milestone']
        tms_milestones = milestone_env.search([])

        for milestone in tms_milestones:
            deliveries = milestone.deliveries or []
            realease_date_lst = []
            for delivery in deliveries:
                if delivery.instance_id.server_type == 'production' and \
                        delivery.state == 'done':
                    release_date = \
                        datetime.strptime(delivery.name,
                                          "%Y-%m-%d %H:%M:%S").date()
                    realease_date_lst.append(str(release_date))
            if realease_date_lst:
                realease_date_on_mst = ', '.join(realease_date_lst)
                milestone.write({'release_dates': realease_date_on_mst})

        logging.info("===== END: Update release dates on Tms Milestone ======")
        return True

    @api.model
    def update__main_dev_milestone_on_tms_milestone(self):
        logging.info("== START: update main dev milestone on Tms Milestone ==")
        projects = self.env['tms.project'].search([])
        milestone_env = self.env['tms.milestone']
        main_milestone_dict = {}
        for project in projects:
            main_milestone = milestone_env.search(
                [('project_id', '=', project.id),
                 ('state', 'in', ['development', 'deployment'])],
                order="number desc", limit=1)
            main_milestone_dict.update({project.id: main_milestone.id})
        for milestone in milestone_env.search([]):
            milestone.is_main_milestone = False
            project_id = milestone.project_id.id
            if main_milestone_dict.get(project_id, False) == milestone.id:
                milestone.is_main_milestone = True

        logging.info("=== END: update main dev milestone on Tms Milestone ===")
        return True

    @api.model
    def function_update_salary_fields_for_hr_applicant(self):
        """
        Replace 'salary_expected' and 'salary_proposed' by 2 new fields
         'salary_expected_secure' and 'salary_proposed_secure'
        """
        sql = """
            SELECT count(column_name)
            FROM information_schema.columns
            WHERE table_name='hr_applicant'
                  AND column_name ilike 'salary_proposed_moved%'
            """
        self._cr.execute(sql)
        col_count = self._cr.fetchone()[0] - 1
        applicants = self.env['hr.applicant'].search([])

        for applicant in applicants:
            count = col_count
            newest_salary_proposed = True
            newest_salary_expected = True
            salary_proposed = 0
            salary_expected = 0
            while count >= 0:
                sql = """SELECT salary_proposed_moved%s,
                salary_expected_moved%s FROM hr_applicant
                WHERE id = %s""" % (str(count), str(count), applicant.id)
                self._cr.execute(sql)
                data = self._cr.fetchone()

                if newest_salary_proposed and data[0] not in [0, None]:
                    salary_proposed = data[0]
                    newest_salary_proposed = False
                if newest_salary_expected and data[1] not in [0, None]:
                    salary_expected = data[1]
                    newest_salary_expected = False
                count -= 1

            salary_update = self.get_salary_update(
                salary_proposed, salary_expected)
            if salary_update:
                sql = """
                  UPDATE hr_applicant
                  SET %s WHERE id = %s""" % (salary_update,
                                             applicant.id)
                self._cr.execute(sql)
        return True

    @api.model
    def update_sequence_tms_forge_ticket(self):
        logging.info("====== START: update_sequence_tms_forge_ticket =======")
        forge_env = self.env['tms.forge.ticket']
        self.env.add_todo(forge_env._fields['sequence'], forge_env.search([]))
        forge_env.search([]).recompute()
        logging.info("====== END: update_sequence_tms_forge_ticket =======")
        return True

    @api.model
    def correct_priority_tms_forge_ticket(self):
        logging.info("====== START: correct_priority_tms_forge_ticket =======")
        sql = """
            UPDATE tms_forge_ticket
            SET priority='very_high'
            WHERE priority='urgent';
        """
        self._cr.execute(sql)

        sql = """
            UPDATE tms_forge_ticket
            SET priority='low'
            WHERE priority='minor';
        """
        self._cr.execute(sql)
        logging.info("====== END: correct_priority_tms_forge_ticket =======")
        return True

    @api.model
    def get_salary_update(self, salary_proposed, salary_expected):
        salary_update = False
        if salary_proposed != 0:
            salary_update = "salary_proposed_secure='%s'" % salary_proposed
        if salary_expected != 0:
            if salary_update:
                salary_update += ", salary_expected_secure = '%s'" % \
                    salary_expected
            else:
                salary_update = "salary_expected_secure='%s'" % \
                    salary_expected
        return salary_update

    @api.model
    def _update_start_date_of_tms_activities(self):
        logging.info("===== START: UPDATE START DATE OF ATIVITIES ======")
        tms_activties = self.env['tms.activity'].search([])
        for tms_activity in tms_activties:
            tms_activity.write({'start_date': tms_activity.create_date})
        logging.info("===== END: UPDATE START DATE OF ATIVITIES ======")

    @api.model
    def _update_data_columns_tms_activity(self):
        logging.info('=====START: UPDATE DATA OF COLUMNS TMS ACTIVITY=====')
        activities = self.env['tms.activity'].search([])
        for activity in activities:
            activity._compute_support_indicators()
        logging.info("===== END: UPDATE DATA OF COLUMNS TMS ACTIVITY ======")

    @api.model
    def _update_receiver_of_email_daily_notification(self):
        logging.info("===== START: UPDATE RECEIVER OF EMAIL "
                     "DAILY NOTIFICATION ======")
        config_pool = self.env['ir.config_parameter']
        config_key = "default_daily_notification_receiver_email"
        config_pool.set_param(config_key, "pm@lists.trobz.com")
        logging.info("===== END: UPDATE RECEIVER OF EMAIL "
                     "DAILY NOTIFICATION ======")

    @api.model
    def _update_ticket_missing_last_assigned_date(self):
        logging.info("===== START: UPDATE LAST ASSIGNED DATE "
                     "OF FORGE TICKET ======")
        tms_forge_tk_env = self.env['tms.forge.ticket']
        tickets = tms_forge_tk_env.search(
            [('state', 'in', ('assigned', 'wip')),
             ('development_time', 'in', (None, '0', '0.00', '0.01'))])
        for ticket in tickets:
            last_assigned_date = ''
            for comment in ticket.tms_forge_ticket_comment_ids:
                if 'Assignee' in comment.comment:
                    last_assigned_date = comment.name
                    break
            ticket.last_assigned_date = last_assigned_date and\
                last_assigned_date or ticket.create_date
        logging.info("===== END: UPDATE LAST ASSIGNED DATE "
                     "OF FORGE TICKET ======")

    @api.model
    def _update_reporter_inactive_for_support_ticket(self):
        logging.info("===== START: UPDATE REPORTER INACTIVE FOR SUPPORT TICKET"
                     " ======")
        user_env = self.env['res.users']
        sql = """
            SELECT DISTINCT(ru.id) as id
            FROM tms_support_ticket tst INNER JOIN
                res_users ru ON tst.reporter_id = ru.id
            WHERE ru.active = false
        """
        self._cr.execute(sql)
        datas = self.env.cr.fetchall()
        user_ids = [data[0] for data in datas]
        logging.info("Found %d users are inactive." % (len(user_ids)))
        user_env.browse(user_ids).change_reporter_for_support_ticket()
        logging.info("Finish change %d users are inactive." % (len(user_ids)))
        logging.info("===== END: UPDATE REPORTER INACTIVE FOR SUPPORT TICKET "
                     "======")

    @api.model
    def _update_team_id_for_employee(self):
        logging.info("===== START: UPDATE TEAM FOR EMPLOYEE ======")
        sql = """
            SELECT id, team_id
            FROM hr_employee
            WHERE team_id is not null
        """
        self._cr.execute(sql)
        datas = self.env.cr.fetchall()
        sql_insert_data = """
            INSERT INTO team_member_rel(hr_employee_id,hr_team_id)
            VALUES(%s,%s)
        """
        for data in datas:
            self._cr.execute(sql_insert_data, (data[0], data[1]))
        logging.info("===== END: UPDATE TEAM FOR EMPLOYEE ======")

    @api.model
    def remove_value_of_language_to_load(self):
        logging.info("===== START: DISABLE LOADING TRANSLATION FR ======")
        self.env['ir.config_parameter'].set_param("language_to_load", "")
        fr_lang = self.env['res.lang'].search(
            [('code', '=', 'fr_FR'), ('iso_code', '=', 'fr')])
        if fr_lang:
            fr_lang.active = False
        logging.info("===== END: DISABLE LOADING TRANSLATION  FR ======")

    @api.model
    def _update_project_id_for_delivery(self):
        logging.info("===== START: UPDATE PROJECT ID ON DELIVERY ======")
        sql = """
            SELECT id
            FROM tms_delivery
            WHERE project_id is null
        """
        self._cr.execute(sql)
        datas = self.env.cr.fetchall()
        delivery_ids = [data[0] for data in datas]
        deliverys = self.env['tms.delivery'].browse(delivery_ids)
        for delivery in deliverys:
            delivery.write({
                'project_id': delivery.instance_id and
                delivery.instance_id.project_id and
                delivery.instance_id.project_id.id or False})
        logging.info("===== END: UPDATE PROJECT ID ON DELIVERY ======")

    def update_state_order_forge_tiket(self):
        logging.info("===== START: UPDATE STATE ORDER OF FORGE TICKET ======")
        state_dict = {
            'assigned': 1,
            'wip': 2,
            'code_completed': 3,
            'ready_to_deploy': 4,
            'in_qa': 5,
            'closed': 6,
        }
        tickets = self.env['tms.forge.ticket'].search([('state', '!=', False)])
        for rec in tickets:
            state_order = rec.state and state_dict[rec.state] or 0
            self._cr.execute(
                """
                UPDATE tms_forge_ticket
                SET state_order = %s
                WHERE id = %s
                """ % (state_order, rec.id)
            )
        logging.info("===== END: UPDATE STATE ORDER OF FORGE TICKET ======")

    @api.model
    def _update_subcriber_for_forge_ticket(self):
        logging.info("===== START: UPDATE SUBSCRIBER FOR FORGE TICKET======")
        sql = """
            SELECT id
            FROM tms_forge_ticket
            WHERE project_id IN (183,194,187,169,189)
        """
        self._cr.execute(sql)
        datas = self.env.cr.fetchall()
        projects = self.env['tms.project'].browse([183, 194, 187])
        user_ids = []
        for project in projects:
            users = project.project_supporter_rel_ids or []
            for user in users:
                if user.employer_id and user.employer_id.id == 1:
                    user_ids.append(user.id)
        user_ids = list(set(user_ids))
        forge_ticket_ids = []
        subscriber_ids = []
        change_forge_ticket = []
        for data in datas:
            forge_ticket_ids.append(data[0])
        if forge_ticket_ids:
            forge_tickets = self.env['tms.forge.ticket'].browse(
                forge_ticket_ids)
        for forge_ticket in forge_tickets:
            subscribers = forge_ticket.forge_ticket_subscriber_ids or []
            for subscriber in subscribers:
                user = subscriber.name
                if user.employer_id and user.employer_id.id != 1 or \
                        user.id not in user_ids:
                    subscriber_ids.append(subscriber.id)
                    str_need_remove = 'FORGE TICKET ID: %s - USER LOGIN: %s' \
                        % (forge_ticket.id, user.login)
                    change_forge_ticket.append(str_need_remove)
        subscriber_ids = list(set(subscriber_ids))
        change_forge_ticket = list(set(change_forge_ticket))
        if subscriber_ids and change_forge_ticket:
            self.env['tms.subscriber'].browse(subscriber_ids).unlink()
            str_change_forge_ticket = '\n- '.join(change_forge_ticket)
            logging.info("CHANGE FORGE TICKET AND REMOVE USERS: \n- %s" %
                         (str_change_forge_ticket))
        logging.info("===== END: UPDATE SUBSCRIBER FOR FORGE TICKET ======")

    @api.model
    def _update_status_of_exist_support_contract(self):
        logging.info(
            "===== START: UPDATE STATUS OF EXIST SUPPORT CONTRACT ======")
        scontracts = self.env['project.support.contracts'].search([])
        scontracts._check_period()
        logging.info(
            "===== END: UPDATE STATUS OF EXIST SUPPORT CONTRACT ======")

    @api.model
    def _update_data_for_asset_adjustment(self):
        # update data for all equipment request
        logging.info("===== START: UPDATE EQUIPMENT REQUESTS ======")
        requests = self.env[
            'hr.equipment.request'].search([])
        for request in requests:
            if not request.partial_apprv:
                request.trobz_contr_amt = request.purchase_price
            request.type = 'personal'
        logging.info("===== END: UPDATE EQUIPMENT REQUESTS ======")
        logging.info("===== START: CREATE ASSETS ======")
        asset_env = self.env['tms.asset']
        requests = self.env[
            'hr.equipment.request'].search([('state', '=', 'purchased')])
        for request in requests:
            if len(request.asset_ids) > 0:
                continue
            for _ in range(0, request.number):
                vals = {
                    'name': request.name,
                    'owner_id': request.employee_id.id,
                    'assignee_id': request.employee_id.id,
                    'type': request.type,
                    'purchased_date': request.delivery_date,
                    'category_id': request.category_id.id,
                    'request_id': request.id,
                    'purchased_price': request.purchase_price,
                    'trobz_contribution': request.trobz_contr_amt,
                }
                if vals['trobz_contribution'] == 0:
                    print vals
                asset_env.create(vals)
        logging.info("===== END: CREATE ASSETS ======")

    @api.model
    def _update_std_estimate_for_forge_ticket(self):
        logging.info("===== START: UPDATE STD DEV ESTIMATE FORGE TICKET======")
        sql_update_std_estimate = '''
        UPDATE tms_forge_ticket
        SET std_development_time = development_time
        '''
        self._cr.execute(sql_update_std_estimate)
        logging.info("===== END: UPDATE STD DEV ESTIMATE FORGE TICKET ======")

    def _update_working_hour_for_support_ticket(self):
        logging.info(
            "===== START: UPDATE WORKING HOUR OF SUPPORT TICKET ======")
        t1 = datetime.now()
        s_tickets = self.env['tms.support.ticket'].search([])
        logging.info(
            "Updating working hours of %s Support Ticket" % len(s_tickets))
        self._cr.execute('''
        UPDATE tms_working_hour as u
        SET tms_support_ticket_id = (
            SELECT tms_support_ticket_id
            FROM tms_forge_ticket where id = u.tms_forge_ticket_id)
        ''')
        t2 = datetime.now()
        t = t2 - t1
        logging.info("Update completely in %s s" % t)
        logging.info(
            "===== END: UPDATE WORKING HOUR OF SUPPORT TICKET ======")

    @api.model
    def _update_data_for_appraisal(self):
        logging.info(
            "===== START: UPDATE DATA FOR APPRAISAL ======")
        t1 = datetime.now()
        hr_apps = self.env['hr.appraisal'].search([('state', '=', 'done')])
        sql = '''
        UPDATE hr_appraisal SET manager_id=%s WHERE id=%s
        '''
        ignore = []
        for app in hr_apps:
            # There are 4 case in updating appraisal:
            # 1. Only 1 input => author of input is manager of appraisal
            # 2. There are 2 input, one of them has author is employee of
            # appraisal => author of res input is manager in apraisal
            # 3. There are 2 input, No one in authors of inputs is employee of
            # appraisal => update manually
            # 4. There are 3 input => update manually
            if len(app.hr_appraisal_input_ids) == 1:
                self._cr.execute(
                    "SELECT author_id FROM hr_appraisal_input "
                    "WHERE appraisal_id = %s" % app.id)
                author = self._cr.fetchone()
                manager_id = author and author[0] or None
                self._cr.execute(sql % (manager_id, app.id))
                logging.info(
                    "Update appraisal %s (has 1 input)" % app.id)
            elif len(app.hr_appraisal_input_ids) == 2:
                self._cr.execute(
                    "SELECT employee_id FROM hr_appraisal "
                    "WHERE id = %s" % app.id)
                employee = self._cr.fetchone()
                employee_id = employee and employee[0] or None
                if employee_id:
                    sql_query = "SELECT author_id FROM hr_appraisal_input " +\
                        "WHERE author_id != %s and appraisal_id = %s"
                    self._cr.execute(
                        sql_query % (employee_id, app.id))
                    author = self._cr.fetchone()
                    author_id = author and author[0] or None
                    if author_id:
                        self._cr.execute(sql % (author_id, app.id))
                        logging.info(
                            "Update appraisal %s (has 2 input)" % app.id)
                else:
                    ignore.append(app.id)
                    logging.info(
                        "Ignore appraisal %s (has 2 input)" % app.id)
            else:
                ignore.append(app.id)
                logging.info(
                    "Ignore appraisal %s (has 3 input)" % app.id)
        t2 = datetime.now()
        t = t2 - t1
        logging.info("Update completely in %s s" % t)
        logging.info("Please update manually these appraisal %s" % ignore)
        logging.info(
            "===== END: UPDATE DATA FOR APPRAISAL ======")

    @api.model
    def _update_time_spent_support_ticket(self):
        logging.info(
            "===== START: UPDATE TIME SPENT FOR SUPPORT TICKET ======")
        wh_er = self.env['tms.working.hour'].search(
            [('tms_support_ticket_id', '!=', None),
             ('tms_forge_ticket_id', '=', None)])
        support_ids = [wh.tms_support_ticket_id.id for wh in wh_er]
        supports = self.env[
            'tms.support.ticket'].search([('id', 'in', support_ids)])
        logging.info("Update %s support tickets" % len(supports))
        for ticket in supports:
            total = 0
            if 'tms_working_hour_ids'in ticket._columns and \
                    ticket.tms_working_hour_ids:
                for working_hours in ticket.tms_working_hour_ids:
                    if working_hours.duration_hour:
                        total += working_hours.duration_hour
            if 'time_spent'in ticket._columns:
                ticket.time_spent = total

        logging.info(
            "===== END: UPDATE TIME SPENT FOR SUPPORT TICKET ======")

    @api.model
    def _update_leave_type_hr_holidays(self):
        logging.info("===== START: UPDATE LEAVE TYPE OF HR HOLIDAYS ======")
        holidays = self.env['hr.holidays'].search([])
        for holiday in holidays:
            if holiday.leave_type:
                continue
            leave_type = []
            for line in holiday.holiday_line:
                status_name = line.holiday_status_id and \
                    line.holiday_status_id.name
                if status_name and status_name not in leave_type:
                    leave_type.append(status_name)
            if leave_type:
                holiday.leave_type = ', '.join(leave_type)
            else:
                holiday.leave_type = ''
        logging.info("===== END: UPDATE LEAVE TYPE OF HR HOLIDAYS ======")

    @api.model
    def _update_mailing_list_project(self):
        logging.info("===== START: UPDATE MAILING LIST OF PROJECT ======")
        mail_env = self.env['mailman.list']
        projects = self.env['tms.project'].search([])
        for project in projects:
            logging.info("Update mailing list for project %s" % project.name)
            lst_tpm_pm = list(set(
                [project.technical_project_manager_id, project.owner_id]))
            mailings = mail_env.search(
                [('project_id', '=', project.id),
                 ('active', '=', True)])
            logging.info("Found %s mailing list" % len(mailings))
            for mailing in mailings:
                partner_ids = mailing.subscriber_ids.ids
                for user in lst_tpm_pm:
                    if user.partner_id.id not in partner_ids:
                        try:
                            mailing.write(
                                {'subscriber_ids': [(4, user.partner_id.id)]})
                            logging.info(
                                "Add %s to mailing list  %s" % (
                                    user.partner_id.name, mailing.name))
                        except:
                            logging.info("Can not update mailing list")
        logging.info("===== END: UPDATE MAILING LIST OF PROJECT ======")

    def _update_balance_benefit(self):
        logging.info("===== START: UPDATE BALANCE BENEFIT ======")
        employees = self.env['hr.employee'].search([])
        for emp in employees:
            emp.balance_benefit = emp.cred_benefit - emp.debit_benefit
        logging.info("===== END: UPDATE BALANCE BENEFIT ======")

    @api.model
    def _update_default_docker_repository(self):
        logging.info("=== START: UPDATE default_docker_repository")
        config_parameter_env = self.env['ir.config_parameter']
        config_key = "default_docker_repository"
        config_parameter_env.set_param(
            config_key, "docker-hub.trobz.com:443/production_data/%s/%s")
        logging.info("===== END: UUPDATE default_docker_repository ======")

    @api.model
    def _update_data_for_equipment_request(self):
        """
        F#29964 - "Benefit Start Date" and "Balance Benefit"
        are empty for the IT request
        """
        logging.info("===== START: UPDATE DATA FOR EQUIPMENT REQUESTS ======")
        requests = self.env[
            'hr.equipment.request'].search([])
        for request in requests:
            # Compute balance at create_date
            if request.type == 'trobz':
                continue
            employee = request.employee_id
            if not employee:
                continue
            request.benefit_start = employee.benefit_start
            create_date = datetime.strptime(
                request.create_date, '%Y-%m-%d %H:%M:%S').date()
            request.balance_benefit = employee.get_credit_benefit_on_date(
                create_date)

            # Update purchase price to total_purchase_amount
            # Set unit_price = total_purchase_amount / number
            request.total_purchase_amount = request.purchase_price
            request.unit_price = request.purchase_price / request.number
        # update balance benefit again
        self._update_balance_benefit()
        # update data for asset
        assets = self.env['tms.asset'].search([])
        for asset in assets:
            req = asset.request_id or None
            if not req:
                continue
            asset.write(
                {
                    'purchased_price': req.unit_price,
                    'trobz_contribution': req.trobz_contr_amt / req.number
                }
            )
        logging.info("===== END: UPDATE DATA FOR EQUIPMENT REQUESTS ======")

    def _update_wrong_Thai_it_equipment_request(self):
        trobz_contribution = 10000000
        request_id = 100
        asset_internal_id = 'ASSET-093'
        employee_id = 132
        logging.info("=== START: UPDATE it equipment request")
        sql = """
            UPDATE hr_equipment_request
            SET partial_apprv = True, trobz_contr_amt = %s
            WHERE id = %s;""" % (trobz_contribution, request_id)
        self._cr.execute(sql)
        logging.info("=== END: UPDATE it equipment request")
        logging.info("=== START: UPDATE tms asset")
        sql = """
            UPDATE tms_asset
            SET trobz_contribution = %s
            WHERE internal_code='%s';""" % (
            trobz_contribution, asset_internal_id)
        self._cr.execute(sql)
        logging.info("=== END: UPDATE tms asset")
        logging.info("=== START: UPDATE hr employee")
        sql = """
            UPDATE hr_employee
            SET balance_benefit = balance_benefit + (debit_benefit - %s),
            debit_benefit = %s
            WHERE id = %s;""" % (
            trobz_contribution, trobz_contribution, employee_id)
        self._cr.execute(sql)
        logging.info("=== END: UPDATE hr employee")

    @api.model
    def _update_balance_on_equipment_request(self):
        """
        """
        logging.info("===== START: UPDATE DATA FOR EQUIPMENT REQUESTS ======")
        req_env = self.env['hr.equipment.request']
        requests = req_env.search([])
        for request in requests:
            # Compute balance at create_date
            if request.type == 'trobz':
                continue
            employee = request.employee_id
            if not employee:
                continue
            request.benefit_start = employee.benefit_start
            create_date = datetime.strptime(
                request.create_date, '%Y-%m-%d %H:%M:%S').date()
            # Compute credit
            cred = employee.get_credit_benefit_on_date(
                create_date)

            # Compute debit
            # Go to request, get credit benefit at create time. At that time,
            # get all request of employee who had been purchased
            # and compute debit
            debit = 0
            appr_reqs = req_env.search(
                [
                    ('id', '!=', request.id),
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'purchased'),
                    ('schd_pur_date', '<=', request.create_date)
                ])
            for req in appr_reqs:
                debit += req.trobz_contr_amt
            # Compute balance
            request.balance_benefit = cred - debit

        logging.info("===== END: UPDATE DATA FOR EQUIPMENT REQUESTS ======")

    @api.model
    def _update_code_and_inactive_leave_type(self):
        logging.info("===== START: UPDATE CODE FOR LEAVE TYPE =====")
        type_env = self.env['hr.holidays.status']
        leave_types = type_env.search([])
        for leave_type in leave_types:
            if leave_type.name == "Casual leave (paid)":
                leave_type.write({'code': 'CP'})
            if leave_type.name == "Sick leave (unpaid)":
                leave_type.write({'code': 'SiU'})
            if leave_type.name == "Unpaid":
                leave_type.write({'code': 'U'})
            if leave_type.name == "Casual leave (unpaid)":
                leave_type.write({'code': 'CU'})
            if leave_type.name == "Sick leave (unclassified)":
                leave_type.write({'code': 'SiUn'})
            if leave_type.name == "Wedding":
                leave_type.write({'code': 'W'})
            if leave_type.name == \
                    "Funeral of parents/parents-in-law/spouse/children":
                leave_type.write({'code': 'F'})
            if leave_type.name == "Child's birth (father)":
                leave_type.write({'code': 'C'})
            if leave_type.name == "Sick leave (paid)":
                leave_type.write({'code': 'SiP'})
            if leave_type.name == "Maternity leave":
                leave_type.write({'code': 'M'})
        logging.info("===== END: UPDATE CODE FOR LEAVE TYPE =====")
        logging.info("===== START: INACTIVE LEAVE TYPE =====")
        wrong_leave_type = type_env.search(
            [('name', '=', 'Casual leave (paid)  (12/12)')], limit=1)
        if wrong_leave_type:
            wrong_leave_type.write({'active': False})
        logging.info("===== END: INACTIVE LEAVE TYPE =====")

    @api.model
    def _inactive_leave_type(self):
        logging.info("===== START: INACTIVE LEAVE TYPE =====")
        sick_leave_unclassified = self.env.ref(
            'tms_modules.tms_holiday_status_sick_leave_unclassified',
            raise_if_not_found=False)
        if sick_leave_unclassified:
            sick_leave_unclassified.write({'active': False})
        logging.info("===== END: INACTIVE LEAVE TYPE =====")

    @api.model
    def function_update_trainee_contract_type(self):
        logging.info("====== START: update_trainee_contract_type =======")
        trainee_type = self.env[
            'hr.contract.type'].search([('name', '=', 'Trainee')], limit=1)
        if trainee_type:
            trainee_type.write({'auto_tick_trial': True})
        logging.info("====== END: update_trainee_contract_type =======")
        return True

    @api.model
    def update_nbr_support_dashboard(self):
        logging.info(
            "====== START: UPDATE NBR FIELD FOR THE SUPPORT DASHBOARD ======="
        )
        sql = '''
            update tms_support_ticket set nbr = 1
            where nbr = 0
        '''
        self._cr.execute(sql)
        logging.info(
            "====== END: UPDATE NBR FIELD FOR THE SUPPORT DASHBOARD ======="
        )
        return True

    @api.model
    def update_field_sprint_forge_ticket(self):
        logging.info(
            "====== START: UPDATE SPRINT FIELD FOR THE FORGE TICKET ======="
        )
        sql = '''
            update tms_forge_ticket set sprint = ts.date_end
            from tms_ticket_sprint ts
            where ticket_sprint_id = ts.id
        '''
        self._cr.execute(sql)
        logging.info(
            "====== END: SPRINT FIELD FOR THE FORGE TICKET ======="
        )

        return True

    @api.model
    def update_field_sprint_resource_allocation(self):
        logging.info(
            "====== START: UPDATE SPRINT FIELD FOR THE "
            "RESOURCE ALLOCATION ======="
        )
        sql = '''
            update hr_resource_allocation set sprint = ts.date_end
            from tms_ticket_sprint ts
            where sprint_id = ts.id
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE SPRINT FIELD FOR THE \
            RESOURCE ALLOCATION =======")
        return True

    @api.model
    def update_field_sprint_working_hours(self):
        logging.info("====== START: UPDATE SPRINT FIELD FOR \
            THE WORKING HOURS =======")
        sql = '''
            update tms_working_hour set sprint = ts.date_end
            from tms_ticket_sprint ts
            where sprint_id = ts.id
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE SPRINT FIELD FOR THE \
            WORKING HOURS =======")
        return True

    @api.model
    def update_field_sprint_ticket_reopening(self):
        logging.info("====== START: UPDATE SPRINT FIELD FOR THE \
            TICKET REOPENING =======")
        sql = '''
            update forge_ticket_reopening set sprint = ts.date_end
            from tms_ticket_sprint ts
            where ticket_sprint_id = ts.id
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE SPRINT FIELD FOR THE TICKET \
            REOPENING =======")

    def update_state_of_field_renew_casual_leave(self):
        logging.info("====== START: UPDATE RENEW CASUAL LEAVE FIELD \
            FOR HR HOLIDAYS =======")
        sql = '''
            update hr_holidays set renew_casual_leave = False
            where renew_casual_leave is null
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE RENEW CASUAL LEAVE FIELD \
            FOR HR HOLIDAYS =======")
        return True

    def update_tms_working_hour_emp(self):
        logging.info("====== START: UPDATE TMS WORKING HOUR FOR \
            EMP ID 172 -> 78 =======")
        sql = '''
            UPDATE tms_working_hour
            SET employee_id = 78 WHERE date >='2019-01-1' AND employee_id =172
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE UPDATE TMS WORKING HOUR FOR \
            EMP ID 172 -> 78 =======")
        return True

    def update_res_users_emp(self):
        logging.info("====== START: UPDATE RELATED EMPLOYEE of res.users \
            EMP ID 172 -> 78 =======")
        sql = '''
            UPDATE res_users
            SET employee_id = 78 WHERE employee_id =172
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE RELATED EMPLOYEE of res.users \
            EMP ID 172 -> 78 =======")
        return True

    def update_casual_leave_type_tms(self):
        logging.info("====== START: UPDATE 'Casual leave (paid)' =======")
        sql = '''
            UPDATE hr_holidays_status SET name = 'Annual leave', code = 'AL'
            WHERE name = 'Casual leave (paid)'
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE 'Casual leave (paid)' TYPE =======")
        return True

    def update_unpaid_leave_type_tms(self):
        logging.info("====== START: UPDATE 'Unpaid' =======")
        sql = '''
            UPDATE hr_holidays_status SET code = 'NL'
            WHERE name = 'Unpaid'
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE 'Unpaid' TYPE =======")
        return True

    def update_sick_leave_type_tms(self):
        logging.info("====== START: UPDATE 'Sick leave (paid)' =======")
        sql = '''
            UPDATE hr_holidays_status
            SET name = 'Emergency Medical Leave', code = 'EML'
            WHERE name = 'Sick leave (paid)'
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE 'Sick leave (paid)' TYPE =======")
        return True

    def update_maternity_leave_type_tms_adj(self):
        logging.info("====== START: UPDATE 'Maternity leave' =======")
        sql = '''
            UPDATE hr_holidays_status
            SET payment_type = 'paid_social', code = 'SIL'
            WHERE name = 'Maternity leave'
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE 'Maternity leave' TYPE =======")
        return True

    def update_accident_leave_type_tms_adj(self):
        logging.info("====== START: UPDATE 'Accident leave' =======")
        sql = '''
            UPDATE hr_holidays_status
            SET payment_type = 'paid_social', active = True, code = 'SIL'
            WHERE name = 'Accident'
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE 'Accident' TYPE =======")
        return True

    def update_funeral_leave_type_tms_rollback(self):
        logging.info("====== START: UPDATE 'Funeral leave' =======")
        sql = '''
            UPDATE hr_holidays_status
            SET payment_type = 'paid',
                name = 'Funeral of parents/parents-in-law/spouse/children',
                code = 'SIL'
            WHERE name = 'Funeral of parents/parents-in-law'
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE 'Funeral' TYPE =======")
        return True

    def update_parameter_default_sick_leave_paid(self):
        logging.info("====== START: UPDATE PARAMETER 'default_sick_leave_paid'\
             =======")
        sql = '''
            UPDATE ir_config_parameter
            SET value = 'Emergency Medical Leave'
            WHERE key = 'default_sick_leave_paid'
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE PARAMETER 'default_sick_leave_paid'\
            =======")
        return True

    def update_parameter_default_sick_leave_paid_new(self):
        logging.info(
            "====== START: UPDATE PARAMETER 'default_sick_leave_paid_new'\
             ======="
        )
        sql = '''
            UPDATE ir_config_parameter
            SET value = '[''Emergency Medical Leave'']'
            WHERE key = 'default_sick_leave_paid_new'
        '''
        self._cr.execute(sql)
        logging.info(
            "====== END: UPDATE PARAMETER 'default_sick_leave_paid_new'\
            ======="
        )
        return True

    def update_parameter_emergency_medical_type(self):
        logging.info(
            "====== START: UPDATE PARAMETER 'emergency_medical_type'\
             ======="
        )
        sql = '''
            UPDATE ir_config_parameter
            SET value = '[''Emergency Medical Leave'']'
            WHERE key = 'emergency_medical_type'
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE PARAMETER 'emergency_medical_type'\
            =======")
        return True

    def update_wedding_leave_type_tms_renew(self):
        logging.info("====== START: UPDATE 'Wedding leave' =======")
        sql = '''
            UPDATE hr_holidays_status
            SET code = 'SIL'
            WHERE name = 'Wedding'
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE 'Wedding' TYPE =======")
        return True

    def update_unactive_leave_unpaid_type_tms(self):
        logging.info("====== START: UPDATE 'deactive leaves unpaid' =======")
        sql = '''
            UPDATE hr_holidays_status
            SET active = False
            WHERE name in ('Sick leave (unpaid)', 'Unpaid',
                'Compensatory Work', 'Compensatory leave',
                'Sick leave (Social Insurance)')

        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE 'deactive leaves unpaid' =======")
        return True

    def update_merge_leaves_unpaid_type_tms(self):
        logging.info("====== START: UPDATE 'merge leaves unpaid' =======")
        holiday_lines = self.env['hr.holidays.line'].search([
            ('holiday_status_id', 'in', [
                self.env.ref('hr_holidays.holiday_status_sl').id,
                self.env.ref('hr_holidays.holiday_status_unpaid').id,
            ])
        ])
        for line in holiday_lines:
            line.write({
                'holiday_status_id': self.env.ref(
                    'trobz_hr_holiday_vn.'
                    'hr_holiday_status_casual_unpaid').id,
            })
        logging.info("====== END: UPDATE 'merge leaves unpaid' =======")
        return True

    def update_paternity_leave_type_tms(self):
        logging.info("====== START: UPDATE 'Child's birth (father)' =======")
        sql = '''
            UPDATE hr_holidays_status
            SET name = 'Paternity Leave',
                code = 'PaL',
                max_days_allowed = 0.0,
                payment_type = 'to_confirm'
            WHERE name = 'Child''s birth (father)'
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE 'Child's birth (father)' =======")
        return True

    def remove_funeral_spouse_children_leave_type_tms(self):
        logging.info(
            "====== START: REMOVE 'Funeral of spouse/children' =======")
        sql = '''
            delete FROM hr_holidays_status
            WHERE name = 'Funeral of spouse/children'
        '''
        self._cr.execute(sql)
        logging.info("====== END: REMOVE 'Funeral of spouse/children' =======")
        return True

    @api.model
    def update_resource_allocation_date_from_date_to(self):
        logging.info(
            "===== START: update_resource_allocation_date_from_date_to =====")
        ra_env = self.env['hr.resource.allocation']
        ra_recs = ra_env.search([('date_from', '=', False)])
        for ra_rec in ra_recs:
            sprint = ra_rec.sprint
            date_from = datetime.strptime(sprint, '%Y-%m-%d') + timedelta(
                days=-6)
            ra_rec.write({
                'date_from': date_from,
                'date_to': sprint
            })
        logging.info(
            "====== END: update_resource_allocation_date_from_date_to =======")
        return True

    @api.model
    def update_default_project_activity(self):
        logging.info(
            "===== START: update_default_project_activity =====")
        sql = """
            UPDATE ir_config_parameter
            SET value = '[
                {
                    "name": "Development / Unit Tests",
                    "analytic_secondaxis_id": "Initial Project Iterations",
                    "state": "Planned", "working_hours_requires_ticket": True
                }, {
                    "name": "Tech Support / Code Review",
                    "analytic_secondaxis_id": "Initial Project Iterations",
                    "state": "Planned", "working_hours_requires_ticket": False
                }, {
                    "name": "Technical Specifications",
                    "analytic_secondaxis_id": "Initial Project Iterations",
                    "state": "Planned", "working_hours_requires_ticket": False
                }, {
                    "name": "Functional Tests",
                    "analytic_secondaxis_id": "Initial Project Iterations",
                    "state": "Planned", "working_hours_requires_ticket": False
                }, {
                    "name": "Supervision / Management",
                    "analytic_secondaxis_id": "Initial Project Iterations",
                    "state": "Planned", "working_hours_requires_ticket": False
                }, {
                    "name": "External Meeting",
                    "analytic_secondaxis_id": "Initial Project Iterations",
                    "state": "Planned", "working_hours_requires_ticket": False
                }, {
                    "name": "Internal Meeting",
                    "analytic_secondaxis_id": "Initial Project Iterations",
                    "state": "Planned", "working_hours_requires_ticket": False
                }, {
                    "name": "User Acceptance Test (UAT)",
                    "analytic_secondaxis_id": "Initial Project Iterations",
                    "state": "Planned", "working_hours_requires_ticket": False
                }, {
                    "name": "Write down Test cases",
                    "analytic_secondaxis_id": "Initial Project Iterations",
                    "state": "Planned", "working_hours_requires_ticket": False
                }]'
            WHERE key='default_project_activity';"""
        self._cr.execute(sql)
        logging.info(
            "====== END: update_default_project_activity =======")
        return True

    def update_code_leave_type_tms(self):
        logging.info("====== START: UPDATE code of some leave types =======")
        holiday_status = self.env['hr.holidays.status'].search([])
        wedding = self.env.ref(
            'trobz_hr_holiday_vn.hr_holiday_status_wedding').id
        funeral = self.env.ref(
            'trobz_hr_holiday_vn.hr_holiday_status_funeral_special').id
        child_wedding = self.env.ref(
            'tms_modules.hr_holiday_status_children_wedding').id
        accident = self.env.ref(
            'trobz_hr_holiday_vn.hr_holiday_status_accident').id
        maternity = self.env.ref(
            'trobz_hr_holiday_vn.hr_holiday_status_maternity').id
        paternity = self.env.ref(
            'trobz_hr_holiday_vn.hr_holiday_status_child_birth_father').id

        for line in holiday_status:
            if line.id == wedding:
                line.write({
                    'code': 'W'
                })
                continue

            if line.id == funeral:
                line.write({
                    'code': 'F'
                })
                continue

            if line.id == child_wedding:
                line.write({
                    'code': 'ChildW'
                })

            if line.id == accident:
                line.write({
                    'code': 'A'
                })
                continue

            if line.id == maternity:
                line.write({
                    'code': 'MaL'
                })
                continue

            if line.id == paternity:
                line.write({
                    'code': 'PaL',
                    'payment_type': 'to_confirm'
                })
                continue

    @api.model
    def update_ticket_project_tags(self):
        logging.info("====== START: UPDATE PROJECT TAGS FOR TICKET  =======")
        sql = '''
            INSERT INTO forge_ticket_project_tag_rel(forge_ticket_id, tag_id)
            SELECT id as forge_ticket_id, tms_project_tag_id as tag_id
            FROM tms_forge_ticket where tms_project_tag_id is not null;

            INSERT INTO
                support_ticket_project_tag_rel(support_ticket_id, tag_id)
            SELECT id as support_ticket_id, tms_project_tag_id as tag_id
            FROM tms_support_ticket where tms_project_tag_id is not null;
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE PROJECT TAGS FOR TICKET  =======")
        return True

    @api.model
    def add_group_tms_manager_for_chaudk(self):
        logging.info("====== START: ADD GROUP TMS HR MANAGER FOR USER chaudk  "
                     "=======")
        group_tms_hr_manager = self.env.ref('tms_modules.group_tms_hr_manager')
        user = self.env['res.users'].search(
            [('login', '=', 'chaudk')], limit=1)
        if user:
            group_tms_hr_manager.write({'users': [(4, user.id)]})
        else:
            logging.info("====== NOT FOUND USER chaudk=======")
        logging.info("====== END: ADD GROUP TMS HR MANAGER FOR USER chaudk  "
                     "=======")
        return True

    @api.model
    def create_config_leave_type_unpaid_ids(self):
        logging.info("====== START: CREATE CONFIG LEAVE TYPE UNPAID  "
                     "=======")
        leave_type_unpaid = self.env.ref(
            'trobz_hr_holiday_vn.hr_holiday_status_casual_unpaid')
        self.env['ir.config_parameter'].set_param(
            "leave_type_unpaid_ids", [leave_type_unpaid.id])
        logging.info("====== END: CREATE CONFIG LEAVE TYPE UNPAID  "
                     "=======")
        return True

    @api.model
    def update_color_on_leave_type(self):
      logging.info("====== START: UPDATE COLOR FOR LEAVE TYPE  =======")
      sql = '''
        UPDATE hr_holidays_status
        SET color = (array[
          '#FF4589', '#FFF70A', '#FFBC1F',
          '#FFC745', '#FFF345', '#9A4DFF',
          '#82FFF3', '#3341FF', '#FF4F4F',
          '#FF80B7', '#A3FF99', '#FFA6DB',
          '#FFE0EF', '#D3D1FF', '#8AFFD4'])[floor(random()*15 + 1)]
        WHERE active = True;
      '''
      self._cr.execute(sql)
      logging.info("====== END: UPDATE COLOR FOR LEAVE TYPE  =  =======")
      return True

    @api.model
    def update_value_default_assignee_id(self):
        logging.info("====== START: UPDATE DEFAULT ASSIGNEE  "
                     "=======")
        sql = '''
            UPDATE tms_project
            SET default_assignee_id = default_supporter_id
        '''
        self._cr.execute(sql)
        logging.info("====== END: UPDATE DEFAULT ASSIGNEE  "
                     "=======")
        return True

    @api.model
    def create_trobz_awx_job_param(self):
        logging.info("=== START: CREATE trobz_awx_job_param System Params")
        config_parameter_env = self.env['ir.config_parameter']
        config_key = "trobz_awx_job_param"
        config_value = """
            {
                "httpauth_instance": {
                    "id": 38,
                    "name": "[NGINX] update htpasswd Instance",
                    },
            }"""
        config_parameter_env.set_param(config_key, config_value)
        logging.info("===== END: CREATE trobz_awx_job_param System Params")

    @api.model
    def update_project_name_to_lowercase(self):
        logging.info("=== START: UPDATE PROJECT NAME TO LOWERCASE")
        # Do not care about inactive project. Currently, where are 2 `inactive`
        # project can be face constraint unique name.
        # allaboutmuine and AllAboutMuine
        sql = '''
            UPDATE tms_project
            SET name = lower(name)
            WHERE active is true
        '''
        self._cr.execute(sql)
        logging.info("===== END: UPDATE PROJECT NAME TO LOWERCASE")

    @api.model
    def generate_it_equipment_bonus(self):
        logging.info("=== START: GENERATE IT EQUIPMENT BONUS")
        ir_config_param_env = self.env['ir.config_parameter']
        benefit_start = \
            ir_config_param_env.get_param('benefit_it_eq_bonus_start_date',
                                          '2014-01-01')
        # Active employee
        employees = self.env['hr.employee'].search([])
        for employee in employees:
            contracts = employee.contract_ids.filtered(
                lambda c:
                (not c.date_end or c.date_end > benefit_start) and
                not c.is_trial
            )
            contracts.action_generate_it_equipment_bonus()
        logging.info("===== END: GENERATE IT EQUIPMENT BONUS")

    @api.model
    def update_check_missing_workload(self):
        logging.info("=== START: UPDATE PROJECT NOT CHECK MISSING WORKLOAD"
                     " ===")
        projects = self.env['tms.project'].search([
            ('project_type_id.name', '=', 'DevOps and Sysadmin')])
        # projects.write({'check_missing_workload': False})
        if projects:
            sql = '''
                UPDATE tms_project
                SET check_missing_workload = false
                WHERE id in %s
            ''' % (tuple(projects.ids),)
            self._cr.execute(sql)
        logging.info("===== END: UPDATE PROJECT NOT CHECK MISSING WORKLOAD"
                     " ===")

    @api.model
    def update_trobz_awx_job_param(self):
        logging.info("=== START: UPDATE trobz_awx_job_param System Params")
        config_parameter_env = self.env['ir.config_parameter']
        config_key = "trobz_awx_job_param"
        value = config_parameter_env.get_param(config_key, '{}')
        config_value = safe_eval(value)
        config_value['sshauth_host'] = {
            "id": 11,
            "name": "[SSH] update authorized_keys",
        }
        config_parameter_env.set_param(config_key, config_value)
        logging.info("===== END: UPDATE trobz_awx_job_param System Params")

    @api.model
    def update_trobz_awx_job_param_dockerize_db_instance(self):
        logging.info("=== START: UPDATE trobz_awx_job_param System Params")
        config_parameter_env = self.env['ir.config_parameter']
        config_key = "trobz_awx_job_param"
        value = config_parameter_env.get_param(config_key, '{}')
        config_value = safe_eval(value)
        config_value['dockerize_db_instance'] = {
            "id": 49,
            "name": "[DOCKER] Dockerize database",
        }
        config_parameter_env.set_param(config_key, config_value)
        logging.info("===== END: UPDATE trobz_awx_job_param System Params")

    @api.model
    def update_trobz_awx_job_param_deploy(self):
        logging.info("=== START: UPDATE trobz_awx_job_param System Params")
        config_parameter_env = self.env['ir.config_parameter']
        config_key = "trobz_awx_job_param"
        value = config_parameter_env.get_param(config_key, '{}')
        config_value = safe_eval(value)
        config_value.update({
            "deploy_emoi": {
                "id": 30,
                "name": "[INTERNAL-TOOLS] deploy emoi",
            },
            "deploy_anhoi": {
                "id": 31,
                "name": "[INTERNAL-TOOLS] deploy anhoi",
            },
            "deploy_auditoi": {
                "id": 32,
                "name": "[INTERNAL-TOOLS] deploy auditoi",
            },
            })
        config_parameter_env.set_param(config_key, config_value)
        logging.info("===== END: UPDATE trobz_awx_job_param System Params")

    @api.model
    def update_tms_ticket_comment(self):
        logging.info("=== START: UPDATE TICKET COMMENT")
        sql = '''
            UPDATE tms_ticket_comment
            SET is_notification_sent = true
            WHERE is_notification_sent is not true
        '''
        self._cr.execute(sql)
        logging.info("===== END: UPDATE TICKET COMMENT")

    @api.model
    def update_hr_employee_capacity(self):
        logging.info('Start: Updating employee capacity')
        emp_capacities = self.env['hr.employee.capacity'].search([])

        for capacity in emp_capacities:
            if float_utils.float_compare(
                    capacity.employee_id.current_employee_capacity,
                    capacity.production_rate,
                    precision_digits=2) != 0:

                capacity = capacity.with_context(by_pass_sec=True)
                current_prod_rate = capacity.production_rate
                vals = {'production_rate': current_prod_rate}

                capacity.write(vals)
                capacity.employee_id.employee_capacity_weekly_ids.write(vals)

        logging.info('End: Updating employee capacity')
    
    @api.model
    def update_location_type(self):
        logging.info("=== START: UPDATE Leave Type on Location Type")
        # Inside HCM
        self.env.ref('tms_modules.tms_location_inside_hcm').\
            holiday_status_id =\
            self.env.ref('tms_modules.tms_holidays_status_bt_inside_hcmc')
        # Outside HCM
        self.env.ref('tms_modules.tms_location_outside_hcm').\
            holiday_status_id =\
            self.env.ref('tms_modules.tms_holidays_status_bt_outside_hcmc')
        # Abroad
        self.env.ref('tms_modules.tms_location_outside_vietnam').\
            holiday_status_id =\
            self.env.ref('tms_modules.tms_holidays_status_bt_abroad')

        logging.info("===== END: UPDATE Leave Type on Location Type")
