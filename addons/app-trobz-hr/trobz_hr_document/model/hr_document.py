# -*- encoding: utf-8 -*-
from openerp import fields, models, api
from datetime import timedelta


class hr_document(models.Model):
    _name = "hr.document"

    # Columns
    name = fields.Char(string='ID / Number', required=True)
    active = fields.Boolean(string='Active', default=True)
    type_id = fields.Many2one('hr.document.type', string='Type', required=True)
    emp_id = fields.Many2one('hr.employee', string='Employee', required=True)
    issue_date = fields.Date(string='Issue Date')
    expiry_date = fields.Date(string='Expiry Date')
    issue_place = fields.Text(string='Issue Place')
    issue_by = fields.Text(string='Issue By')
    mandatory_issue_date = fields.Boolean(string='Mandatory Issue Date')
    mandatory_expiry_date = fields.Boolean(string='Mandatory Expiry Date')
    mandatory_issue_place = fields.Boolean(string='Mandatory Issue Place')
    mandatory_issue_by = fields.Boolean(string='Mandatory Issue By')
    expired = fields.Boolean(string='Expired', compute="_expired")

    @api.onchange('type_id')
    def _mandatory_fields(self):
        if self.type_id:
            self.mandatory_issue_date = self.type_id.mandatory_issue_date
            self.mandatory_expiry_date = self.type_id.mandatory_expiry_date
            self.mandatory_issue_place = self.type_id.mandatory_issue_place
            self.mandatory_issue_by = self.type_id.mandatory_issue_by

    @api.one
    @api.depends()
    def _expired(self):
        self.expired = self.expiry_date \
                       and self.expiry_date < fields.Date.today() \
                       and True or False

    @api.model
    def get_doc_expiring_30_days(self):
        res = []
        today = fields.Date.today()
        next_30_days = (fields.Date.from_string(today) +
                        timedelta(days=30)).strftime("%Y-%m-%d")
        employees = self.env['hr.employee'].search([])
        doc_types = self.env['hr.document.type'].search([])
        for emp in employees:
            for doc_type in doc_types:
                # Get latest doc
                docs = self.search([('expiry_date', '>=', today),
                                    ('expiry_date', '<=', next_30_days), ('emp_id', '=', emp.id),
                                    ('type_id', '=', doc_type.id)], order="expiry_date DESC")
                renewal_docs = self.search([('emp_id', '=', emp.id), ('type_id', '=', doc_type.id),
                                            ('expiry_date', '>', next_30_days)])
                if renewal_docs:
                    continue
                if docs:
                    res.append(docs[0])
        return res

    @api.model
    def get_doc_expired(self):
        res = []
        today = fields.Date.today()
        employees = self.env['hr.employee'].search([])
        doc_types = self.env['hr.document.type'].search([])
        for emp in employees:
            for doc_type in doc_types:
                # Get latest doc
                docs = self.search([('expiry_date', '<', today), ('emp_id', '=', emp.id),
                                    ('type_id', '=', doc_type.id)], order="expiry_date DESC")
                renewal_docs = self.search([('emp_id', '=', emp.id), ('type_id', '=', doc_type.id),
                                            ('expiry_date', '>', today)])
                if renewal_docs:
                    continue
                if docs:
                    res.append(docs[0])
        return res
