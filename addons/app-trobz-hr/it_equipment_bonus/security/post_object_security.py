# -*- encoding: utf-8 -*-
from openerp import models, api


group_user = 'Human Resources / Employee'
group_hr_manager = 'Human Resources / Manager'


class it_equipment_bonus_post_object_security(models.TransientModel):
    _name = "it.equipment.bonus.post.object.security"

    @api.model
    def start(self):
        self.create_model_access_rights()
        return True

    @api.model
    def create_model_access_rights(self):

        MODEL_ACCESS_RIGHTS = {
            ('hr.equipment.category'): {
                (group_hr_manager,): [1, 1, 1, 1],
                (group_user,): [1, 0, 0, 0],
            },
            ('employee.it.bonus'): {
                (group_hr_manager,): [1, 1, 1, 1],
                (group_user,): [1, 0, 0, 0],
            },
            ('hr.equipment.request'): {
                (group_hr_manager,): [1, 1, 1, 1],
                (group_user,): [1, 1, 1, 0],
            },
        }

        return self.env['trobz.base'].with_context(
            {'module_name': 'it_equipment_bonus'}).create_model_access_rights(
            MODEL_ACCESS_RIGHTS)
