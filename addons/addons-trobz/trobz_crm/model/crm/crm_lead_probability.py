# -*- coding: utf-8 -*-
from openerp import models, fields


class CrmLeadProbability(models.Model):

    _name = "crm.lead.probability"
    _description = "Lead Probability"
    _order = "probability_percentage DESC"

    name = fields.Char("Name", required=True)
    probability_percentage = fields.Integer(
        "Conversion probability (%)", required=True)
    description = fields.Text("Description")
