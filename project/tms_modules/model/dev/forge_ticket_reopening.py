# -*- encoding: utf-8 -*-
from openerp import models, api, fields, _
from .tms_forge_ticket import TmsForgeTicket
from openerp.exceptions import Warning
from datetime import datetime
import logging


REOPENING_TYPES = [
    ('defect', 'Defect'),
    ('mis_analysis', 'Mis-analysis'),
    ('new_requirement', 'New requirement'),
    ('refactor', 'Refactoring Source Code'),
    ('invalid', 'Invalid'),
    ('deployment_issue', 'Deployment Issue')
]
REOPENING_TYPES_HELP = """
* Defect: the ticket has not been implemented as specified in the summary \
and description of the ticket.\n
* Mis-Analysis: The developer did implement the ticket as specified but \
the solution cannot solve fully the requirement of the user.\n
* Requirement: this is not linked to the initial requirement and \
could not have been guessed by the developer.\n
* Refactoring Source Code: this is used when TPM wants to reopen related \
ticket to ask DEV to adjust the source code.\n
* Invalid: this reopening time is invalid.\n
* Deployment Issue: this is problem comes from deployment
"""


class forge_ticket_reopening(models.Model):

    _name = "forge.ticket.reopening"
    _description = "Forge Ticket Reopening"
    _order = 'date desc'

    # Columns
    name = fields.Many2one(
        'tms.forge.ticket', string='Ticket ID', required=True,
        select=1, readonly=True)
    summary = fields.Char(
        string='Summary', size=512, required=True, readonly=True)
    comment = fields.Text(string='Comment', required=True)
    date = fields.Datetime(string='Date', readonly=True)
    sprint = fields.Date(string='Sprint', readonly=True)
    project_id = fields.Many2one(
        'tms.project', string='Project', readonly=True)
    last_completer_id = fields.Many2one(
        'res.users', string='Responsible', select=1, readonly=True)
    reopener_id = fields.Many2one(
        'res.users', string='Reopener', select=1, readonly=True)
    past_reopening_times = fields.Integer(
        string='Past Reopening Times', readonly=True)
    development_time = fields.Float(string='Estimate', readonly=True)
    time_spent = fields.Float(string='Time Spent at reopening', readonly=True)
    fixing_time_spent = fields.Float(
        string='Time Spent for Fix before reopening', readonly=True,
        help="ticket.time_spent - ticket.completion_time_spent "
        "at the moment the ticket is re-opened. This measures the time "
        "in case a ticket is re-opened twice or ")
    completion_date = fields.Datetime(
        string='Completion Date', readonly=True)
    reopening_type = fields.Selection(
        selection=REOPENING_TYPES, string='Reopening type', required=True,
        default='defect', help=REOPENING_TYPES_HELP)
    pre_state = fields.Selection(
        selection=TmsForgeTicket.FORGE_STATES, default='in_qa',
        string='Previous Status', readonly=True,
        help='The status of the forge ticket '
        'before this ticket was reopened.')
    proj_owner_id = fields.Many2one(
        'res.users', string='Project\'s Owner', related='project_id.owner_id',
        store=True)

    team_id = fields.Many2one(string='Team', related='project_id.team_id',
                              store=True)
    team_manager_id = fields.Many2one(
        string="Team Manager", related='project_id.team_id.team_manager',
        store=True)

    @api.model
    def get_last_author_close_ticket(self, ticket_id):
        if ticket_id:
            ttc_env = self.env['tms.ticket.comment']
            ticket_comment = ttc_env.search(
                [('tms_forge_ticket_id', '=', ticket_id),
                 ('comment', 'ilike', '%%Status%%=> Closed%%Resolution%%')],
                order='create_date DESC', limit=1)
            return ticket_comment and ticket_comment.author_id.id or False
        return False

    @api.model
    def create_forge_ticket_reopening(self, ticket):
        """
        Create a forge ticket reopening when a forge ticket is reopened.
        """
        context = self._context and self._context.copy() or {}
        context['auto_creation_forge_reopening'] = True

        ticket_reopening = self.search([('name', '=', ticket.id),
                                        ('reopening_type', '!=', 'invalid')],
                                       order='date DESC', limit=1)

        past_fixing_time = ticket_reopening and \
            ticket_reopening.fixing_time_spent or 0

        # Based on the current status of the forge ticket
        # and the reopening type, choose a proper responsible
        # (last_completer_id).
        reopening_type = context.get('reopening_type', False)
        if not reopening_type:
            raise Warning(
                'Warning', 'You must choose a reopening type.')
        if reopening_type == 'defect' and ticket.state == 'closed':
            last_completer_id = self.get_last_author_close_ticket(
                ticket.id)
        elif reopening_type == 'mis_analysis':
            last_completer_id = ticket.project_id and \
                ticket.project_id.owner_id and \
                ticket.project_id.owner_id.id or False
        elif reopening_type == 'new_requirement':
            last_completer_id = self._uid
        elif reopening_type == 'invalid':
            raise Warning(
                _('Warning'),
                _('You cannot create an invalid reopening time.'))
        else:
            last_completer_id = ticket.last_completer_id and \
                ticket.last_completer_id.id or False

        current_sprint = self.env[
            'daily.mail.notification'].get_current_sprint()

        vals = {
            'name': ticket.id,
            'summary': ticket.summary,
            'date': datetime.now(),
            'sprint': current_sprint,
            'past_reopening_times': self.search_count(
                [('name', '=', ticket.id),
                 ('reopening_type', '!=', 'invalid')]),
            'project_id': ticket.project_id and
            ticket.project_id.id or False,
            'last_completer_id': last_completer_id,
            'reopener_id': self._uid,
            'development_time': ticket.development_time,
            'time_spent': ticket.time_spent,
            'fixing_time_spent': ticket.time_spent -
            ticket.completion_time_spent - past_fixing_time,
            'completion_date': ticket.completion_date,
            'reopening_type': reopening_type,
            'comment': context.get('comment', ''),
            'pre_state': ticket.state
        }

        return self.with_context(context).create(vals)

    @api.model
    def create(self, vals):
        """
        Do NOT allow any users to create reopening manually
        through user interface.
        """
        context = self._context and self._context.copy() or {}
        if not context.get('auto_creation_forge_reopening', False):
            raise Warning(
                'Warning',
                'Forge ticket reopening can only '
                'be created when a ticket is reopened !')
        return super(
            forge_ticket_reopening, self.with_context(context)).create(vals)

    @api.multi
    def write(self, vals):
        """
        Only allow reopener to edit his reopening
        (only two fields are editable: reopening_type, comment).
        When editing reopening_type, reopener needs to update comment.
        When the edition is done, add a comment to related forge ticket.
        When a reopening is marked as invalid,
        decrease the number of reopening times of related forge ticket by 1.
        """
        # Weird behavior when saving an object that is contained inside a
        # one2many field of another object
        if len(vals.keys()) == 1 and 'name' in vals:
            return super(forge_ticket_reopening, self).write(vals)
        # When editing reopening_type, reopener needs to update comment.
        if vals.get('reopening_type', False) and \
                not vals.get('comment', False):
            raise Warning(
                _('Warning'),
                _('You must update the content of the field Comment of the '
                  'Re-opening after changing the re-opening type.'))
        # Only allow reopener to edit his reopening.
        if not self.env.user.is_admin_profile():
            # TODO: Recheck this logic
            invalid_count = self.search_count(
                [('id', 'in', self.ids), ('reopener_id', '!=', self._uid)])
            if invalid_count:
                raise Warning(
                    _('Warning'),
                    _('You can only update the forge reopenings '
                      'that you created!'))
        result = super(forge_ticket_reopening, self).write(vals)

        # When a reopening is marked as invalid, decrease the number of
        # reopening times of related forge ticket by 1.
        update_sql = ''
        update_sql_tmpl = """
            UPDATE tms_forge_ticket
            SET reopening_times = reopening_times - 1,
                write_date = NOW() AT TIME ZONE 'UTC',
                write_uid = %s
            WHERE id = %s;
        """
        update_reopening = ''
        # When the edition is done, add a comment to related forge ticket.
        ticket_comment_obj = self.env['tms.ticket.comment']
        email_template = self.env.ref(
            'tms_modules.tms_forge_notification_email_html_div_template'
        )

        for reopening in self:
            vals = {
                'type': 'comment',
                'tms_forge_ticket_id': reopening.name and
                reopening.name.id or False
            }
            ticket_comment = 'Updated the forge reopening at' +\
                ' %s:\n \tReopening type: %s\n\tComment: %s' \
                % (reopening.date, reopening.reopening_type,
                   reopening.comment)
            vals.update({'comment': ticket_comment})
            ticket_comment_obj.create(vals)
            if reopening.name.get_subscriber_email_list(vals.keys()):
                email_template._send_mail_asynchronous(
                    reopening.name.id, asynchronous=False)

            # When a reopening is marked as invalid, decrease the number of
            # reopening times of related forge ticket by 1.
            if reopening.reopening_type == 'invalid':
                update_sql += update_sql_tmpl % (self._uid, reopening.name.id)
                # Update responsible of this reopening time
                update_reopening += """
                    UPDATE forge_ticket_reopening
                    SET last_completer_id = %s,
                        write_date = NOW() AT TIME ZONE 'UTC',
                        write_uid = %s
                    WHERE id = %s;
                """ % (self._uid, self._uid, reopening.id)

        # When a reopening is marked as invalid, decrease the number of
        # reopening times of related forge ticket by 1.
        if update_sql:
            self._cr.execute(update_sql)
        # When a reopening is marked as invalid, change the responsible to the
        # user who created this reopening.
        if update_reopening:
            self._cr.execute(update_reopening)

        return result

    @api.model
    def find_status_change_comment(self, comment):
        """
        Given a comment. Find the status of the ticket after
        that comment is created.
        """
        result = ''
        comment_parts = comment.split(',')
        for comment_part in comment_parts:
            if 'Status' in comment_part:
                result = comment_part
                break
        if not result:
            logging.warning(
                '[1] No status change found. Return status Assigned.')
            return 'assigned'
        comment_parts = result.split('=>')
        if not comment_parts\
                or len(comment_parts) < 2:
            logging.warning(
                '[2] No status change found. Return status Assigned.')
            return 'assigned'
        result = comment_parts[1].strip()
        return result
