# -*- encoding: utf-8 -*-
from openerp import models, fields


class hr_equipment_category(models.Model):
    _name = "hr.equipment.category"

    name = fields.Char('Name', required=True)
