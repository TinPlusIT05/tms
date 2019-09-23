from openerp import models, fields, api, _
from openerp.exceptions import Warning


class HrAppraisalInput(models.Model):
    _name = 'hr.appraisal.input'
    _inherit = ['mail.thread']
    _description = "Appraisal input"

    name = fields.Char(
        compute='_get_name_hr_appraisal_input', string='Name',
        size=128, store=True)
    appraisal_id = fields.Many2one(
        "hr.appraisal", string="Appraisal", readonly=True, ondelete='restrict')
    author_id = fields.Many2one(
        "hr.employee", string="Author", required=True, readonly=True)
    input_line_ids = fields.One2many(
        'hr.appraisal.input.line', 'input_id', string="Input Lines",
        required=True, readonly=True,
        states={'requested': [('readonly', False)]})
    extra_comments = fields.Text(string="Extra Comments")
    state = fields.Selection(
        [('requested', 'Requested'),
         ('done', 'Done'),
         ('cancel', 'Cancelled')],
        readonly=True, track_visibility='onchange', default='requested')

    @api.multi
    def write(self, vals):
        """
        Security on appraisal input:
        - Manual update: only author can update his input
        - Auto update state from appraisal:
            HR manager can change input state to requested, cancelled
            User must change the state of appraisal input to `done` by himself
        """
        context = self._context or {}
        current_user_id = self._uid
        for appraisal in self:
            author_user_id = appraisal.author_id.user_id and \
                appraisal.author_id.user_id.id or False
            auto_update = context.get('auto_update_from_appraisal')
            if not auto_update and vals and author_user_id != current_user_id:
                raise Warning(_("Only author can update his appraisal input."))
        return super(HrAppraisalInput, self).write(vals)

    @api.multi
    def button_done(self):
        """
        Change state to done
        """
        self.write({'state': 'done'})
        self.send_email()

    @api.multi
    def button_reopen(self):
        """
        Button Done appraisal input:
        - Set state to requested
        - For a done appraisal, do not allow to reopen its inputs
        """
        for line in self:
            if line.appraisal_id.state == 'done':
                raise Warning(
                    _('You cannot reopen this appraisal input'
                      ' because the appraisal has been done already.'))
            line.state = 'requested'

    @api.multi
    def get_url(self):
        """
        Calculate the URL of current appraisal input.
        """
        ParamObj = self.env["ir.config_parameter"]
        link_template = u"{0}#id={1}&view_type=form&model=hr.appraisal.input"
        conf_val = ParamObj.get_param(
            key="web.base.url",
            default=self.get_value_from_param('tms_url_appraisal')
        )
        if not conf_val:
            conf_val = self.get_value_from_param('tms_url_appraisal')
        base_url = conf_val + '/web?db=%s' % self._cr.dbname
        link = link_template.format(base_url, self[0].id)
        return link

    @api.model
    def get_subject(self):
        self.ensure_one()
        res = '[Appraisal Input][Done]: %s by %s' % (
            self.appraisal_id.name, self.author_id.name)
        return res

    @api.model
    def get_value_from_param(self, key):
        ParamObj = self.env["ir.config_parameter"]
        res = ParamObj.get_param(key, 'False')
        return res

    @api.model
    def get_notification_mail_content(self):
        self.ensure_one()
        mail_body = '''
            Dear  HR,<br/><br/>

            Employee %s has completed the appraisal "%s"

         ''' % (self.author_id.name, self.appraisal_id.name)
        return mail_body

    @api.multi
    def send_email(self):

        email_template = self.env.ref(
            'trobz_hr_simple_appraisal.'
            'email_template_notification_appraisal_input_done'
        )
        if email_template:
            for appr_input in self:
                email_template.send_mail(
                    appr_input.id, force_send=True, raise_exception=False
                )
        return True

    @api.depends('appraisal_id', 'author_id',
                 'appraisal_id.name', 'author_id.login')
    def _get_name_hr_appraisal_input(self):
        for appraisal_input in self:
            appraisal_input.name = '%s by %s' % (
                appraisal_input.appraisal_id.name,
                appraisal_input.author_id.login)
