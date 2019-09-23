# -*- encoding: UTF-8 -*-
from datetime import datetime, timedelta

from openerp import SUPERUSER_ID
from openerp import api, models, fields, _
from openerp.addons import mail  # @UnresolvedImport
from openerp.exceptions import Warning
from openerp.osv import fields as fields_v7, osv, orm
from passlib.apache import HtpasswdFile
import logging
import bcrypt


class ResUsers(models.SecureModel):
    _inherit = ['mail.thread', 'res.users']
    _name = 'res.users'
    _description = "TMS user"
    _order = "login"

    @api.multi
    def _compute_hide_calendar(self):
        """
        The tab Calendar should be visible only when:
        - A user is opening his own User form
        - Admin user is connected (uid=1)
        - User with Admin Profile is connected
        """
        logged_user = self.env.user
        for user in self:
            if logged_user.id == 1 or logged_user.is_admin_profile()\
                    or logged_user.id == user.id:
                user.hide_calendar = False
            else:
                user.hide_calendar = True

    @api.model
    def is_admin_profile(self):
        user_profile_name = self.group_profile_id and \
            self.group_profile_id.name or ''
        if user_profile_name == "Admin Profile":
            return True
        return False

    @api.multi
    @api.depends('supporter_of_project_ids',
                 'supporter_of_project_ids.project_supporter_rel_ids')
    def _get_customer_visible_user_ids(self):
        """
        Calculate field `customer_visible_user_ids`
        Get users who are the supporters of the projects
        supported by current user (User > tab Support > Supporter of Project)
        """
        # TODO: check why we must all clear_cache to make security rule re-run
        # related to security rule on res.users or using function field.
        # Conclusion: Both Stored function field and clear_cache
        #    can make the security rule worked
        self.env['ir.rule'].sudo().clear_cache()
        for user in self:
            if user.id == SUPERUSER_ID:
                # Ignore superuser
                continue

            if not isinstance(user.id, (int, long)):
                continue
            customer_visible_user_ids = []
            for project in user.supporter_of_project_ids:
                for supporter in project.project_supporter_rel_ids:
                    customer_visible_user_ids.append(supporter.id)
            user.customer_visible_user_ids = \
                customer_visible_user_ids and \
                [(6, 0, list(set(customer_visible_user_ids)))] or False

    @api.multi
    @api.depends('group_profile_id')
    def _get_is_trobz_member(self):
        for user in self:
            group_user = self.env.ref('base.group_user')
            profile_ids = group_user.profile_ids and \
                group_user.profile_ids.ids or False
            user.is_trobz_member = True if (
                profile_ids and user.group_profile_id and
                user.group_profile_id.id in profile_ids) else False

    @api.multi
    @api.depends('group_profile_id')
    def _get_is_external_dev(self):
        for user in self:
            if user.has_group('tms_modules.group_profile_external_developer'):
                user.is_external_dev = True
            else:
                user.is_external_dev = False

    @api.multi
    def _get_users_not_working_hour(self):
        """
        Get list of users who did not input enough working hours within n days
        """
        result = ''
        no_days = self.env.ref(
            'tms_modules.no_days_check_working_hour',
            raise_if_not_found=True)
        days = no_days and no_days.value or 40
        sql = """
            SELECT rus.id, rp.name
            FROM res_users rus
            JOIN res_partner rp ON rus.partner_id = rp.id
                AND rp.active = True
            WHERE rus.active = True
                AND rus.must_input_working_hour = True
                AND rus.is_trobz_member = True
            ORDER BY rp.name;
        """
        self._cr.execute(sql)
        if self._cr.rowcount > 0:
            data = self._cr.fetchall()
            for user in data:
                day_not_enough = self.check_wh_n_day_past(user[0], days)
                if not day_not_enough:
                    continue
                if len(day_not_enough) >= 10:
                    result += '<span style="font-weight: bold; ' +\
                              'color: red;">@'
                elif len(day_not_enough) >= 3:
                    result += '<span style="font-weight: bold;">@'
                else:
                    result += '<span>@'
                result += user[1] + ': </span>'
                result += ', '.join(day_not_enough)
                result += '<br/>'
        for user in self:
            user.users_not_working_hour = result

    def _set_new_password(self, cr, uid, user_id, name, value, args,
                          context=None):
        if value is False:
            # Do not update the password if no value is provided,
            # ignore silently.
            # For example web client submits False values for all empty fields.
            return
        if uid == user_id:
            # To change their own password users must use
            # the client-specific change password wizard,
            # so that the new password is immediately used for
            # further RPC requests, otherwise the user
            # will face unexpected 'Access Denied' exceptions.
            raise osv.except_osv(_('Operation Canceled'), _(
                'Please use the change password wizard (in User Preferences' +
                ' or User menu) to change your own password.'))
        self.write(cr, uid, user_id, {'password': value})

    def _get_password(self, cr, uid, ids, arg, karg, context=None):
        return dict.fromkeys(ids, '')

    _columns = {
        'new_password': fields_v7.function(
            _get_password, type='char', size=64,
            fnct_inv=_set_new_password, string='Set Password',
            help="Specify a value only when creating a user or if you're "
            "changing the user's password, otherwise leave empty. After "
            "a change of password, the user has to login again.",
            track_visibility='onchange'),
        'google_calendar_rtoken': fields_v7.char('Refresh Token',
                                                 track_visibility='onchange'),
        'google_calendar_token': fields_v7.char('User token',
                                                track_visibility='onchange'),
        'google_calendar_token_validity': fields_v7.datetime(
            'Token Validity', track_visibility='onchange'),
        'google_calendar_last_sync_date': fields_v7.datetime(
            'Last synchro date',
            track_visibility='onchange'),
        'google_calendar_cal_id': fields_v7.char(
            'Calendar ID', help='Last Calendar ID who has been synchronized.\
             If it is changed, we remove all links between GoogleID and\
              Odoo Google Internal ID',
            track_visibility='onchange')
    }
    # Computed fields
    customer_visible_user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='res_user_project_default_supporter_rel',
        column1='user_id',
        column2='supporter_id',
        compute=_get_customer_visible_user_ids, store=True,
        string="Visible Users for Customer")
    is_trobz_member = fields.Boolean(
        compute="_get_is_trobz_member",
        string='Trobz Member', store=True)
    is_external_dev = fields.Boolean(
        compute="_get_is_external_dev",
        string='External Dev?', store=True)
    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Related Employee', readonly=True)
    users_not_working_hour = fields.Char(
        compute='_get_users_not_working_hour',
        string='Users not input working hours')

    # Tracking Fields
    name = fields.Char(related='partner_id.name', inherited=True,
                       track_visibility='onchange')
    employer_id = fields.Many2one(
        'res.partner', 'Employer', ondelete='restrict', required=True,
        domain="[('is_company', '=', True)]", track_visibility='onchange')
    email = fields.Char('Email', track_visibility='onchange')

    # TODO: Discuss with Tu about renaming as _notif_pref_id to encourage the
    # use of get_notif_pref
    notif_pref_id = fields.Many2one(
        'notification.preferences', string='Notification Preferences',
        track_visibility='onchange')
    login = fields.Char('Login', size=64, required=True,
                        help="Used to log into the system",
                        track_visibility='onchange')
    group_profile_id = fields.Many2one('res.groups',
                                       string='Profile Group',
                                       domain=[('is_profile', '=', True)],
                                       help='The profile group of a user \
                                            which defines all the required \
                                            groups for a user.',
                                            track_visibility='onchange')
    action_id = fields.Many2one(
        'ir.actions.actions', 'Home Action',
        help="If specified, this action will be opened at log on " +
        " for this user, in addition to the standard menu.",
        track_visibility='onchange')
    active = fields.Boolean('Active', track_visibility='onchange')
    default_project_id = fields.Many2one(
        'tms.project', 'Default Project', ondelete='restrict',
        track_visibility='onchange')
    send_support_status_mail = fields.Boolean(
        'Send Support Status Mail', default=False, track_visibility='onchange')
    daily_hour = fields.Integer('Number of working hours per day', default=8,
                                track_visibility='onchange')
    must_input_working_hour = fields.Boolean('Must Input Working Hours',
                                             track_visibility='onchange')
    # mac address field

    # Normal fields
    set_default_related_partner = fields.Boolean(
        'Use Employer as Related Partner', default=False)
    has_full_sysadmin_access = fields.Boolean(
        'Full Sysadmin Access', default=False, track_visibility='onchange')
    is_sysadmin = fields.Boolean('Is Sysadmin', default=False)
    default_supporter_of_project_ids = fields.One2many(
        'tms.project', 'default_supporter_id',
        'Default Supporter of Projects',
        help="Used when clicking on the button assign to Trobz.",
        track_visibility='onchange')
    supporter_of_project_ids = fields.Many2many(
        comodel_name='tms.project',
        relation='tms_project_supporter_rel',
        column1='user_id',
        column2='project_id',
        string="Supporter of Projects",
        help="Only those people would be listed in the fields Assignee," +
        "Reporter and Subscriber of the support ticket for.",
        track_visibility='onchange')
    subscriber_of_project_ids = fields.One2many(
        "project.subscriber", 'name',
        string="Default Subscriber of Projects", track_visibility='onchange')

    host_user_ids = fields.Many2many(
        comodel_name='tms.host',
        relation='host_users_rel',
        column1='user_id',
        column2='host_id',
        string="User of Hosts",
        help="Hosts where access through ssh will be granted "
        "(with user openerp).")
    instance_user_ids = fields.Many2many(
        comodel_name='tms.instance',
        relation='tms_instance_user_rel',
        column1='user_id',
        column2='instance_id',
        string="User of Instances",
        help="Instances where access through http authentication will be "
        "granted.")
    https_password = fields.Secure(
        string="HTTP Password", security="_security_https_password")
    https_password_hashed = fields.Secure(
        string="HTTP Password Hashed",
        security="_security_https_password",
        help="Use this hash to prepare htpasswd files on instances.")
    https_password_bcrypt_hashed = fields.Secure(
        string="HTTP Password Bcrypt Hashed",
        security="_security_https_password",
        help="Use this hash for Docker Authentication Gateway.")
    hide_calendar = fields.Boolean(compute='_compute_hide_calendar')
    external_project_ids = fields.Many2many(
        "tms.project", "tms_project_external_dev_rel", "user_id", "project_id",
        string="External Project",
    )
    default_job_type_id = fields.Many2one(
        comodel_name='tms.job.type',
        string="Default Job Type"
    )
    slack_user_id = fields.Char(
        string='Slack user ID',
        help="In Slack: View user profile > Copy member ID")
    tpm_project_ids = fields.One2many(
        'tms.project', 'technical_project_manager_id',
        'TPM of Projects',
        help="Projects which user is TPM.")

    @api.multi
    @api.onchange('set_default_related_partner')
    def onchange_set_default_related_partner(self):
        for user in self:
            if user.set_default_related_partner:
                user.partner_id = user.employer_id.id
            else:
                user.partner_id = False

    @api.multi
    @api.constrains('partner_id', 'login')
    def _constrains_partner_id(self):
        for user in self:
            users = self.search(
                [('partner_id', '=', user.partner_id.id),
                 ('id', '!=', user.id)])
            if users:
                raise Warning(
                    _('Warning'),
                    _('The Related Partner of this User '
                      'is already related to another User "%s". '
                      'For specific case, you can create '
                      'an additional Contact of the Employer '
                      '(example "http-account-2").' % users[0].login)
                )

    @api.multi
    def _security_https_password(self):
        # Only by users with profile Admin or users with "Full Sysadmin Access"
        current_user = self.env.user
        is_allow = False
        for rec in self:
            if current_user.group_profile_id and\
                current_user.group_profile_id.name == 'Admin Profile' or\
                    current_user.has_full_sysadmin_access or\
                    rec.id == current_user.id:
                is_allow = True
            else:
                is_allow = False
                break
        return is_allow

    @api.constrains('has_full_sysadmin_access', 'group_profile_id')
    def _check_sysadmin_access(self):
        """
        Cannot uncheck `Full Sysadmin Access` for user with Admin Profile
        """
        # Cannot uncheck `Full Sysadmin Access` for user with Admin Profile
        if self.group_profile_id.name == 'Admin Profile' \
                and not self.has_full_sysadmin_access:
            raise Warning(
                _('Cannot uncheck `Full Sysadmin Access` for users with '
                  'Admin Profile. An Admin user always has '
                  '`Full Sysadmin Access`!')
            )

    @api.model
    def create(self, vals):
        """
        Only SUPERUSER/Admin user can create a user with
            + `Full Sysadmin Access` checked
            + Admin Profile
        """
        context = self._context and self._context.copy() or {}
        context.update({'reset_password': False})
        self.with_context(context)
        current_user = self.env.user
        group_obj = self.env['res.groups']
        if current_user.id != SUPERUSER_ID \
                and current_user.group_profile_id.name != 'Admin Profile':
            if 'group_profile_id' in vals and \
                    group_obj.browse(vals['group_profile_id']).name \
                    == 'Admin Profile':
                raise Warning(
                    _('Only Admin user can create a new user with'
                      ' Admin Profile'))
            if vals.get('has_full_sysadmin_access'):
                raise Warning(
                    _('Only Admin user can create a new user with '
                      '`Full Sysadmin Access` checked'))

        # F#12640 : Update Related User and company for Partner.contact
        # Get customer/prospect/supplier like company
        context.update({'write_tracking_fields': True,
                        'no_create_partner': vals.get('employer_id', False)})
        new_user = super(ResUsers, self.with_context(context)).create(vals)
        partner_vals = {'related_user_id': new_user.id}
        new_user.partner_id.write(partner_vals)
        new_user._get_is_external_dev()

        return new_user

    # TODO: It does not seem correct to use the api.model here.
    # How can this work? self.default_supporter_of_project_ids

    @api.model
    def remove_user_from_project_support_subscriber(self):
        tms_subscriber_env = self.env['tms.subscriber']
        project_subscriber_env = self.env['project.subscriber']
        tms_forge_subscriber_env = self.env['tms.forge.subscriber']

        # Remove this user from Supporters of projects
        if self.supporter_of_project_ids:
            self.supporter_of_project_ids = False

        if self.default_supporter_of_project_ids:
            self.default_supporter_of_project_ids.write(
                {'default_supporter_id': False})

        # Remove Subscribers of support ticket is this users
        remove_tms_subscribers = tms_subscriber_env.search(
            [('name', '=', self.id)])
        if remove_tms_subscribers:
            remove_tms_subscribers.unlink()

        remove_tms_forge_subscribers = tms_forge_subscriber_env.search(
            [('name', '=', self.id)])
        if remove_tms_forge_subscribers:
            remove_tms_forge_subscribers.unlink()

        remove_project_subscribers = project_subscriber_env.search(
            [('name', '=', self.id)])
        if remove_project_subscribers:
            remove_project_subscribers.unlink()

    @api.model
    def get_notif_pref(self):
        '''
        Returns the notification preference of the user
        or if not set from the profile of the user.
        At least one of the two must be defined.
        '''
        np = self.notif_pref_id or self.group_profile_id.notif_pref_id or False

        msg = "A notification preference should be set on the user or " + \
            "on the profile"
        assert np, msg

        return np

    @api.multi
    def change_reporter_for_support_ticket(self):
        tms_support_ticket_env = self.env['tms.support.ticket']
        ctx = self._context and self._context.copy() or {}
        # prevent sending email for this case because many tickets will be
        # change and they will sent a bulk emails that they are same as spam.
        if not ctx.get('test_support_ticket', False):
            ctx.update({'test_support_ticket': True})
        # select all tickets that they are reported by inactive users
        support_tickets = tms_support_ticket_env.search([
            ('reporter_id', 'in', self.ids)])
        logging.info("Change %d reporters for %d tickets." % (
            len(self.ids), len(support_tickets)))
        for spt in support_tickets:
            if spt.project_id.is_blocked:
                continue
            pm_id = spt.project_id.owner_id and \
                spt.project_id.owner_id.id or False

            if not pm_id or pm_id not in\
                    spt.project_id.project_supporter_rel_ids.ids:
                continue
            spt.with_context(ctx).write({'reporter_id': pm_id})
        return True

    @api.multi
    def write(self, vals):
        """
        Only SUPERUSER/Admin user can update:
            + Full Sysadmin Access
            + Profile to Admin Profile
        """
        context = self._context and self._context.copy() or {}
        group_obj = self.env['res.groups']
        project_obj = self.env['tms.project']
        current_user = self.browse(self._uid)
        default_project_id = vals.get('default_project_id', False)
        supporter_of_project_ids = vals.get('supporter_of_project_ids', [])
        for user in self:
            if 'email' in vals and not vals['email']:
                raise Warning(_(
                    'Forbidden action!',
                    'You must set an email for the user!'))

            if current_user.id != SUPERUSER_ID \
                    and current_user.group_profile_id.name != 'Admin Profile':
                if 'group_profile_id' in vals and \
                        group_obj.browse(vals['group_profile_id']).name \
                        == 'Admin Profile':
                    raise Warning(
                        _('Only Admin user can update the profile of user to'
                          ' Admin Profile'))
                if 'has_full_sysadmin_access' in vals:
                    raise Warning(
                        _('Only Admin user can update `Full Sysadmin Access`'))

            # User without Admin profiles
            # only be able to change his password
            if 'new_password' in vals and \
                    current_user.id != SUPERUSER_ID and \
                    current_user.group_profile_id.name not in (
                        'Admin Profile',
                        'Sysadmin Profile',
                        'Sysadmin Manager Profile',
                        'FC and Admin Profile') and \
                    current_user.id != user.id:
                raise Warning(
                    _('You are able to change your password only.'))

            if 'slack_user_id' in vals and \
                current_user.id != SUPERUSER_ID and \
                    current_user.group_profile_id.name not in (
                        'Admin Profile',
                        'Sysadmin Profile',
                        'Sysadmin Manager Profile'):
                raise Warning(
                    _('Only Admin user and Sysadmin can update "Slack user ID"'
                      ))

            context.update({'write_tracking_fields': True})

            if default_project_id:
                project = project_obj.browse(default_project_id)
                project_supporter_rel_ids = supporter_of_project_ids and \
                    supporter_of_project_ids[0] and \
                    supporter_of_project_ids[0][2] or \
                    user.supporter_of_project_ids.ids
                if project and project.id not in project_supporter_rel_ids:
                    raise Warning(
                        _('This user is not the supporter of project "%s"'
                          % project.name))

            if 'supporter_of_project_ids' in vals:
                new_ids = vals.get('supporter_of_project_ids', False)[0][2]
                old_ids = [support_project.id for support_project in
                           user.supporter_of_project_ids]
                removed_ids = list(set(old_ids) - set(new_ids))

                projects = project_obj.browse(removed_ids)
                # If user is Defalut Supporter of project, not allow remove
                # project out of Supporter list
                for project in projects:
                    if user.default_project_id.id == project.id:
                        raise Warning(
                            _('Warning'),
                            _('User %s must be a supporter of project %s'
                              ' because it is his/her default project.' %
                              (user.name, project.name)))

                default_project_id = default_project_id or \
                    user.default_project_id.id
                if default_project_id and \
                        default_project_id in removed_ids:
                    vals.update({
                        'default_project_id': False
                    })
                for project in projects:
                    if user.id in [project.technical_project_manager_id.id,
                                   project.tester_id.id]:
                        raise Warning(
                            _('This user is TPM or Tester of %s project, '
                              'can not remove this user out of supporter '
                              'of %s project' % (project.name, project.name)))

            # write password hash
            if vals.get("login", False) or vals.get("https_password", False):
                user_name = vals.get("login", user.login) or False
                https_password = vals.get(
                    "https_password",
                    user.read_secure(
                        fields=['https_password'])[0].get('https_password')) \
                    or False
                ht = HtpasswdFile()
                ht.set_password(user_name or '', https_password or '')
                vals.update({
                    'https_password_hashed': ht.to_string()
                })
            # write password bcrypt hash
            https_password_for_bcrypt = vals.get("https_password", False)
            if https_password_for_bcrypt:
                password_bcrypt_hash = bcrypt.hashpw(
                    https_password_for_bcrypt.encode("utf-8"),
                    bcrypt.gensalt())
                vals.update({
                    'https_password_bcrypt_hashed': password_bcrypt_hash
                })
            # update email information to employer_id(related_partner_id),
            # they are the same partner_id. Do not create a new partner
            if 'set_default_related_partner' in vals:
                if vals.get('set_default_related_partner'):
                    if vals.get('employer_id'):
                        vals.update({'partner_id': vals.get('employer_id')})
                    else:
                        vals.update({'partner_id': user.employer_id.id})
                    context.update(
                        {'is_employer': True,
                         'old_related_partner_obj': user.partner_id})
                else:
                    context.update({'is_employer': False,
                                    'user_id': user.id})
            elif not user.set_default_related_partner and 'partner_id' in vals:
                context.update({'is_employer': True,
                                'old_related_partner_obj': user.partner_id,
                                'user_id': user.id})
            elif user.set_default_related_partner and 'employer_id' in vals:
                vals.update({'partner_id': vals['employer_id']})
                context.update({'is_employer': True,
                                'old_employer_obj': user.employer_id})
            res = super(ResUsers, user.with_context(context)).write(vals)

            if vals.get('new_password', False):
                user.message_post(body='<div> &nbsp; &nbsp; &bull;\
                     <b>Password has been changed</b>')

            if 'active' in vals and not vals.get('active', False):
                profile_tms_admin = self.env.ref(
                    'tms_modules.group_profile_tms_admin')
                profile_sys_admin = self.env.ref(
                    'tms_modules.group_profile_tms_sysadmin_manager')
                if self.env.user.group_profile_id.id in \
                        (profile_tms_admin.id, profile_sys_admin.id):
                    user.sudo().change_reporter_for_support_ticket()
                    user.sudo().remove_user_from_project_support_subscriber()
                else:
                    user.change_reporter_for_support_ticket()
                    user.remove_user_from_project_support_subscriber()
        return res

    @api.onchange('group_profile_id')
    def onchange_group_profile_id(self):
        """
        - Update `is_sysadmin` and `has_full_sysadmin_access`
        according to selected profile.
        - Auto check `has_full_sysadmin_access` when change to Admin Profile
        """
        self.is_sysadmin = self.group_profile_id.is_sysadmin
        if self.group_profile_id.name == 'Admin Profile':
            self.has_full_sysadmin_access = True
        elif not self.group_profile_id.is_sysadmin:
            self.has_full_sysadmin_access = False

    @api.onchange('employer_id')
    def onchange_employer_id(self):
        """
        - If Use Employer as Related Partner is ticked, change Related Partner
        according to the new Employer.
        """

        if self.set_default_related_partner:
            self.partner_id = self.employer_id and self.employer_id.id or False

    @api.model
    def get_email_list(self):
        """
        @return email-to of email `[dev] Check Working Hour`
        """
        result = ''
        no_days = self.env.ref(
            'tms_modules.no_days_check_working_hour',
            raise_if_not_found=True)
        days = no_days and no_days.value or 40
        sql = """
            SELECT rus.id, rp.email
            FROM res_users rus
            JOIN res_partner rp ON rus.partner_id = rp.id
            WHERE rus.active = 't'
                AND rus.must_input_working_hour = 't'
                AND rus.is_trobz_member = 't'
            ORDER BY rus.id
        """
        self._cr.execute(sql)
        for user in self._cr.fetchall():
            day_not_enough = self.check_wh_n_day_past(user[0], days)
            if day_not_enough:
                result += user[1] + ','
        return result

    @api.multi
    def get_public_holidays_last_n_days(self, days):
        pulic_holiday = []
        today = datetime.now()
        lastdmonth = today - timedelta(days + 1)
        pulic_holidays = self.env['hr.public.holiday'].search(
            [('date', '>=', lastdmonth), ('date', '<=', today),
             ('is_template', '=', False)])
        for phol in pulic_holidays:
            pulic_holiday.append(phol.date)
        return pulic_holiday

    @api.model
    def check_wh_n_day_past(self, user_id, days):
        """
        Check missing working hours for a user with n days ago from now.
        """
        days = int(days)
        working_hour_obj = self.env['tms.working.hour']
        hr_employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        result = []
        pulic_holidays = self.get_public_holidays_last_n_days(days)

        hr_employees = hr_employee_obj.search([('user_id', '=', user_id)])
        if not hr_employees:
            return ["Could not find any employee with user id %d" % (user_id)]
        if len(hr_employees) > 1:
            return ["There are %s employee found with user id %d"
                    % (len(hr_employees), user_id)]

        employee_id = hr_employees[0].id

        today = datetime.now()
        contracts = contract_obj.search(
            [('employee_id', '=', employee_id),
             '|', '&', ('date_start', '<=', today),
             ('date_end', '=', False),
             '&', ('date_start', '<=', today),
             ('date_end', '>=', today)],
            order='date_start desc'
        )
        if not contracts:
            return ['Cannot check working hours for this employee,'
                    ' because no contract is defined.']
        contract = contracts[0]

        latest_contract_date = contract.date_start
        for i in range(0, days + 1):
            date = (datetime.now() - timedelta(i))
            if date.weekday() in [5, 6] or \
                    date.strftime("%Y-%m-%d") in pulic_holidays:
                # We do not check working hours on public holidays nor weekend
                continue

            if latest_contract_date \
                    and date.strftime("%Y-%m-%d") < latest_contract_date:
                # Check working hours only after the current contract has
                # started
                continue
            wh_obj = self.env(self._cr, user_id, self._context)
            working_hour_in_today = \
                working_hour_obj.with_env(
                    wh_obj).get_daily_total_working_hour(date)
            number_hours_working_schedule = 0

            if not contract.working_hours:
                return ['No working schedule found for the contract %s'
                        % contract.name]
            else:
                for attendance in contract.working_hours.attendance_ids:
                    if str(date.weekday()) == attendance.dayofweek:
                        number_hours_working_schedule += attendance.hour_to - \
                            attendance.hour_from

            if working_hour_in_today < number_hours_working_schedule:
                result.append(
                    date.strftime("%d/%m") +
                    ' (' + str(working_hour_in_today) + ' hours)')
        return result

    @api.model
    def _check_missing_working_hour(self, days):
        """
        Go through the list of users, if there is one user_id who
        has some missing working hour, return True.
        """
        users = self.search([
            ('must_input_working_hour', '=', True),
            ('is_trobz_member', '=', True)])

        for user in users:
            day_not_enough = self.check_wh_n_day_past(user.id, days)
            if day_not_enough:
                return True
        return False

    @api.model
    def send_email_remain_working_hour(self):
        """
        """
        no_days = self.env.ref(
            'tms_modules.no_days_check_working_hour',
            raise_if_not_found=True)
        days = no_days and no_days.value or 40
        if self._check_missing_working_hour(days):
            template = self.env.ref(
                'tms_modules.tms_remain_wh_email_template'
            )
            template._send_mail_asynchronous(1)
        return True

    @api.model
    def user_export_permitted(self):
        """
        Use on front-end
        Get current user profile, will be called by the client side
        to hide Odoo export feature
        """

        if self._context is None:
            self._context = {}
        record = self.sudo().browse(self._uid)
        # If current user is admin => overpass
        if self._uid == 1:
            return True
        # Customer profile are not allowed to use Openerp Export feature on
        # support ticket
        native_export_profiles = self.env['ir.config_parameter'].get_param(
            "native_export_profiles")
        native_export_profiles = eval(native_export_profiles)
        if record.group_profile_id.name in native_export_profiles:
            return False
        return True

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        context = dict(self._context)
        # Filter the support ids on project form
        if context.get('filter_supporter_ids', False):
            supporter_ids = context['filter_supporter_ids']
            if not supporter_ids:
                args = [('id', 'in', [])]
            else:
                args = [('id', 'in', supporter_ids)]
        project_id = context.get('project_id', False)
        project = self.env['tms.project'].search([('id', '=', project_id)])
        new_args = ['|']
        if project and project.project_supporter_rel_ids:
            new_args.extend(args)
            new_args.append(['id', 'in', list(project.external_dev_ids.ids)])
            args = new_args
        ids = []
        if name and operator in ['=', 'ilike']:
            ids = self.search(
                ['|', ('name', operator, name),
                 ('login', operator, name)] + args, limit=limit)
        if not ids:
            ids = self.search([('name', operator, name)] + args, limit=limit)
        return ids and ids.name_get() or self.name_get()

    @api.model
    def fields_get(self, allfields=None, write_access=True, attributes=None):
        """
        Override function
        To make the open chatter work on users
        """
        if self._context is None:
            self._context = {}
        if self._context.get('write_tracking_fields', False):
            """
                FIXME: (the one who refactor source code should notice)

                Currently res.users has some issue with open chatter so
                if we call directly super(models.SecureModel, self).fields_get
                we will get a strange error related to the group.

                for example:
                ```
                    field = self._fields[col_name]
                    KeyError: 'in_group_52'
                ```

                so temporary fix is to call from Model class directly which
                is from BaseModel, it should fix the error
            """
            return super(models.Model, self).fields_get(
                allfields=allfields, write_access=write_access,
                attributes=attributes
            )
        return super(ResUsers, self).fields_get(
            allfields=allfields, write_access=write_access,
            attributes=attributes
        )

    @api.cr_uid_ids_context
    def message_post(self, cr, uid, thread_id, context=None, **kwargs):
        """
        Override function
        To make the open chatter work on users
        """
        if isinstance(thread_id, (list, tuple)):
            thread_id = thread_id[0]
        return mail.mail_thread.mail_thread.message_post(
            self, cr, uid, thread_id, **kwargs)

    @api.cr_uid_ids_context
    def message_subscribe(self, cr, uid, ids, partner_ids, subtype_ids=None,
                          context=None):
        """
        Override function
        To make the open chatter work on users
        """
        if context is None:
            context = {}
        # not necessary for computation, but saves an access right check
        if not partner_ids:
            return True

        mail_followers_obj = self.pool.get('mail.followers')
        subtype_obj = self.pool.get('mail.message.subtype')

        user_pid = self.pool.get('res.users').browse(
            cr, uid, uid, context=context).partner_id.id
        if set(partner_ids) == set([user_pid]):
            try:
                self.check_access_rights(cr, uid, 'read')
                self.check_access_rule(cr, uid, ids, 'read')
            except (osv.except_osv, orm.except_orm):
                return False
        else:
            self.check_access_rights(cr, uid, 'write')
            self.check_access_rule(cr, uid, ids, 'write')

        existing_pids_dict = {}
        fol_ids = mail_followers_obj.search(
            cr, SUPERUSER_ID, [
                '&', '&', ('res_model', '=', self._name),
                ('res_id', 'in', ids), ('partner_id', 'in', partner_ids)])
        for fol in mail_followers_obj.browse(cr, SUPERUSER_ID, fol_ids,
                                             context=context):
            existing_pids_dict.setdefault(
                fol.res_id, set()).add(fol.partner_id.id)

        # subtype_ids specified: update already subscribed partners
        if subtype_ids and fol_ids:
            mail_followers_obj.write(cr, SUPERUSER_ID, fol_ids, {
                                     'subtype_ids': [(6, 0, subtype_ids)]},
                                     context=context)
        # subtype_ids not specified: do not update already subscribed partner,
        # fetch default subtypes for new partners
        if subtype_ids is None:
            subtype_ids = subtype_obj.search(
                cr, uid, [
                    ('default', '=', True), '|',
                    ('res_model', '=', self._name),
                    ('res_model', '=', False)], context=context)

        for record_id in ids:
            existing_pids = existing_pids_dict.get(record_id, set())
            new_pids = set(partner_ids) - existing_pids

            # subscribe new followers
            for new_pid in new_pids:
                mail_followers_obj.create(
                    cr, SUPERUSER_ID, {
                        'res_model': self._name,
                        'res_id': record_id,
                        'partner_id': new_pid,
                        'subtype_ids': [(6, 0, subtype_ids)],
                    }, context=context)

        return True

    @api.multi
    def get_secure_user_info(self):
        """
        Get hashed of http auth password and login name
        """
        user_lst = []
        for user in self:
            httpauthpasswd = user.read_secure(
                fields=['https_password_hashed'])
            user_lst.append({
                'id': user.id,
                'login': user.login,
                'https_password_hashed': httpauthpasswd[0].get(
                    'https_password_hashed'),
                'is_sysadmin': user.is_sysadmin and
                user.has_full_sysadmin_access
            })
        return user_lst
