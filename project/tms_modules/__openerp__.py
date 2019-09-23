# -*- coding: utf-8 -*-
{
    'name': 'AAA -Installer of TMS',
    'version': '1.1',
    'category': 'Trobz Standard Modules',
    'description': """
This module is intended to be used for One Click Deployment purpose of Trobz.
TMS.
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'analytic',
        'document',
        'hr_recruitment',
        'trobz_base',
        'trobz_target',
        'trobz_hr_active_job',
        'trobz_hr_application',
        'trobz_hr_contract',
        'trobz_hr_holiday',
        'trobz_hr_holiday_vn',
        'trobz_hr_mail_holiday',
        'trobz_hr_simple_appraisal_markdown',
        'trobz_hr_simple_appraisal_secure',
        'trobz_hr_employee_image',
        'trobz_crm',
        'trobz_report',
        'web_serialized',
        'tms_slack',
        'web_widget_text_markdown',
        'web_button_enhanced',
        'mass_editing',
        'report_xls',
        'report_xlsx',
        'trobz_hr_recruitment_interview',
        'field_secure',
        'trobz_security_safe_password',
        'trobz_security_periodical_password',
        'web_sheet_full_width',
        'mailman',
        'booking_chart',
        'trobz_hr_employee_hierarchy',
        'google_calendar',
        'web_recipients_uncheck',
        'trobz_calendar',
        'it_equipment_bonus',
        'tms_download_all_attachments',
        'web_advanced_search_x2x',
        'web_sticky_header',
        'web_readonly_bypass',
        'web_widget_color',
        'l10n_vn_country_state',
    ],
    'init_xml': [],
    'data': [
        # ============================================================
        # SECURITY SETTING - GROUP - PROFILE
        # ============================================================
        'security/res_group.xml',
        'security/ir_rule.xml',

        # ============================================================
        # EMAIL TEMPLATES DATA
        # ============================================================
        'data/mail/forge_notification_data.xml',
        'data/mail/support_notification_data.xml',
        'data/mail/email_template_data.xml',
        'data/mail/inactive_support_ticket_data.xml',

        # ============================================================
        # OTHER DATA
        # ============================================================
        'data/analytic_secondaxis_data.xml',
        'data/target_type_data.xml',
        'data/hr_holidays_status_data.xml',
        'data/ir_cron_data.xml',
        'data/ir_config_parameter_data.xml',
        'data/booking_resource_tag_data.xml',
        'data/tms_project_intensity_data.xml',
        'data/dowload_all_attachments_data.xml',
        'data/dowload_all_attachments.yml',
        'data/ir_sequence_data.xml',
        'data/tms_job_type_data.xml',
        'data/tms_location_type_data.xml',
        'data/tms_wkhtmltopdf_version_data.xml',
        'data/hr_overtime_data.xml',

        # ============================================================
        # WIZARD
        # ============================================================
        'view/wizard/functional_block_update_view.xml',
        'view/wizard/ssh_config_view.xml',
        'view/wizard/reopen_ticket_wizard_view.xml',
        'view/wizard/hr_holidays_detail_view.xml',
        'view/wizard/daily_mail_notification_view.xml',
        'view/wizard/recalculate_reactivity_view.xml',
        'view/wizard/toggle_subscribe_ticket_wizard_view.xml',
        'view/wizard/working_hours_export_wizard_view.xml',
        'view/wizard/customer_support_tickets_wizard_view.xml',
        'view/wizard/hr_resource_allocation_wizard_view.xml',
        'view/wizard/customer_support_activity_wizard_view.xml',
        'view/wizard/update_subscriptions_wizard_view.xml',
        'view/wizard/global_analysis_partner_wizard_view.xml',
        'view/wizard/global_analysis_project_wizard_view.xml',
        'view/wizard/erppeek_report_wizard_view.xml',
        'view/wizard/delivery_acceptance_wizard_view.xml',
        'view/wizard/re_assign_tms_asset_wizard_view.xml',
        'view/wizard/manage_deadline_sp_ticket_wizard_view.xml',
        'view/wizard/add_comment_ticket_wizard_view.xml',
        'view/wizard/staff_working_attendance_report_view.xml',
        'view/wizard/hr_mothly_timesheet_wizard_view.xml',
        'view/wizard/hr_em_leave_summary_wizard_view.xml',
        'view/wizard/hr_dedicated_team_leave_wizard_view.xml',
        'view/wizard/tms_remove_subcribe_wizard_view.xml',
        'view/wizard/hr_config_settings_wizard_view.xml',
        'view/wizard/choose_internal_users_to_notify_wizard.xml',

        # ============================================================
        # VIEWS
        # ============================================================

        # ==========Dev============
        'view/dev/tms_forge_ticket_view.xml',
        'view/dev/tms_forge_ticket_reopening_view.xml',
        'view/dev/tms_free_delivery_view.xml',
        'view/dev/tms_delivery_view.xml',
        'view/dev/repository_view.xml',
        'view/dev/tms_free_instance_view.xml',
        'view/dev/tms_instance_view.xml',
        'view/dev/tms_project_view.xml',
        'view/dev/tms_milestone_view.xml',
        'view/dev/tms_project_feature_view.xml',
        'view/dev/tms_project_feature_group_view.xml',
        'view/dev/tms_project_feature_tag_view.xml',
        'view/dev/tms_project_feature_url_view.xml',
        'view/dev/project_support_contracts_view.xml',
        'view/dev/tms_sysadmin_view.xml',
        'view/dev/tms_project_type_view.xml',
        'view/dev/tms_framework_version_view.xml',
        'view/dev/tms_functional_block_view.xml',
        'view/dev/project_subscriber_view.xml',
        'view/dev/tms_subscriber_view.xml',
        'view/dev/tms_project_tag_view.xml',
        'view/dev/tms_ticket_task_type_view.xml',
        'view/dev/tms_ticket_task_type_family_view.xml',
        'view/dev/tms_docker_repo_view.xml',
        'view/dev/tms_docker_repo_users_view.xml',
        'view/dev/tms_docker_repo_tags_view.xml',
        'view/dev/calculate_kpi_view.xml',
        'view/dev/workload_estimation_view.xml',
        'view/dev/workload_estimation_risk_view.xml',
        'view/dev/tms_internal_tools_view.xml',

        # ==========Support============
        'view/support/tms_location_type_view.xml',
        'view/support/tms_support_ticket_view.xml',
        'view/support/tms_ticket_comment_view.xml',
        'view/support/tms_support_training_view.xml',

        # ==========Human Resources============
        'view/hr/hr_job_view.xml',
        'view/hr/hr_applicant_view.xml',
        'view/hr/hr_contract_view.xml',
        'view/hr/hr_appraisal_view.xml',
        'view/hr/hr_employee_capacity_view.xml',
        'view/hr/hr_employee_capacity_weekly_view.xml',
        'view/hr/hr_holidays_view.xml',
        'view/hr/hr_holidays_summary_view.xml',
        'view/hr/hr_holidays_summary_line_view.xml',
        'view/hr/hr_dedicated_resource_contract_view.xml',
        'view/hr/hr_resource_allocation_view.xml',
        'view/hr/tms_working_hour_view.xml',
        'view/hr/hr_holidays_status_view.xml',
        'view/hr/hr_resource_allocation_chart_view.xml',
        'view/hr/hr_dedicated_resource_contract_chart_view.xml',
        'view/hr/hr_team_view.xml',
        'view/hr/hr_job_type_view.xml',
        'view/hr/hr_equipment_request_view.xml',
        'view/hr/hr_employee_view.xml',
        'view/hr/tms_job_type.xml',
        'view/hr/hr_holidays_workflow.xml',
        'view/hr/hr_public_holiday_view.xml',
        'view/hr/hr_overtime_view.xml',

        # ==========Assets============
        'view/asset/tms_asset_view.xml',
        'view/asset/item_condition_view.xml',

        # ==========Analysis============
        'view/analysis/tms_activity_view.xml',
        'view/analysis/analytic_secondaxis_view.xml',
        'view/analysis/account_analytic_account_view.xml',
        'view/analysis/account_analytic_line_view.xml',
        'view/analysis/tms_invoice_line_view.xml',
        'view/analysis/activity_link_view.xml',
        'view/analysis/activity_status_view.xml',
        'view/analysis/activity_task_view.xml',

        # ==========Sales============
        'view/sale/crm_lead_view.xml',
        'view/sale/tms_project_view.xml',
        'view/sale/trobz_crm_event_view.xml',

        # ==========Base============
        'view/base/ir_cron_view.xml',
        'view/base/mailman_list_view.xml',
        'view/base/res_users_view.xml',
        'view/base/resource_calendar_attendance_view.xml',
        'view/base/res_groups_view.xml',
        'view/base/res_partner_view.xml',

        # ==========Dashboard============
        'view/board/board_board_view.xml',

        # ==========Report============
        'view/report/erppeek_report_config_view.xml',

        # ==========Mail============
        'view/mail/notification_preferences_view.xml',
        'view/mail/invite_view.xml',
        'view/mail/fetch_mail_view.xml',


        # ============================================================
        # VIEWS
        # ============================================================
        'views/tms_modules.xml',
        'views/tms_templates.xml',

        # ============================================================
        # REPORT
        # ============================================================
        'report/support/customer_support_activity.xml',
        'report/analysis/global_analysis_partner_report.xml',
        'report/analysis/global_analysis_project_report.xml',
        'report/hr/monthly_timesheet_export_report_view.xml',
        'report/hr/hr_em_leave_summary_report_xlsx.xml',
        'report/qc/fc_productivity_report_xlsx.xml',
        'report/qc/wizard/fc_productivity_wizard_view.xml',
        'report/hr/hr_dedicated_team_leave_report_xlsx.xml',
        # ============================================================
        # MENU
        # ============================================================
        "menu/analysis_menu.xml",
        "menu/sales_menu.xml",
        "menu/dev_menu.xml",
        "menu/support_menu.xml",
        "menu/hr_menu.xml",
        "menu/admin_menu.xml",
        "menu/portal_menu.xml",
        "menu/website_menu.xml",
        "menu/mail_menu.xml",
        "menu/reporting_menu.xml",

        # ============================================================
        # FUNCTION USED TO UPDATE DATA LIKE POST OBJECT
        # ============================================================
        "data/tms_update_functions_data.xml",
    ],
    'qweb': [
        'static/src/xml/base.xml',
        'static/src/xml/diff_view.xml',
        'static/src/xml/*.xml'
    ],
    'test': [],
    'demo': [],
    'js': ['static/src/js/*.js'],
    'installable': True,
    'active': False,
    'application': True,
    'post_objects': ['post.access.setup'],
}
