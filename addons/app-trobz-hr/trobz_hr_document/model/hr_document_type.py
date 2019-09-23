# -*- encoding: utf-8 -*-
from openerp import fields, models


class hr_document_type(models.Model):

    _name = "hr.document.type"

    # Columns
    name = fields.Char(string='Name', required=True)
    mandatory_issue_date = fields.Boolean(string='Mandatory Issue Date')
    mandatory_expiry_date = fields.Boolean(string='Mandatory Expiry Date')
    mandatory_issue_place = fields.Boolean(string='Mandatory Issue Place')
    mandatory_issue_by = fields.Boolean(string='Mandatory Issue By')
