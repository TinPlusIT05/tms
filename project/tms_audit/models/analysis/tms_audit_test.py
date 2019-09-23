from openerp import api, models, fields


class tms_audit_test(models.Model):

    _name = "tms.audit.test"

    # ------------------------------------
    # FIELD DEFINITIONS
    # ------------------------------------

    # name of the test
    name = fields.Char(string="Name", required=True)

    # explain what is the purpose of the test
    description = fields.Text(
        string="Description", help="What is this test used for?"
    )

    # decides the priority of the test, more score more priority
    weight = fields.Float(
        string="Weight", digits=(15, 2), required=True,
        help="Helps to decide test priority"
    )

    # this test should be activated or not
    active = fields.Boolean(string="Active", default=True)

    # ------------------------------------
    # CONSTRAINT
    # ------------------------------------

    _sql_constraints = [
        (
            "tms_audit_test_name_unique", "UNIQUE(name)",
            "Name of the test should be unique."
        )
    ]

    @api.multi
    def write(self, vals):
        res = super(tms_audit_test, self).write(vals)
        # re-calculate all project health when (de)activating one test.
        if 'active' in vals:
            boards = self.env['tms.audit.board'].search(
                [('active', '=', True)])
            if boards:
                boards.calculate_update_project_health()
        return res
