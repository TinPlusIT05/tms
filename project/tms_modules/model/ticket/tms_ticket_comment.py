# -*- encoding: utf-8 -*-
##############################################################################
from openerp import models, fields, api
from datetime import datetime
from openerp.tools.translate import _
from openerp.exceptions import Warning, ValidationError

TEST_LOG_REQUIRED_FIELDS = {
    "comment": "Summary",
    "test_procedure": "Procedure",
    "expected_test_result": "Expected Result",
}


class tms_ticket_comment(models.Model):

    _name = "tms.ticket.comment"
    _description = "Comment on a ticket"
    _order = "name desc"
    _rec_name = "comment"

    # override order by clause only when clicking on Trobz Support Activity
    # menu
    @api.model
    def search(self, args, offset=0, limit=None,
               order=None, context=None, count=False):
        ctx = self._context and self._context.copy() or {}
        if ctx.get('orderby_date_desc', False):
            order = 'name DESC'
        return super(tms_ticket_comment, self).search(
            args, offset, limit, order, count=count)

    # get a list of defined priority on support ticket
    @api.model
    @api.depends('tms_support_ticket_id')
    def get_priorities_from_support_ticket(self):
        return self.env['tms.support.ticket'].list_priority

    # get a list of defined tiket types on support ticket
    @api.model
    def get_ticket_types_from_support_ticket(self):
        return self.env['tms.support.ticket'].list_ticket_type

    # Columns
    tms_support_ticket_id = fields.Many2one(
        'tms.support.ticket', 'Ticket',
        default=lambda self: self._context.get('tms_support_ticket_id', False)
    )
    tms_forge_ticket_id = fields.Many2one(
        'tms.forge.ticket', 'Ticket',
        default=lambda self: self._context.get('tms_forge_ticket_id', False)
    )
    name = fields.Datetime(
        'Date', readonly=True,
        default=lambda *a: fields.Datetime.now())
    type = fields.Selection(
        [('changelog', 'Changelog'),
         ('comment', 'Comment'),
         ('poke', 'Poke'), ('invalid', 'Invalid'),
         ('attachment', 'Attachment'),
         ('test_log', "Test Log")],
        string='Type', required=True, default='comment')
    comment = fields.Text('Description', required=True)
    description_change = fields.Text('Description Change', readonly=True)
    author_id = fields.Many2one(
        'res.users', 'Author', readonly=True,
        default=lambda self: self._uid
    )
    create_date = fields.Datetime('Create Date', readonly=True)
    is_notification_sent = fields.Boolean(
        'Notification Sent', default=False,
        help='True if this comment has been sent in a notification email.')

    # for support ticket (on tms.ticket.comment view)
    project_id = fields.Many2one(
        'tms.project', string='Project', help='Support_Ticket_Project',
        readonly=True)
    support_owner_id = fields.Many2one(
        'res.users', string="Assignee", help='Support Ticket Assignee',
        readonly=True)
    support_ownership_duration = fields.Char(
        size=10, string='Assignee Duration',
        help='Support Ticket Ownership Duration', readonly=True)
    support_type = fields.Selection(
        get_ticket_types_from_support_ticket,
        string='Ticket Type',
        related='tms_support_ticket_id.ticket_type', store=True,
        help='Support Ticket Type', readonly=True)
    support_summary = fields.Char(
        size=512, string="Summary", help='Support Ticket Summary',
        readonly=True)
    support_priority = fields.Selection(
        get_priorities_from_support_ticket, string='Priority',
        related='tms_support_ticket_id.priority', store=True,
        help='Support Ticket Priority', readonly=True)

    # These fields related to (get from) tms project fields
    partner_id = fields.Many2one(
        comodel='res.partner',
        related='project_id.partner_id',
        string="Customer", help="Customer from project", store=True
    )
    trobz_partner_id = fields.Many2one(
        comodel='res.partner',
        related='project_id.trobz_partner_id',
        string="Partner", help="Partner from project", store=True
    )
    is_invalid = fields.Boolean('Invalid', default=False)
    user_set_invalid_id = fields.Many2one(
        'res.users', string="User Who Set As Invalid", readonly=True)
    invalid_date = fields.Datetime('Invalidation Date', readonly=True)

    # TEST LOG
    test_procedure = fields.Text(
        'Procedure',
    )
    test_data = fields.Text(
        'Test Data',
    )
    expected_test_result = fields.Text(
        'Expected Result',
    )
    actual_test_result = fields.Text(
        'Actual Result',
    )
    test_result = fields.Selection(
        string="Test Result",
        selection=[
            ("pass", "Passed"),
            ("fail", "Failed"),
            ("suspended", "Suspended")
        ]
    )
    test_remark = fields.Text(
        "Remarks"
    )

    @api.model
    def create(self, vals):
        if 'author_id' not in vals or not vals.get('author_id', False):
            vals['author_id'] = self._context.get('uid')
        if 'name' not in vals:
            vals['name'] = str(datetime.now())
        if not vals['comment']:
            raise Warning(
                _('Forbidden action!'),
                _('Comment cannot be empty!'))

        # get previous values of support ticket before set
        if vals.get('tms_support_ticket_id', False):
            ticket_env = self.env['tms.support.ticket']
            ticket_obj = ticket_env.browse(vals['tms_support_ticket_id'])
            if ticket_obj:
                vals.update({
                    'support_type': ticket_obj.ticket_type or False,
                    'support_priority': ticket_obj.priority or False,
                    'support_summary': ticket_obj.summary or False,
                    'support_ownership_duration':
                    ticket_obj.ownership_duration or '0',
                    'project_id': ticket_obj.project_id and
                    ticket_obj.project_id.id or False,
                    'support_owner_id': ticket_obj.owner_id and
                    ticket_obj.owner_id.id or False,
                })
        else:
            if vals.get('tms_forge_ticket_id', False) is False:
                raise Warning(
                    _('Forbidden action!'),
                    _('You cannot create comment.'))

        # in reality, It doesnt usually happen this case when create a ticket
        # and mark it as invalid.
        if vals.get('is_invalid', False):
            vals.update({'user_set_invalid_id': self._uid,
                         'invalid_date': fields.Datetime.now()})

        res = super(tms_ticket_comment, self).create(vals)
        res.check_test_log_required_fields()

        return res

    @api.multi
    def write(self, vals):
        if vals.get('comment', False):
            raise Warning(
                _('Forbidden action!'),
                _('You cannot modify previous comments!'))

        for comment in self:
            if comment.is_invalid and 'is_invalid' in vals and  \
                    comment.is_invalid != vals.get('is_invalid', False):
                raise Warning(
                    _('Forbidden action!'),
                    _('Once a comment '
                      'is marked as invalid, it is not possible to change '
                      'it anymore back to valid.'))

        if vals.get('is_invalid'):
            # update { is_notification_sent: False, 'type': 'invalid'}:
            # to sent modification email again with type "invalid"
            vals.update({'user_set_invalid_id': self._uid,
                         'invalid_date': fields.Datetime.now(),
                         'type': 'invalid',
                         'is_notification_sent': False})

        res = super(tms_ticket_comment, self).write(vals)
        self.check_test_log_required_fields()

        return res

    @api.multi
    def check_test_log_required_fields(self):
        # Check fields which are required for Test Log (type = "test_log")
        object_fields = self._fields
        missed_field_labels = []
        for record in self.filtered(lambda x: x.type == "test_log"):
            for f_name, f_label in TEST_LOG_REQUIRED_FIELDS.iteritems():
                if f_name in object_fields and not record[f_name]:
                    missed_field_labels.append(f_label)

        if missed_field_labels:
            raise ValidationError(
                _("Please make sure listed field%s of Test Logs %s not "
                  "empty:\n - %s" % (
                      len(missed_field_labels) > 1 and "s" or "",
                      len(missed_field_labels) > 1 and "are" or "is",
                      "\n - ".join(missed_field_labels)
                  ))
            )
