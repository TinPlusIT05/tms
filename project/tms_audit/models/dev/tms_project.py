from openerp import models, fields


class tms_project(models.Model):

    _inherit = "tms.project"

    audit_test_result_ids = fields.One2many(
        "tms.audit.result", "project_id", string="Audit Test Results")
