# -*- encoding: utf-8 -*-
##############################################################################

from openerp import models, api

# Groups
g_manuf_manager = 'Manufacturing / Manager'
g_manuf_viewer = 'Manufacturing / Viewer'
g_manuf_user = 'Manufacturing / User'
g_warehouse_manager = 'Warehouse / Manager'
g_warehouse_user = 'Warehouse / User'
g_purchase_user = 'Purchases / User'
g_purchase_manager = 'Purchases / Manager'
g_hr_manager = 'Human Resources / Manager'
g_hr_employee = 'Human Resources / Employee'
g_hr_officer = 'Human Resources / Officer'
g_account_accountant = 'Accounting & Finance / Accountant'
g_account_accountant_manager = 'Accounting & Finance / Financial Manager'
g_product_manager = 'Products / Manager'
g_hr_attendance = 'Technical Settings / Attendances'
g_account_invoice = 'Accounting & Finance / Invoicing & Payments'
g_create_contact = 'Contact Creation'

# Profile
p_workshop_manager = 'Workshop Manager'
p_product_manager = 'Product Manager'
p_purchase_manager = 'Purchase Manager'
p_stock_keeper = 'Stock Keeper'
p_hr_manager = 'HR Manager'
p_hr_user = 'HR User'
p_accounting = 'Accounting'

profile_def = {}
profile_def[p_workshop_manager] = [g_manuf_manager, g_warehouse_manager, g_hr_employee]
profile_def[p_purchase_manager] = [g_purchase_manager, g_manuf_viewer, g_hr_employee]
profile_def[p_stock_keeper] = [g_warehouse_user, g_manuf_viewer, g_hr_employee]
profile_def[p_product_manager] = [g_product_manager, g_hr_employee]
profile_def[p_hr_manager] = [g_hr_manager, g_hr_attendance]
profile_def[p_hr_user] = [g_hr_officer, g_hr_attendance]
profile_def[p_accounting] = [g_account_accountant_manager, g_account_accountant, g_hr_employee, g_account_invoice, g_create_contact, g_purchase_user]

class post_access_set_up(models.Model):
    _name = "post.access.setup"
    _description = "Set up the Profiles and Users"
    _auto = False

    @api.model
    def start(self):
        self.env['trobz.profile'].create_profiles(profile_def)
        return True

post_access_set_up()
