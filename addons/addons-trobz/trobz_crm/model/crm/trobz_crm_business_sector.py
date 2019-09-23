# -*- coding: utf-8 -*-
from openerp import fields, models


class trobz_crm_business_sector(models.Model):

    _name = 'trobz.crm.business.sector'
    _description = 'Business Sector'

    name = fields.Char('Name', size=64, required=True)
