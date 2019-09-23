from openerp import models, fields, api

# possible result for each audit test, value should be in string
# format because odoo treat 0 number as False and there for the
# same as unselected on the selection
audit_result_test_result = [("0", "Failed"), ("1", "Pass")]


class tms_audit_result(models.Model):

    _name = "tms.audit.result"

    # ------------------------------------
    # FIELD DEFINITIONS
    # ------------------------------------

    write_date = fields.Datetime(
        string="Last Updated", readonly=True)

    project_id = fields.Many2one(
        "tms.project", string="Project", required=True)

    audit_test_id = fields.Many2one(
        "tms.audit.test", string="Test", required=True)

    # the target to make a comparison with score
    target = fields.Char(string="Target")

    # result from the test should always be 0 or 1 (Failed|Pass)
    result = fields.Selection(audit_result_test_result, string="Result")

    # the score of the test
    score = fields.Integer(string="Test Score")

    # ------------------------------------
    # OVERRIDE METHODS (ORM)
    # ------------------------------------

    @api.model
    def create(self, vals):

        # prevent data from being flooded (if user keep the test running
        # frequently every hour) by removing the previous result of the
        # current project test
        previous_test_results = self.search([
            ("project_id", "=", vals.get("project_id")),
            ("audit_test_id", "=", vals.get("audit_test_id"))
        ])

        previous_test_results.unlink()

        result = super(tms_audit_result, self).create(vals)

        result.update_audit_board_project_health()

        return result

    @api.multi
    def write(self, vals):

        result = super(tms_audit_result, self).write(vals)

        self.update_audit_board_project_health()

        return result

    @api.multi
    def update_audit_board_project_health(self):

        board_pool = self.env["tms.audit.board"]

        for _result in self:

            # get corresponding tms.audit.board record
            board_records = board_pool.search(
                [("project_id", "=", _result.project_id.id)]
            )

            # to make sure board record is already exists before updating
            if not board_records.ids:
                board_records = board_pool.create({
                    "project_id": _result.project_id.id
                })

            # update project health
            board_records.calculate_update_project_health()

        return True
