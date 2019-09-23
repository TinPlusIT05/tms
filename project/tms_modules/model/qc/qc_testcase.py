from openerp import api, models, fields

TEST_LOG_FIELDS_MAPPING = {
    # qc_testcase_field: tms_ticket_comment_field (test_log)
    "summary": "comment",
    "procedure": "test_procedure",
    "expected_result": "expected_test_result",
    "actual_result": "actual_test_result",
    "test_result": "test_result",
    "remark": "test_remark",
    "forge_ticket_id": "tms_forge_ticket_id"
}


class QcTestcase(models.Model):
    _name = "qc.testcase"
    _description = "Testcase for QC"
    _order = "sequence,id"

    summary = fields.Char(
        string="Summary",
        required=True,
        help="An explicit summary to know what we are checking",
    )

    procedure = fields.Text(
        string="Procedure",
        required=True,
        help="Steps to execute this test case",
    )

    test_date = fields.Text(
        string="Test Data",
    )

    expected_result = fields.Text(
        string="Expected Result",
        required=True,
    )

    actual_result = fields.Text(
        string="Actual Result",
    )

    test_result = fields.Selection(
        selection=[('pass', 'Pass'),
                   ('fail', 'Fail'),
                   ('suspended', 'Suspended')],
        string="Test Result"
    )

    remark = fields.Text(
        string="Remarks",
        help="In case Test result = Fail, we should log bug description here"
    )

    forge_ticket_id = fields.Many2one(
        'tms.forge.ticket',
        string='Forge Ticket ID',
    )
    no_number = fields.Integer(string='No.')
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Sequence for the handle.")

    @api.model
    def create(self, vals):
        res = super(QcTestcase, self).create(vals)
        if "test_result" in vals:
            res.create_test_log()
        return res

    @api.multi
    def write(self, vals):
        res = super(QcTestcase, self).write(vals)
        if "test_result" in vals:
            self.create_test_log()
        return res

    @api.multi
    def create_test_log(self):
        TestLog = self.env["tms.ticket.comment"]
        object_fields = self._fields

        log_ids = TestLog
        for test_case in self:
            if not test_case.test_result:
                continue

            vals = {"type": "test_log"}
            for test_case_field, test_log_field in\
                    TEST_LOG_FIELDS_MAPPING.iteritems():

                if isinstance(
                    object_fields[test_case_field],
                    fields.Many2one
                ):
                    vals[test_log_field] = test_case[test_case_field].id
                else:
                    vals[test_log_field] = test_case[test_case_field]

            log_ids |= TestLog.create(vals)

        return log_ids
