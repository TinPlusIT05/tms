# -*- encoding: utf-8 -*-
from openerp import models, api
import logging


# Native Odoo Groups
group_all = ''
group_profile_tms_partner_manager = 'Contact Creation'
group_user = 'Human Resources / Employee'
group_hr_user = 'Human Resources / Officer'
group_hr_manager = 'Human Resources / Manager'
group_sale_salesman_all_leads = 'Sales / User: All Opportunity'
group_sale_salesman = 'Sales / User: Own Opportunity Only'
group_sale_manager = 'Sales / Manager'
group_configure_user = 'Administration / User'
group_partner_manager = 'Contact Creation'
group_portal = 'Portal'
group_document_user = 'Knowledge / User'

# TMS Groups
group_tms_dev_user = 'TMS Dev User'
group_tms_hr_job_applicant = 'TMS Hr Job Applicant'
group_tms_project_user = 'TMS Project User'
group_tms_dev_configuration_user = 'TMS Dev Configuration User'
group_tms_delivery_user = 'TMS Delivery User'
group_tms_support_viewer = 'TMS Support Viewer'
group_tms_support_user = 'TMS Support User'
group_tms_support_time_spent_access = 'TMS Access Support Time Spent'
group_tms_customer = 'TMS Customer'
group_tms_customer_read_only = 'TMS Customer Viewer'
group_tms_activity_viewer = 'TMS Activity Viewer'
group_tms_activity_user = 'TMS Activity User'
group_tms_activity_customer = 'TMS Activity Customer'
group_tms_analytic_user = 'TMS Analytic User'
group_tms_analytic_manager = 'TMS Analytic Manager'
group_tms_no_confidential_access = 'TMS No Confidential Access'
g_help_user = 'Trobz Help User'  # Ticket 1065
g_help_manager = 'Trobz Help Manager'  # Ticket 1065
group_trobz_partner = 'Trobz Partner'
group_tms_employee_user = 'TMS Employee User'
group_tms_training_user = 'TMS Training User'
group_tms_management_instance_db = 'TMS Management Instance Database'
group_tms_mailman_unsubsribe_me = 'Mailman / Unsubscribe Me'
g_mailman_manager = 'Mailman Manager'
group_sales_configuration = "Sales / Configuration"  # Ticket 12497
group_hr_appraisal_employee_manager = \
    'Human Resources / Appraisal Employee Manager'
group_tms_activity_monitoring_manager = "TMS Activity Monitoring Manager"
group_tms_activity_monitoring_user = "TMS Activity Monitoring User"
group_tms_add_user_to_host = "TMS Add User To Host"
# TMS Profiles
group_profile_hr_officer = "HR Officer Profile"
group_profile_tms_admin = 'Admin Profile'
group_profile_tms_sysadmin_manager = 'Sysadmin Manager Profile'
group_profile_tms_sysadmin = 'Sysadmin Profile'
group_profile_tms_employee = 'Employee Profile'
group_profile_fc_and_admin = 'FC and Admin Profile'
group_profile_fc_and_crm = 'FC+CRM Profile'
group_profile_crm = 'CRM Profile'
group_profile_tms_functional_consultant = 'Functional Consultant Profile'
group_profile_qc = 'QC Profile'
group_profile_tms_technical_consultant = 'Technical Consultant Profile'
group_profile_tms_technical_project_manager = 'Technical Project Manager '\
                                              'Profile'
group_profile_tms_customer = 'TMS Customer Profile'
group_profile_tms_customer_reporter_only = 'TMS Customer Reporter Only Profile'
group_profile_tms_customer_readonly = 'TMS Customer Viewer Profile'
group_profile_tms_partner = 'TMS Partner Profile'
group_profile_tms_partner_admin = 'TMS Partner Admin Profile'
group_profile_tms_delivery_team_manager = 'Team Manager Profile'
group_profile_external_developer = 'External Developer Profile'
group_external_developer = 'External Developer'
group_appraisal_input_owner = 'Appraisal Input Owner'

# TFA Group
group_tfa_api = 'TFA - API'

# TFA Profiles
group_profile_tfa_api = 'TFA - API Profile'  # Ticket 14502

# Trobz Package API Profiles
group_profile_trobz_package_api = 'Trobz Package API Profile'


class post_object_security_tms_modules(models.TransientModel):
    _name = "post.object.security.tms.modules"
    _description = "Set up the Groups, Profiles and Access Rights"

    @api.model
    def start(self):
        logging.info("======== Start Post Object Security TMS Modules =======")
        self.create_profiles()
        self.create_model_access_rights()
        self.deactivate_partner_portal_rule()
        logging.info("======= Finish Post Object Security TMS Modules =======")
        return True

    @api.model
    def _get_all_group_full_name(self):
        result = {}
        group_pool = self.env['res.groups']
        all_groups = group_pool.search(
            ['|', ('is_profile', '=', False), ('is_profile', '=', '')])
        for group in all_groups:
            result[group.full_name] = group.id
        return result

    @api.model
    def _get_all_groups_ids_by_names(self, names):
        result = []
        all_group_full_name = self._get_all_group_full_name()
        for group in names:
            if all_group_full_name.get(group, False):
                result.append(all_group_full_name[group])
        return result

    @api.model
    def _get_all_users_ids_by_logins(self, logins):
        users_pool = self.env['res.users']
        return users_pool.search([('login', 'in', logins)]) or []

    @api.model
    def create_profiles(self):
        """
        Link Groups to Group Profiles
        """
        profile_def = {}

        # ADMIN PROFILE
        profile_def[group_profile_tms_admin] = [
            group_configure_user, group_hr_manager, group_hr_user,
            group_partner_manager, group_sale_manager, group_tms_activity_user,
            group_tms_activity_viewer, group_tms_analytic_manager,
            group_tms_analytic_user, group_tms_delivery_user,
            group_tms_dev_configuration_user, group_tms_dev_user,
            group_tms_project_user, group_tms_support_user,
            group_tms_support_viewer, group_tms_training_user, group_user,
            group_tms_management_instance_db, g_mailman_manager,
            group_tms_employee_user, group_sales_configuration,
            group_tms_activity_monitoring_manager,
            group_appraisal_input_owner, group_tms_hr_job_applicant
        ]

        # SYSADMIN PROFILE
        profile_def[group_profile_tms_sysadmin] = [
            group_configure_user, group_user, g_mailman_manager,
            group_tms_delivery_user, group_partner_manager,
            group_tms_dev_configuration_user, group_tms_dev_user,
            group_tms_management_instance_db, group_tms_project_user,
            group_tms_analytic_user, group_tms_support_viewer,
            group_tms_employee_user, group_appraisal_input_owner
        ]

        # SYSADMIN MANAGER PROFILE
        profile_def[group_profile_tms_sysadmin_manager] = [
            group_configure_user, group_user, g_mailman_manager,
            group_tms_delivery_user, group_partner_manager,
            group_tms_dev_configuration_user, group_tms_dev_user,
            group_tms_management_instance_db, group_tms_project_user,
            group_tms_analytic_user, group_tms_support_viewer,
            group_hr_user, group_tms_employee_user,
            group_appraisal_input_owner
        ]

        #  TECHNICAL PROJECT MANAGER PROFILE
        profile_def[group_profile_tms_technical_project_manager] = [
            group_user, group_tms_activity_viewer, group_tms_analytic_user,
            group_tms_dev_user, group_tms_project_user,
            group_tms_delivery_user,
            group_tms_support_viewer, group_tms_support_user,
            group_tms_no_confidential_access,
            group_tms_employee_user,
            group_tms_management_instance_db,
            group_appraisal_input_owner
        ]

        #  DELIVERY TEAM MANAGER PROFILE
        profile_def[group_profile_tms_delivery_team_manager] = [
            group_user, group_tms_analytic_user,
            group_tms_dev_user, group_tms_project_user,
            group_tms_delivery_user,
            group_tms_support_viewer, group_tms_support_user,
            group_tms_no_confidential_access,
            group_tms_management_instance_db,
            group_tms_employee_user,
            group_hr_user,
            group_hr_appraisal_employee_manager,
            group_tms_training_user, group_tms_activity_monitoring_user,
            group_tms_activity_user, group_tms_analytic_manager,
            group_appraisal_input_owner,
            group_tms_add_user_to_host,
        ]

        # EMPLOYEE PROFILE
        profile_def[group_profile_tms_employee] = [
            group_user, group_tms_employee_user, group_appraisal_input_owner
        ]

        # FC AND ADMIN
        profile_def[group_profile_fc_and_admin] = [
            group_document_user, group_tms_hr_job_applicant,
            group_hr_manager, group_sale_manager, group_sale_salesman,
            group_tms_analytic_manager, group_tms_delivery_user,
            group_tms_dev_user, group_tms_no_confidential_access,
            group_tms_support_user, group_user,
            group_tms_support_viewer, group_tms_training_user,
            group_tms_employee_user,
            group_tms_management_instance_db, group_tms_activity_user,
            group_appraisal_input_owner
        ]

        # FC+CRM
        profile_def[group_profile_fc_and_crm] = [
            group_partner_manager, group_sale_manager, group_user,
            group_tms_activity_user, group_tms_analytic_user,
            group_tms_dev_user, group_tms_support_user,
            group_tms_delivery_user, group_tms_support_viewer,
            group_tms_no_confidential_access, group_tms_training_user,
            group_tms_employee_user,
            group_tms_management_instance_db,
            group_appraisal_input_owner
        ]

        # CRM
        profile_def[group_profile_crm] = [
            group_sale_manager
        ]

        # FUNCTIONAL CONSULTANT PROFILE
        profile_def[group_profile_tms_functional_consultant] = [
            group_user, group_tms_analytic_user, group_tms_dev_user,
            group_tms_delivery_user, group_tms_support_viewer,
            group_tms_support_user,
            group_tms_no_confidential_access, group_tms_training_user,
            group_tms_employee_user,
            group_tms_management_instance_db,
            group_appraisal_input_owner
        ]

        # QC PROFILE
        profile_def[group_profile_qc] = [
            group_user, group_tms_analytic_user, group_tms_dev_user,
            group_tms_delivery_user, group_tms_support_viewer,
            group_tms_no_confidential_access,
            group_tms_employee_user, group_appraisal_input_owner
        ]

        # TECHNICAL CONSULTANT PROFILE
        profile_def[group_profile_tms_technical_consultant] = [
            group_user, group_tms_analytic_user, group_tms_dev_user,
            group_tms_support_viewer, group_tms_no_confidential_access,
            group_tms_employee_user, group_appraisal_input_owner
        ]

        # CUSTOMER PROFILE
        profile_def[group_profile_tms_customer] = [
            group_portal, group_tms_support_viewer, group_tms_support_user,
            group_tms_customer, group_tms_no_confidential_access,
            group_tms_customer_read_only
        ]

        # TMS CUSTOMER REPORTER ONLY PROFILE
        profile_def[group_profile_tms_customer_reporter_only] = [
            group_portal, group_tms_support_viewer, group_tms_support_user,
            group_tms_customer, group_tms_no_confidential_access,
            group_tms_customer_read_only
        ]

        # CUSTOMER VIEWER PROFILE
        profile_def[group_profile_tms_customer_readonly] = [
            group_tms_customer_read_only, group_portal, group_tms_customer
        ]

        # PARTNER PROFILE
        profile_def[group_profile_tms_partner] = [
            group_portal, group_tms_support_viewer, group_tms_support_user,
            group_tms_customer, group_tms_no_confidential_access,
            group_trobz_partner
        ]

        # EXTERNAL DEV PROFILE
        profile_def[group_profile_external_developer] = [
            group_portal, group_external_developer,
        ]

        # PARTNER ADMIN PROFILE
        profile_def[group_profile_tms_partner_admin] = [
            group_portal, group_tms_support_viewer, group_tms_support_user,
            group_tms_customer, group_tms_no_confidential_access,
            group_trobz_partner
        ]

        # TFA-API PROFILE
        profile_def[group_profile_tfa_api] = [
            group_tfa_api, group_portal
        ]

        # Trobz Package API PROFILE
        profile_def[group_profile_trobz_package_api] = [
        ]

        # HR Officer Profile
        profile_def[group_profile_hr_officer] = [
            group_hr_appraisal_employee_manager,
            group_tms_employee_user, group_tms_training_user,
            group_hr_manager, group_tms_dev_user,
            group_tms_support_user, group_tms_analytic_user,
            group_appraisal_input_owner
        ]

        profiles_info = {}
        for profile in profile_def:
            profiles_info[profile] = self.\
                _get_all_groups_ids_by_names(profile_def[profile])
        logging.info('Start creating all profiles ...')
        profile_pool = self.env['res.groups']
        for name in profiles_info:
            profile_rcs = profile_pool.search([('name', '=', name)])
            if profile_rcs:
                profile_rcs.write(
                    {'implied_ids': [(6, 0, profiles_info[name])]})
            else:
                profile_pool.create(
                    {'name': name,
                     'implied_ids': [(6, 0, profiles_info[name])]})
        logging.info('Successfully created all profiles.')

    @api.model
    def deactivate_partner_portal_rule(self):
        """
        Deactivate the record rule
        "res_partner: portal/public: read access on my commercial partner"
        """
        logging.info('Deactivate the rule related to portal group and partner')
        part_portal_rule = self.env.ref('base.res_partner_portal_public_rule')
        if part_portal_rule and part_portal_rule.active:
            part_portal_rule.active = False
        return True

    @api.model
    def create_model_access_rights(self):
        """
        Use this SQL Query to select all access rights related to TMS project:
        select im.model, ima.name, rg.name, imd.name, ima.perm_read,
            ima.perm_write, ima.perm_create, ima.perm_unlink
        from ir_model_access ima join ir_model im on ima.model_id = im.id
        join res_groups rg on ima.group_id = rg.id
        join ir_model_data imd on rg.id = imd.res_id
        where ima.name ilike '%tms%'
        and imd.model = 'res.groups'
        order by im.model;
        """
        context = self._context and self._context.copy() or {}
        if not context:
            context = {}
        MODEL_ACCESS_RIGHTS = {
            ('tms.activity'): {
                (group_tms_support_user,): [1, 0, 0, 0],
                (group_tms_activity_viewer,): [1, 0, 0, 0],
                (group_tms_activity_user,): [1, 1, 1, 1],
                (group_tms_activity_customer,): [1, 0, 0, 0],
                (group_tms_customer_read_only,): [1, 0, 0, 0],
                (group_tms_support_viewer,
                 group_external_developer,): [1, 0, 0, 0],
                (group_tms_employee_user,): [1, 0, 0, 0],
                (group_tfa_api,): [1, 0, 0, 0],
                (group_trobz_partner,): [1, 0, 0, 0],
            },
            ('tms.delivery'): {
                (group_tms_dev_user,): [1, 1, 1, 0],
                (group_tms_delivery_user,): [1, 1, 1, 1],
                (group_external_developer,): [1, 0, 0, 0],
            },
            ('document.directory'): {
                (group_profile_tms_admin,): [1, 1, 1, 1],
            },
            ('account.analytic.account'): {
                (group_tms_analytic_user,): [1, 0, 0, 0],
                (group_tms_analytic_manager,): [1, 1, 1, 1],
            },
            ('account.analytic.line'): {
                (group_tms_analytic_user,): [1, 0, 0, 0],
                (group_tms_analytic_manager,): [1, 1, 1, 1],
            },
            ('analytic.secondaxis'): {
                (group_tms_analytic_user,): [1, 0, 0, 0],
                (group_tms_analytic_manager,): [1, 1, 1, 1],
                (group_external_developer,): [1, 1, 1, 0],
            },
            ('tms.working.hour'): {
                (group_tms_analytic_user,): [1, 1, 1, 1],
                (group_tms_employee_user,): [1, 1, 1, 1],
                (group_tms_customer,): [1, 0, 0, 0],
                (group_profile_tms_partner_admin,): [1, 0, 0, 0],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
                (group_trobz_partner,): [1, 0, 0, 0],
                (group_external_developer,): [1, 1, 1, 0],
            },
            ('hr.overtime.type'): {
                (group_tms_employee_user,): [1, 0, 0, 0],
                (group_tms_customer,): [1, 0, 0, 0],
                (group_profile_tms_partner_admin,): [1, 0, 0, 0],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
                (group_trobz_partner,): [1, 0, 0, 0],
                (group_external_developer,): [1, 0, 0, 0],
            },
            ('monthly.timesheet.sqlview'): {
                (group_hr_user,): [1, 1, 1, 1],
                (group_profile_tms_admin,): [1, 1, 1, 1],
            },
            ('monthly.overtime.sqlview'): {
                (group_hr_user,): [1, 1, 1, 1],
                (group_profile_tms_admin,): [1, 1, 1, 1],
            },
            ('hr.input.overtime'): {
                (group_hr_manager,): [1, 1, 1, 0],
                (group_tms_employee_user,): [1, 1, 1, 0],
                (group_tms_customer,): [1, 0, 0, 0],
                (group_profile_tms_partner_admin,): [1, 0, 0, 0],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
                (group_trobz_partner,): [1, 0, 0, 0],
                (group_external_developer,): [1, 1, 1, 0],
            },
            ('target'): {
                (group_user,): [1, 0, 0, 0],
                (group_configure_user,): [1, 1, 1, 1],
            },
            ('target.type'): {
                (group_user,): [1, 0, 0, 0],
                (group_tms_customer,): [1, 0, 0, 0],
                (group_configure_user,): [1, 1, 1, 1],
                (group_external_developer,): [1, 1, 1, 1],
            },
            ('res.partner'): {
                (group_tms_support_viewer,
                 group_external_developer,): [1, 0, 0, 0],
                (group_tms_customer_read_only,): [1, 0, 0, 0],
                (group_profile_tms_delivery_team_manager,): [1, 0, 0, 0],
                (group_tfa_api,): [1, 0, 0, 0],
            },
            ('ir.attachment'): {
                (group_tms_support_viewer,
                 group_external_developer,): [1, 1, 1, 1],
            },
            ('ir.model.data'): {
                (group_tms_support_viewer,
                 group_external_developer,): [1, 1, 1, 1],
            },
            ('document.storage'): {
                (group_tms_support_viewer,
                 group_external_developer,): [1, 0, 0, 0],
            },
            ('ir.exports'): {
                (group_all): [1, 0, 0, 0],
            },
            ('res.users'): {
                (group_hr_manager,): [1, 1, 1, 0],
                (group_configure_user,): [1, 1, 1, 0],
                (group_all,): [1, 1, 0, 0],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
                (group_external_developer,): [1, 0, 0, 0],
            },
            ('hr.employee'): {
                (group_hr_manager,): [1, 1, 1, 1],
                (group_tms_employee_user,): [1, 1, 1, 1],
                (group_tfa_api): [1, 0, 0, 0],
                (group_external_developer,): [1, 0, 0, 0],
                (group_user,): [1, 0, 0, 0],
            },
            ('hr.applicant_category'): {
                (group_tms_hr_job_applicant): [1, 1, 1, 1],
                (group_user,): [1, 1, 1, 0],
            },
            ('hr.applicant'): {
                (group_tms_hr_job_applicant): [1, 1, 1, 1],
                (group_user,): [1, 1, 1, 0],
            },
            ('hr.applicant.interview'): {
                (group_user,): [1, 1, 0, 0],
            },
            ('hr.recruitment.stage'): {
                (group_user,): [1, 1, 1, 0],
            },
            ('hr.recruitment.source'): {
                (group_hr_manager,): [1, 1, 1, 1],
                (group_hr_user,): [1, 1, 1, 1],
                (group_user,): [1, 0, 0, 0],
            },
            ('monthly.timesheet.sqlview'): {
                (group_hr_manager,): [1, 1, 1, 1],
            },
            ('hr.holidays'): {
                (group_tms_employee_user): [1, 1, 1, 1],
                (group_tfa_api,): [1, 0, 0, 0],
            },
            ('res.groups'): {
                (group_all): [1, 0, 0, 0],
            },
            # TODO: Check this, we already have configs for 'email.template'
            # ('email.template'): {
            #     (group_all): [1, 0, 0, 0],
            # },
            ('ir.sequence'): {
                (group_all): [1, 0, 0, 0],
            },
            ('email.template'): {
                (group_all): [1, 1, 1, 0],
            },
            ('forge.ticket.reopening'): {
                (group_tms_dev_user,): [1, 1, 1, 0],
                (group_external_developer,): [1, 0, 0, 0],
            },
            ('forge.ticket.assign'): {
                (group_user,): [1, 0, 1, 0],
            },
            ('hr.dedicated.resource.contract'): {
                (group_tms_dev_configuration_user,
                 group_profile_tms_delivery_team_manager,): [1, 1, 1, 1],
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_external_developer,): [1, 0, 0, 0],

            },
            ('hr.employee.capacity'): {
                (group_hr_manager,): [1, 1, 1, 1],
                (group_user,): [1, 1, 0, 0],
            },
            ('hr.employee.capacity.weekly'): {
                (group_hr_manager,): [1, 1, 1, 1],
                (group_user,): [1, 0, 0, 0],
            },
            ('instance.repository'): {
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_tms_project_user,): [1, 1, 1, 1],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
            },
            ('project.repository'): {
                (group_tms_project_user,): [1, 1, 1, 1],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_tms_dev_user,): [1, 0, 0, 0],
            },
            ('repository'): {
                (group_tms_project_user,): [1, 1, 0, 0],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_tms_dev_user,): [1, 0, 0, 0],
            },
            ('tms.forge.ticket'): {
                (group_tms_dev_user,): [1, 1, 1, 0],
                (group_external_developer,): [1, 1, 1, 0],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
            },
            ('qc.testcase'): {
                (group_tms_dev_user,): [1, 1, 1, 1],
                (group_external_developer,): [1, 1, 1, 1],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
            },
            # F#9914
            ('tms.free.delivery'): {
                (group_user,): [1, 0, 0, 0],
                (group_profile_tms_admin,): [1, 1, 1, 0],
                (group_profile_tms_technical_project_manager,): [1, 1, 1, 0],
            },
            ('tms.free.instance'): {
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_tms_project_user,): [1, 1, 1, 0],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
            },
            ('tms.functional.block'): {
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_tms_customer,): [1, 0, 0, 0],
                (group_tms_project_user,): [1, 1, 1, 0],
                (group_profile_tms_technical_project_manager,): [1, 1, 1, 0],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_external_developer,): [1, 0, 0, 0],
            },
            ('tms.host'): {
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
                (group_tms_add_user_to_host,): [1, 1, 0, 0],
            },
            ('tms.docker.repo'): {
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
            },
            ('tms.docker.repo.users'): {
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
            },
            ('tms.docker.repo.tags'): {
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
            },
            ('tms.host.group'): {
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
                (group_external_developer,): [1, 0, 0, 0],
            },
            ('multi.host.database'): {
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
                (group_external_developer,): [1, 0, 0, 0],
            },
            ('tms.host.virtualization'): {
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
            },
            ('tms.instance'): {
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_tms_project_user,): [1, 1, 1, 0],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
                (group_external_developer,): [1, 0, 0, 0],
            },
            ('tms.milestone'): {
                (group_tms_customer,): [1, 0, 0, 0],
                (group_tms_project_user,): [1, 1, 1, 1],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
                (group_external_developer,): [1, 0, 0, 0],
            },
            ('tms.openerp.version'): {
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_tms_dev_user,): [1, 0, 0, 0],
            },
            ('tms.operating.system'): {
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_tms_dev_user,): [1, 0, 0, 0],
            },
            ('tms.project'): {
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_tms_support_viewer,
                 group_external_developer,): [1, 0, 0, 0],
                (group_tms_project_user,): [1, 1, 1, 0],
                (group_tms_customer_read_only,): [1, 0, 0, 0],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
            },
            ('project.support.contracts'): {
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_tms_support_viewer,): [1, 0, 0, 0],
                (group_tms_project_user,): [1, 1, 1, 0],
                (group_tms_customer_read_only,): [1, 0, 0, 0],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
                (group_external_developer,): [0, 0, 0, 0],

            },
            ('tms.project.feature'): {
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_user,): [1, 0, 0, 0],
                (group_tms_training_user,): [1, 1, 1, 1],
            },
            ('tms.project.feature.group'): {
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_user,): [1, 0, 0, 0],
                (group_tms_training_user,): [1, 1, 1, 1],
            },
            ('tms.project.feature.tag'): {
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_user,): [1, 0, 0, 0],
                (group_tms_training_user,): [1, 1, 1, 1],
            },
            ('tms.project.feature.url'): {
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_user,): [1, 0, 0, 0],
                (group_tms_training_user,): [1, 1, 1, 1],
            },
            ('tms.project.type'): {
                (group_tms_support_viewer,
                 group_external_developer,): [1, 0, 0, 0],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_tms_customer_read_only,): [1, 0, 0, 0],
                (group_tms_project_user,): [1, 1, 0, 0],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
            },
            ('tms.support.ticket'): {
                (group_tms_support_user,): [1, 1, 1, 0],
                (group_tms_customer_read_only,): [1, 0, 0, 0],
                (group_tms_support_viewer,
                 group_external_developer,): [1, 0, 0, 0],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
            },
            ('tms.location.type'): {
                (group_user,): [1, 0, 0, 0],
                (group_hr_manager): [1, 1, 1, 1],
            },
            ('tms.support.training'): {
                (group_user): [1, 1, 1, 0],
                (group_hr_manager): [1, 1, 1, 1],
                (group_profile_tms_delivery_team_manager): [1, 1, 1, 1],
                (group_tms_training_user,): [1, 1, 1, 1],
                (group_tms_support_user,): [1, 0, 0, 0],
                (group_tfa_api,): [1, 0, 0, 0],
            },
            ('tms.ticket.comment'): {
                (group_tms_support_viewer,): [1, 0, 0, 0],
                (group_tms_dev_user,): [1, 1, 1, 0],
                (group_tms_support_user,): [1, 1, 1, 0],
                (group_tms_customer_read_only,): [1, 0, 0, 0],
                (group_external_developer,): [1, 1, 1, 0],
            },
            ('calculate.kpi'): {
                (group_tms_employee_user,): [1, 0, 0, 0],
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_profile_fc_and_admin,
                 group_profile_tms_delivery_team_manager): [1, 1, 1, 0],
                (group_external_developer,): [1, 0, 0, 0],
            },
            ('toggle.subscribe.ticket.wizard'): {
                (group_user,): [1, 1, 1, 1],
                (group_tms_customer,): [1, 1, 1, 1],
            },
            ('tms.framework.version'): {
                (group_user,): [1, 0, 0, 0],
                (group_tms_dev_user,): [1, 1, 1, 1],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
            },
            ('instance.database'): {
                (group_tms_management_instance_db,): [1, 1, 1, 1],
                (group_user,): [1, 0, 0, 0],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
                (group_external_developer,): [1, 0, 0, 0],
            },
            ('notification.preferences'): {
                (group_all,): [1, 0, 0, 0],
                (group_configure_user,): [1, 1, 1, 1],
            },
            ('tms.subscriber'): {
                (group_all,): [1, 0, 0, 0],
                (group_tms_support_user,): [1, 1, 1, 0],
                (group_tms_dev_user,): [1, 1, 1, 1],
                (group_external_developer,): [1, 1, 1, 0],
            },
            ('project.subscriber'): {
                (group_all,): [1, 0, 0, 0],
                (group_tms_project_user): [1, 1, 1, 1],
            },
            ('tms.project.tag'): {
                (group_profile_tms_admin,
                 group_profile_fc_and_admin,
                 group_profile_fc_and_crm,
                 group_profile_tms_functional_consultant,
                 group_profile_tms_technical_project_manager,
                 group_profile_tms_delivery_team_manager): [1, 1, 1, 1],
                (group_all,): [1, 0, 0, 0],
                (group_external_developer,): [1, 0, 0, 0],
            },
            ('mailman.list'): {
                (group_tms_mailman_unsubsribe_me): [1, 1, 0, 0],
                (group_profile_tms_delivery_team_manager,): [1, 1, 1, 0],
                (group_external_developer,): [1, 0, 0, 0],
            },
            ('hr.resource.allocation'): {
                (group_profile_tms_technical_project_manager,
                 group_profile_tms_delivery_team_manager,
                 group_profile_tms_admin,
                 group_profile_tms_sysadmin_manager,
                 group_hr_manager): [1, 1, 1, 1],
            },
            ('booking.chart'): {
                (group_user,): [1, 0, 0, 0],
            },
            ('booking.resource.tag'): {
                (group_user,): [1, 0, 0, 0],
            },
            ('booking.resource'): {
                (group_profile_tms_technical_project_manager,
                 group_profile_tms_delivery_team_manager,
                 group_profile_tms_admin,
                 group_profile_fc_and_admin,
                 group_profile_tms_sysadmin_manager,
                 group_profile_tms_sysadmin): [1, 1, 1, 1],
                (group_user,): [1, 1, 1, 0],
            },
            ('tms.ticket.task.type'): {
                (group_user,): [1, 0, 0, 0],
                (group_profile_tms_admin,): [1, 1, 1, 1],
                (group_external_developer,): [1, 0, 0, 0],
            },
            ('tms.ticket.task.type.family'): {
                (group_user,): [1, 0, 0, 0],
                (group_profile_tms_admin,): [1, 1, 1, 1],
            },
            ('res.currency'): {
                (group_profile_tms_admin,): [1, 1, 1, 1],
            },
            ('trobz.crm.event'): {
                (group_user,): [1, 0, 0, 0],
                (group_profile_tms_delivery_team_manager,): [1, 0, 0, 0],
            },
            ('crm.lead'): {
                (group_profile_tms_delivery_team_manager,): [1, 0, 0, 0],
            },
            ('crm.phonecall'): {
                (group_profile_tms_delivery_team_manager,): [1, 0, 0, 0],
            },
            ('crm.lead.probability'): {
                (group_sale_manager,): [1, 1, 1, 1],
            },
            ('trobz.crm.business.sector'): {
                (group_user,): [1, 0, 0, 0],
                (group_profile_tms_admin,): [1, 1, 1, 1],
            },
            ('tms.forge.subscriber'): {
                (group_all,): [1, 0, 0, 0],
                (group_tms_project_user): [1, 1, 1, 1],
            },
            ('hr.team'): {
                (group_user,): [1, 0, 0, 0],
                (group_hr_manager): [1, 1, 1, 1],
                (group_profile_tms_delivery_team_manager): [1, 1, 1, 1],
            },
            ('hr.job.type'): {
                (group_user,): [1, 1, 1, 0],
                (group_tms_hr_job_applicant): [1, 1, 1, 1],
            },
            ('tms.project.intensity'): {
                (group_profile_tms_admin,): [1, 1, 1, 1],
                (group_user): [1, 0, 0, 0],
            },
            ('tms.invoice.line'): {
                (group_profile_tms_admin,): [1, 0, 0, 0],
                (group_profile_tms_delivery_team_manager,): [1, 0, 0, 0],
                (group_profile_tms_functional_consultant,): [1, 0, 0, 0],
                (group_profile_fc_and_admin,): [1, 0, 0, 0],
                (group_tfa_api,): [1, 1, 1, 1],
            },
            ('res.partner.title'): {
                (group_tfa_api,): [1, 0, 0, 0],
            },
            ('res.country.state'): {
                (group_tfa_api,): [1, 0, 0, 0],
            },
            ('res.country'): {
                (group_tfa_api,): [1, 0, 0, 0],
            },
            ('mail.alias'): {
                (group_tfa_api,): [1, 0, 0, 0],
            },
            ('resource.resource'): {
                (group_tfa_api,): [1, 0, 0, 0],
            },
            ('resource.calendar'): {
                (group_tfa_api,): [1, 0, 0, 0],
            },
            ('resource.calendar.attendance'): {
                (group_tfa_api,): [1, 0, 0, 0],
            },
            ('resource.calendar.leaves'): {
                (group_tfa_api,): [1, 0, 0, 0],
            },
            ('hr.contract.type'): {
                (group_tfa_api,): [1, 0, 0, 0],
            },
            ('hr.contract'): {
                (group_tfa_api,): [1, 0, 0, 0],
            },
            ('hr.holidays.status'): {
                (group_tfa_api,): [1, 0, 0, 0],
            },
            ('hr.department'): {
                (group_tfa_api): [1, 0, 0, 0],
                (group_external_developer,): [1, 0, 0, 0],
            },
            ('hr.job'): {
                (group_tfa_api,): [1, 0, 0, 0],
                (group_user,): [1, 1, 1, 0],
                (group_tms_hr_job_applicant): [1, 1, 1, 1],
            },
            ('hr.holidays.line'): {
                (group_tfa_api,): [1, 0, 0, 0],
            },
            ('activity.task'): {
                (group_tms_activity_monitoring_manager): [1, 1, 1, 1],
                (group_tms_activity_monitoring_user): [1, 0, 0, 0],
            },

            ('activity.status'): {
                (group_tms_activity_monitoring_manager): [1, 1, 1, 1],
                (group_tms_activity_monitoring_user): [1, 0, 0, 0],
            },

            ('activity.link'): {
                (group_tms_activity_monitoring_manager): [1, 1, 1, 1],
                (group_tms_activity_monitoring_user): [1, 0, 0, 0],
            },

            # # erppeek reports
            # ## erppeek user
            ('erppeek.report.config'): {
                (group_user, group_tms_customer): [1, 0, 0, 0],
                (group_profile_tms_admin,): [1, 1, 1, 1],
            },
            ('erppeek.report.wizard'): {
                (group_user,): [1, 1, 1, 1],
                (group_tms_customer,): [1, 1, 1, 1],
            },
            ('tms.asset'): {
                (group_hr_manager,): [1, 1, 1, 1],
                (group_user,): [1, 0, 0, 0],
            },
            ('depreciation.lines'): {
                (group_hr_manager,): [1, 1, 1, 1],
                (group_user,): [1, 1, 1, 0],
            },
            ('asset.assign.history'): {
                (group_hr_manager,): [1, 1, 1, 1],
                (group_user,): [1, 1, 1, 0],
            },
            ('item.condition'): {
                (group_hr_manager,): [1, 1, 1, 1],
                (group_user,): [1, 0, 0, 0],
            },
            ('tms.job.type'): {
                (group_profile_tms_admin,): [1, 1, 1, 1],
                (group_user,): [1, 0, 0, 0],
            },
            ('tms.wkhtmltopdf.version'): {
                (group_user,): [1, 0, 0, 0],
                (group_tms_dev_user,): [1, 1, 1, 1],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
            },
            ('tms.forge.ticket.card'): {
                (group_tms_dev_user,): [1, 1, 1, 0],
                (group_external_developer,): [1, 1, 1, 0],
                (group_tms_project_user,): [1, 1, 1, 1],
            },
            ('workload.estimation'): {
                (group_profile_tms_delivery_team_manager,): [1, 1, 1, 1],
                (group_profile_tms_technical_project_manager): [1, 0, 0, 0],
                (group_user): [1, 0, 0, 0],
            },
            ('workload.estimation.risk'): {
                (group_profile_tms_delivery_team_manager,): [1, 1, 1, 1],
                (group_profile_tms_technical_project_manager): [1, 0, 0, 0],
                (group_user): [1, 0, 0, 0],
            },
            ('tms.forge.ticket.workload'): {
                (group_profile_tms_delivery_team_manager,
                 group_profile_tms_technical_project_manager): [1, 1, 1, 1],
                (group_user): [1, 0, 0, 0],
            },
            ('tms.awx.job.history'): {
                (group_user): [1, 1, 1, 1],
            },
            ('tms.internal.tools'): {
                (group_tms_dev_user,): [1, 0, 0, 0],
                (group_tms_dev_configuration_user,): [1, 1, 1, 1],
                (group_profile_trobz_package_api,): [1, 0, 0, 0],
            },
        }

        return self.env['trobz.base'].with_context(
            {'module_name': 'tms_modules'}).create_model_access_rights(
            MODEL_ACCESS_RIGHTS)

    @api.model
    def rename_profile_dtm(self):
        """
        - Rename the profile Delivery Team Manager to Team Manager
        """
        logging.info('Start rename DTM profile information...')
        sql = ("UPDATE ir_config_parameter "
               "SET value = '(\"Technical Project Manager Profile\","
               "\"Functional Consultant Profile\",\"Sysadmin Profile\","
               "\"Sysadmin Manager Profile \",\"FC and Admin Profile\","
               "\"FC+CRM Profile\",\"Team Manager Profile\")'"
               "WHERE key = 'db_instance_profiles'")
        self._cr.execute(sql)
        logging.info('Finish rename DTM profile information.')
        return True
