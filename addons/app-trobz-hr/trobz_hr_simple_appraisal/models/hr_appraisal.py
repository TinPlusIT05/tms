from openerp import fields, api, models, _
from openerp.exceptions import Warning
from datetime import timedelta, datetime, date
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class HrAppraisal(models.Model):

    _name = "hr.appraisal"
    _inherit = ['mail.thread']
    _description = "Hr Appraisal"

    name = fields.Char(string='Name', size=128)
    origin_appraisal_id = fields.Many2one('hr.appraisal', string="Source")
    employee_id = fields.Many2one(
        "hr.employee", string="Employee", required=True,
        track_visibility='onchange',
        readonly=True, states={'future': [('readonly', False)]})
    manager_id = fields.Many2one(
        "hr.employee", string="Manager", required=True)
    evaluators_ids = fields.Many2many(
        "hr.employee", string="Evaluators",
        readonly=True, states={'future': [('readonly', False)]})
    evaluators_user_ids = fields.Many2many(
        "res.users", string="Evaluators' Users",
        compute='_compute_evaluators_user_ids', store=True)
    starting_date = fields.Date(
        string="Starting Date", required=True,
        help="Date at which the evaluators should be "
             "requested to do the evaluation.",
        track_visibility='onchange',
        readonly=True, states={'future': [('readonly', False)]})
    deadline = fields.Date(
        string="Deadline", required=True, track_visibility='onchange')
    interview_id = fields.Many2one(
        "calendar.event", string="Interview", track_visibility='onchange')
    interview_result = fields.Text(
        string="Interview Result", track_visibility='onchange')
    salary_information = fields.Text(
        string="Salary Information", track_visibility='onchange',
        help="For the Manager to record employees expectations")
    hr_appraisal_input_ids = fields.One2many(
        "hr.appraisal.input", "appraisal_id",
        string="List of appraisal inputs",
        readonly=True, states={'future': [('readonly', False)]})
    active = fields.Boolean(string="Active", default=True)
    input_progress = fields.Float(
        string="Input Progress", compute='_compute_input_progress',
        track_visibility='onchange')
    template_employee_id = fields.Many2one(
        'hr.appraisal.template', string="Template for Employee",
        required=True, track_visibility='onchange',
        readonly=True, states={'future': [('readonly', False)]})
    template_evaluator_id = fields.Many2one(
        'hr.appraisal.template', string="Template for Evaluator",
        required=True, track_visibility='onchange',
        readonly=True, states={'future': [('readonly', False)]})
    state = fields.Selection(
        [("future", "Future"),
         ("in_progress", "In Progress"),
         ("done", "Done"), ("cancel", "Cancelled")],
        default="future", track_visibility='onchange', readonly=True)

    @api.onchange('employee_id')
    def onchange_manager(self):
        if self.employee_id:
            self.manager_id = self.employee_id.parent_id
        else:
            self.manager_id = None

    @api.depends('evaluators_ids', 'evaluators_ids.user_id')
    def _compute_evaluators_user_ids(self):
        """
        Calculate the users of the evaluators
        Use for the security rules
        """
        for appraisal in self:
            appraisal.evaluators_user_ids = \
                [x.user_id.id for x in appraisal.evaluators_ids if x.user_id]

    @api.depends('hr_appraisal_input_ids', 'hr_appraisal_input_ids.state')
    def _compute_input_progress(self):
        """
        Input Progress (%) = number of done inputs / number of inputs * 100
        """
        for appraisal in self:
            # Need to use superuser to read all inputs that can be limited by
            # security rules.
            appraisal_inputs = appraisal.sudo().hr_appraisal_input_ids
            all_inputs = float(len(appraisal_inputs))
            if all_inputs == 0:
                appraisal.input_progress = 0
            else:
                done_inputs = 0
                for appraisal_input in appraisal_inputs:
                    if appraisal_input.sudo().state == 'done':
                        done_inputs += 1
                appraisal.input_progress = done_inputs / all_inputs * 100

    @api.multi
    def unlink(self):
        """
        Allow to delete an future/cancelled appraisal.
        """
        for appraisal in self:
            if appraisal.state not in ('future', 'cancel'):
                raise Warning(
                    _('You can only delete a future or cancelled appraisal.'))
        return super(HrAppraisal, self).unlink()

    @api.model
    def create(self, vals):
        """
        Appraisal name = {Employee name} - {Starting date}
        """
        employee_id = vals.get('employee_id')
        starting_date = vals.get('starting_date')
        if employee_id and starting_date:
            employee_name = self.env['hr.employee'].browse(employee_id).name
            vals.update(name='%s - %s' % (employee_name, starting_date))
        return super(HrAppraisal, self).create(vals)

    @api.multi
    def write(self, vals):
        """
        Update Appraisal name = {Employee name} - {Starting date}
        """
        res = super(HrAppraisal, self).write(vals)
        if 'employee_id' not in vals and 'starting_date' not in vals:
            return res
        for appraisal in self:
            employee_name = appraisal.employee_id.name
            starting_date = appraisal.starting_date
            appraisal.name = '%s - %s' % (employee_name, starting_date)
        return res

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """
        Set the employee manager to be evaluators
        """
        if self.employee_id and self.employee_id.parent_id:
            self.evaluators_ids = [self.employee_id.parent_id.id]

    @api.onchange('starting_date')
    def _onchange_starting_date(self):
        """
        Ending Date = Staring Date + 15 days
        """
        if self.starting_date:
            start_date = datetime.strptime(self.starting_date, DF)
            self.deadline = start_date + timedelta(days=14)
        else:
            self.deadline = None

    @api.multi
    def send_email_request(self):
        """
        Send email to employee and evaluators using proper email template
        """
        employee_template = self.env.ref(
            'trobz_hr_simple_appraisal.'
            'hr_appraisal_employee_request_email_template')
        evaluators_template = self.env.ref(
            'trobz_hr_simple_appraisal.'
            'hr_appraisal_evaluators_request_email_template')
        for appraisal in self:
            for appr_input in appraisal.hr_appraisal_input_ids:
                if appr_input.author_id.id == appraisal.employee_id.id:
                    employee_template.send_mail(appr_input.id)
                else:
                    evaluators_template.send_mail(appr_input.id)

    @api.model
    def generate_input_line(self, input_id, template):
        """
        @param template: recordset of hr.appraisal.template
        Generate input lines based on appraisal template lines
        """
        InputLineObj = self.env['hr.appraisal.input.line']
        if not template.appraisal_question_ids:
            return True
        vals = {'input_id': input_id}
        for question in template.appraisal_question_ids:
            vals.update({'question_id': question.id})
            InputLineObj.create(vals)

    @api.multi
    def button_start(self):
        """
        Button Start appraisal:
        - Change state to in_progress
        - Create inputs based on selected employee, evaluators
            and appraisal templates
            - For re-opened appraisal, only need to create
        - Send remind email to employee or evaluators
        """
        InputObj = self.env['hr.appraisal.input']
        for appraisal in self:
            # Create appraisal inputs for evaluators
            vals = {'appraisal_id': appraisal.id}
            for evaluator in appraisal.evaluators_ids:
                if appraisal.hr_appraisal_input_ids:
                    # If the input of this evaluator is created
                    # No need to re-create the input.
                    # Only need to do this for the re-opened appraisal.
                    # For new appraisal, create input for all evaluators
                    evaluator_input = InputObj.search(
                        [('author_id', '=', evaluator.id),
                         ('appraisal_id', '=', appraisal.id)])
                    if evaluator_input:
                        continue
                vals.update({'author_id': evaluator.id})
                appraisal_input = InputObj.create(vals)
                self.generate_input_line(
                    appraisal_input.id, appraisal.template_evaluator_id)

            # Create appraisal input for employee
            # Only need to create input for employee if it's not created
            # (in case reopened appraisal, it's created already)
            employee_id = appraisal.employee_id.id
            employee_input = InputObj.search(
                [('author_id', '=', employee_id),
                 ('appraisal_id', '=', appraisal.id)])
            if not employee_input:
                vals.update({'author_id': employee_id})
                appraisal_input = InputObj.create(vals)
                self.generate_input_line(
                    appraisal_input.id, appraisal.template_employee_id)
            # Set appraisal state to in_progress
            appraisal.state = "in_progress"
        # Send email to employee and evaluators
        self.send_email_request()

    @api.multi
    def button_done(self):
        """
        Button Done appraisal:
        - Create the Appraisal for 1 year later
        - Set status of related hr.appraisal.input to done
        """
        for appraisal in self:
            if appraisal.input_progress < 100 or \
                    not appraisal.interview_result:
                raise Warning(
                    _("You cannot mark an appraisal as done before all inputs"
                      " are not done and the interview result is not set."))
            appraisal.write({'state': 'done', 'active': True})
            appraisal.send_email()

    @api.multi
    def button_reopen(self):
        """
        Button Reopen appraisal:
        - Change state to future and activate this appraisal
        - Delete the the next Appraisal which is created from `Button Done`
        """
        for appraisal in self:
            self.search([('origin_appraisal_id', '=', appraisal.id)]).unlink()
            appraisal.write({'state': 'future', 'active': True})
            appraisal.hr_appraisal_input_ids.write({'state': 'requested'})

    @api.multi
    def button_cancel(self):
        """
        Button Cancel appraisal:
        - Change appraisal state to Cancelled, inactive appraisal
        - Change related inputs state to Cancelled as well
        """
        for appraisal in self:
            appraisal.write({'state': 'cancel', 'active': False})
            appraisal.hr_appraisal_input_ids.write({'state': 'cancel'})

    @api.model
    def run_send_email_reminder(self):
        """
        Scheduled action to send reminder email to employee and evaluators
        if starting date < today - appraisal_remind_date_nb
        """
        employee_reminder_template = self.env.ref(
            'trobz_hr_simple_appraisal.'
            'hr_appraisal_reminder_for_employee_email_template'
        )
        evaluators_reminder_template = self.env.ref(
            'trobz_hr_simple_appraisal.'
            'hr_appraisal_reminder_for_evaluator_email_template'
        )
        remind_date_nb = self.env['ir.config_parameter'].get_param(
            'appraisal_remind_date_nb', 4)
        if isinstance(remind_date_nb, (str, unicode)):
            remind_date_nb = int(remind_date_nb)
        compare_date = date.today() - timedelta(remind_date_nb)
        appraisal_inputs = self.env['hr.appraisal.input'].search([
            ('appraisal_id.starting_date', '<=', compare_date),
            ('state', '=', 'requested')])
        for appr_input in appraisal_inputs:
            if appr_input.author_id.id == \
                    appr_input.appraisal_id.employee_id.id:
                employee_reminder_template.send_mail(
                    appr_input.id, force_send=True, raise_exception=True)
            else:
                evaluators_reminder_template.send_mail(
                    appr_input.id, force_send=True, raise_exception=True)

    @api.multi
    def button_create_calendar(self):
        """
        Create a meeting for employee and evaluators
        """
        CalendarEventObj = self.env['calendar.event']
        for appraisal in self:
            if appraisal.interview_id:
                raise Warning(_("The meeting was created already."))
            if not appraisal.starting_date:
                raise Warning(_("You cannot create calendar event if you"
                                " don't set the field Starting date"))

            # Create a calendar event is not created yet
            name = "Appraisal for %s" % appraisal.employee_id.name
            result = {'name': name}
            partners = [appraisal.employee_id.user_id.partner_id.id]
            if appraisal.evaluators_ids:
                for evaluator in appraisal.evaluators_ids:
                    partners.append(evaluator.user_id.partner_id.id)
                result.update({'partner_ids':  [(6, 0, partners)]})
            else:
                raise Warning(
                    _("You cannot create calendar event "
                      "if you don't set the field Evaluators"))
            result.update({'start_datetime': appraisal.starting_date,
                           'stop_datetime': appraisal.deadline})

            appraisal.interview_id = CalendarEventObj.create(result)

    @api.multi
    def get_subject(self):
        self.ensure_one()
        res = '[Appraisal][Done]: %s' % (
            self.name)
        return res

    @api.model
    def get_value_from_param(self, key):
        ParamObj = self.env["ir.config_parameter"]
        res = ParamObj.get_param(key, 'False')
        return res

    @api.multi
    def get_url(self):
        """
        Calculate the URL of current appraisal input.
        """
        ParamObj = self.env["ir.config_parameter"]
        link_template = u"{0}#id={1}&view_type=form&model=hr.appraisal"
        conf_val = ParamObj.get_param(
            key="web.base.url",
            default=self.get_value_from_param('tms_url_appraisal')
        )
        if not conf_val:
            conf_val = self.get_value_from_param('tms_url_appraisal')
        base_url = conf_val + '/web?db=%s' % self._cr.dbname
        link = link_template.format(base_url, self[0].id)
        return link

    @api.multi
    def get_notification_mail_content(self):
        self.ensure_one()
        mail_body = '''
            Dear  HR,<br/><br/>
            
            Appraisal "%s" is completed. 

         ''' % (self.name)
        return mail_body

    @api.multi
    def send_email(self):
        email_template = self.env.ref(
            'trobz_hr_simple_appraisal.'
            'email_template_notification_appraisal_done'
        )
        if email_template:
            for appraisal in self:
                email_template.send_mail(
                    appraisal.id, force_send=True, raise_exception=False
                )
        return True
