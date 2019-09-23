# -*- encoding: utf-8 -*-
from openerp.osv import osv

group_admin_profile = "Admin Profile"
group_employee_user = "Human Resources / Employee"
group_profile_trobz_package_api = "Trobz Package API Profile"


class post_object_security_tms_audit(osv.TransientModel):
    _name = 'post.object.security.tms.audit'
    _description = "Set up the Groups, Profiles and Access Rights"
    _log_access = True

    def start(self, cr, uid):
        self.create_model_access_rights(cr, uid)
        return True

    def create_model_access_rights(self, cr, uid, context=None):

        if context is None:
            context = {}

        context.update({'module_name': 'tms_audit'})

        MODEL_ACCESS_RIGHTS = {

            'tms.audit.test': {
                (group_admin_profile,): [1, 1, 1, 1],
                (group_employee_user,): [1, 0, 0, 0],
                (group_profile_trobz_package_api,): [1, 0, 1, 0]
            },

            'tms.audit.result': {
                (group_admin_profile,): [1, 1, 1, 1],
                (group_employee_user,): [1, 0, 0, 0],
                (group_profile_trobz_package_api,): [1, 1, 1, 1]
            },

            'tms.audit.board': {
                (group_admin_profile,): [1, 1, 1, 1],
                (group_employee_user,): [1, 0, 0, 0],
                (group_profile_trobz_package_api,): [1, 1, 1, 1]
            }
        }

        return self.pool.get("trobz.base").create_model_access_rights(
            cr, uid, MODEL_ACCESS_RIGHTS, context=context
        )
