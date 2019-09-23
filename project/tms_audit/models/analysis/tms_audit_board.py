from openerp import models, fields, api
from openerp import tools
from datetime import datetime


class tms_audit_board(models.Model):

    _name = "tms.audit.board"

    # project which has less health than the others should be taken
    # care of first, we must have some action on the project
    # this field should be stored in database and auto re-calculated
    # updated automatically when one of the test result is updated
    _order = "project_health ASC"

    # ------------------------------------------------------
    # FIELD DEFINITIONS
    # ------------------------------------------------------

    last_update = fields.Datetime(
        string="Last Update", readonly=True,
        compute="compute_field_last_update"
    )

    # should link to project and should be unique
    project_id = fields.Many2one(
        "tms.project", string="Project"
    )

    # list of all test results of the current project
    audit_test_result_ids = fields.One2many(
        "tms.audit.result", readonly=True, string="Audit Test Results",
        compute="compute_field_audit_test_result_ids"
    )

    # should be displayed in percentage on the board (bootstrap progress bar)
    project_health = fields.Float(
        digits=(15, 2), readonly=True, string="Health",
    )

    # number of failed tests (will be displayed on progress bar as-well)
    failed_tests = fields.Integer(
        readonly=True, string="Failed", compute="compute_field_failed_tests"
    )

    # number of pass tests (will be displayed on progress bar as-well)
    pass_tests = fields.Integer(
        readonly=True, string="Pass", compute="compute_field_pass_tests"
    )

    # Error Message
    error_message = fields.Text("Health Error", help="Show error message when"
                                "auditing project")

    # auto de-active audit board of project if it's inactive
    active = fields.Boolean(related="project_id.active",
                            store=True)
    noti_trobz_audit = fields.Boolean(related="project_id.noti_trobz_audit",
                                      store=True)

    # ------------------------------------------------------
    # CONSTRAINTS
    # ------------------------------------------------------

    _sql_constraints = [
        (
            "tms_audit_board_project_id_unique",
            "UNIQUE(project_id)",
            """
            One audit board record can only be
            associated with one unique project.
            """
        )
    ]

    # ------------------------------------------------------
    # FUNCTION FIELD COMPUTE METHODS
    # ------------------------------------------------------

    # latest update of the test
    def compute_field_last_update(self):

        for _record in self:

            _record.last_update = fields.Datetime.context_timestamp(
                self, datetime.strptime(
                    _record.write_date, tools.DEFAULT_SERVER_DATETIME_FORMAT
                )
            )

    # list of tests result generated for each project
    def compute_field_audit_test_result_ids(self):

        for _record in self:
            result_ids = [test.id
                          for test in _record.project_id.audit_test_result_ids
                          if test.audit_test_id.active]
            _record.audit_test_result_ids = [(6, 0, result_ids)]

    # get total number of failed tests of project
    def compute_field_failed_tests(self):

        for _record in self:
            _record.failed_tests = len([
                test
                for test in _record.project_id.audit_test_result_ids
                if test.audit_test_id.active and test.result == "0"
            ])

    # get total number of passed test of project
    def compute_field_pass_tests(self):

        for _record in self:  # TODO
            _record.pass_tests = len([
                test
                for test in _record.project_id.audit_test_result_ids
                if test.audit_test_id.active and test.result == "1"
            ])

    # ------------------------------------------------------
    # HELPER METHODS
    # ------------------------------------------------------
    @api.multi
    def calculate_update_project_health(self):
        for _record in self:
            test_weights, cal_test_results = 0, []

            for _test in _record.audit_test_result_ids:
                # to get weight of all tests
                test_weights += _test.audit_test_id.weight

                # all test result rates = test result weight * test weight
                cal_test_results.append(
                    float(_test.result) * _test.audit_test_id.weight
                )

            # all test result rates / weight of all tests * 100
            _record.project_health = test_weights and (
                sum(cal_test_results) / test_weights) * 100

    @api.model
    def get_audit_board_percentage(self):
        percentage = self.env['ir.config_parameter'].get_param(
            'trobz_default_audit_board_percentage', '90')
        return eval(percentage)

    @api.model
    def _get_bad_projects(self):
        domain = [('project_health', '<', self.get_audit_board_percentage()),
                  ('noti_trobz_audit', '=', True)]
        return self.search(domain)

    @api.model
    def get_mail_list(self):
        bad_project = self._get_bad_projects()
        tmps = bad_project.mapped('project_id.technical_project_manager_id')
        email_list = [p.email for p in tmps if p.email]
        email_list.append('audit@lists.trobz.com')
        return ','.join(list(set(email_list)))

    @api.model
    def get_list_bad_projects_info(self):
        bad_project = self._get_bad_projects()
        rs = '<strong>This is a list of the projects with an audit '\
            'percentage &lt; <b style=\"color:red;\">' + str(
                self.get_audit_board_percentage()) + '%</b>.</strong>'
        rs += '<ul>'
        for p in bad_project:
            rs += '<li>%s - %s</li>' % (
                p.project_id.name,
                p.project_id.technical_project_manager_id.name)
        rs += '</ul>'
        return rs

    @api.model
    def bad_project_audit_email(self):
        bad_project = self._get_bad_projects()
        if not bad_project:
            return
        template = self.env.ref('tms_modules.email_template_bad_project_audit')
        if template:
            template._send_mail_asynchronous(template.id)
        return True

    @api.multi
    def btn_recalculate_project_health(self):
        self.calculate_update_project_health()
        return True
