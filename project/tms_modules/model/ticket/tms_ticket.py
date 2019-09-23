# -*- encoding: utf-8 -*-
import ast
import logging
from collections import defaultdict

from openerp import models, api, fields
from openerp.exceptions import Warning
from openerp.exceptions import except_orm, AccessError


_logger = logging.getLogger(__name__)
# LIST OF TICKET RESOLUTIONS
RESOLUTION_LIST = [
    ('fixed', 'Fixed'),
    ('invalid', 'Invalid'),
    ('duplicate', 'Duplicate'),
    ('canceled', 'Canceled'),
    ('unscheduled', 'Unscheduled')
]


class TmsTicket(models.AbstractModel):

    _name = "tms.ticket"
    _description = "Ticket"
    _order = "priority DESC, create_date ASC"

    @api.model
    def get_total_time_spent(self, ticket_records):
        for ticket in ticket_records:
            total = 0
            if 'tms_working_hour_ids'in ticket._columns and \
                    ticket.tms_working_hour_ids:
                for working_hours in ticket.tms_working_hour_ids:
                    if working_hours.duration_hour:
                        total += working_hours.duration_hour
            if 'time_spent'in ticket._columns:
                ticket.time_spent = total

    @api.model
    def check_subscriber_field_per_user(
            self, ticket_model, subscriber_obj, fields_change):
        """
        For current user,
        If his applicable notification preference (ANP) has:
            - the receive_notif_for_my_action is not checked
                Not send email to him
            - the receive_notif_for_my_action is checked
                Continue to check ANP
        Check ANP:
            if the changed fields on ticket intersect with the fields
            configured on ANP is not empty, send email to him
        """
        field_objs = False
        msg = "A subscriber must have a default notification preference."
        assert subscriber_obj.tk_default_notif_pre_id, msg

        notif_obj = subscriber_obj.tk_notif_pref_id or \
            subscriber_obj.tk_default_notif_pre_id

        # If this subscriber is the current user,send the mail only
        # if receive_notif_for_my_action is True
        if self._uid == subscriber_obj.name.id:
            if not notif_obj.receive_notif_for_my_action:
                return False

        # Continue to check the applicable notification preference (ANP)
        # if fields changed exist in the forge/support fields on ANP
        # Send email to him
        if ticket_model == 'tms.forge.ticket':
            field_objs = notif_obj.forge_field_ids
        elif ticket_model == 'tms.support.ticket':
            field_objs = notif_obj.support_field_ids

        if not field_objs:
            return False

        fields_name = field_objs.mapped(lambda r: r.name)
        return list(set(fields_change).intersection(fields_name))

    @api.model
    def get_subscriber_email_list_by_ticket(
            self, ticket_model, ticket_obj, subscribers_field,
            fields_change, context):
        mail_list = ''
        assignee_id = ticket_obj.owner_id.id
        for subscriber in getattr(ticket_obj, subscribers_field):
            if not subscriber.name.active:
                _logger.warn("Subscriber %s of ticket %s is inactive." % (
                    subscriber.name.name,
                    ticket_obj.id
                ))
                _logger.warn("Remove this subscriber from the ticket")
                continue

            email = subscriber.name.email
            assert email, "The email of a subscriber is not set"

            if assignee_id == subscriber.name.id:
                # The subscriber is ticket's assignee
                # Always send email to ticket's assignee
                mail_list += email + ','
            elif context.get('create_support_ticket', False):
                # No need to check the notification preference
                # when creating a support ticket
                # Always send email for all subscribers
                mail_list += email + ','
            else:
                # Create/Update forge ticket
                # Update support ticket
                # Send email based on the notification preference
                send_email = self.check_subscriber_field_per_user(
                    ticket_model, subscriber, fields_change)
                if send_email:
                    mail_list += email + ','

        # If the support ticket has additional subscribers
        if ticket_model == 'tms.support.ticket' and \
                ticket_obj.additional_subscribers:
            mail_list = mail_list and \
                (mail_list + ticket_obj.additional_subscribers) or \
                ticket_obj.additional_subscribers
        return mail_list.rstrip(',')

    @api.model
    def get_subscriber_email_list(
            self, ids, ticket_model, subscribers_field, fields_change=[]):
        """
        Create support ticket (use context create_support_ticket)
            - subscribers' email
            - additional subscribers' email
        Update support ticket, create/update forge ticket:
            - subscribers' email following the notification preference
                configured on the current ticket
            - additional subscribers' email
        """
        context = self._context and self._context.copy() or {}
        res = {}
        for ticket in self.env[ticket_model].browse(ids):
            res[ticket.id] = self.get_subscriber_email_list_by_ticket(
                ticket_model, ticket, subscribers_field, fields_change,
                context)
        return res

    @api.model
    def _get_default_project(self):
        result = None
        current_user = self.env.user
        if not current_user.is_trobz_member and self._uid > 1:
            result = current_user.default_project_id and \
                current_user.default_project_id.id or False
        return result

    summary = fields.Char(string='Summary', required=True)
    description = fields.Text(string='Description')
    resolution = fields.Selection(
        RESOLUTION_LIST, help="""* Unscheduled:
            Will be used to allow the closing of tickets which have not been
            implemented but for which we have no more commitment
            with the customers.
        """, string="Resolution")
    reporter_id = fields.Many2one(
        'res.users', string='Reporter', required=True,
        domain="[('supporter_of_project_ids', '=like', project_id)]",
        default=lambda self: self._uid)
    project_id = fields.Many2one(
        'tms.project', string='Project', required=True,
        default=lambda self: self._get_default_project(),
        help='Automatically synchronized with related Forge/Support ticket.')
    tms_activity_id = fields.Many2one(
        'tms.activity', string='Activity',
        domain="[('project_id','=',project_id), \
            ('state','in',('planned','in_progress'))]",
        help='Automatically synchronized with related Forge/Support ticket.')
    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        help='Hidden field used for access rules')
    create_date = fields.Datetime(
        string='Creation date', readonly=True)
    write_date = fields.Datetime(
        string='Last Modification Date', readonly=True)
    closing_datetime = fields.Datetime(
        string='Closing date', readonly=True)
    subscriber_id = fields.Many2one('res.users', string='Subscriber')
    tk_default_notif_pre_id = fields.Many2one(
        comodel_name='notification.preferences',
        string="Default Notification Preference")
    tk_notif_pref_id = fields.Many2one(
        'notification.preferences', 'Ticket Notification Preference')

    @api.multi
    @api.onchange('resolution')
    def on_change_resolution(self):
        for rcs in self:
            if rcs.resolution:
                rcs.state = 'closed'

    @api.model
    def record_changes(self, obj, ids, vals, old_ticket,
                       tracked_fields, ticket_field_name):
        context = self._context and self._context.copy() or {}
        changes = []
        description_change = False
        fields_dict = obj.fields_get()
        for field in vals:
            if field in tracked_fields:
                field_label = fields_dict[field]['string']
                field_object = obj._columns[field]
                field_type = fields_dict[field]['type'].upper()
                if field_type == 'MANY2ONE':
                    # for many2one field, we check the id, don't take care
                    # about the content
                    old_id = getattr(old_ticket, field) and \
                        getattr(old_ticket, field).id
                    # TODO: Fix this warning which appears when setting the
                    # owner of a forge ticket.
                    # WARNING tms80_production_20160205 openerp.models:
                    # Comparing apples and oranges: res.users() == 90 s
                    if old_id and old_id == vals[field] or field not in vals:
                        continue
                    # if different id, get the name_get
                    old_value = getattr(old_ticket, field) and \
                        getattr(old_ticket, field).name_get() and \
                        getattr(old_ticket, field).name_get()[0] and \
                        getattr(old_ticket, field).name_get()[0][1] or \
                        'Empty'
                    if vals[field]:
                        vals_new_values = [{'id': ids[0], field:vals[field]}]
                        new_value = field_object.get(
                            self._cr, obj, ids, field, self._uid, None,
                            vals_new_values)[ids[0]][1] or 'Empty'
                    else:
                        new_value = 'Empty'

                elif field_type == 'SELECTION':
                    old_value = getattr(old_ticket, field) or 'Empty'
                    new_value = vals[field] or 'Empty'
                    old_value = old_value and \
                        old_value != 'Empty' and \
                        dict(self.fields_get(
                            allfields=[field])[
                            field]['selection'])[old_value] or 'Empty'
                    new_value = new_value and \
                        new_value != 'Empty' and \
                        dict(self.fields_get(allfields=[field])[
                            field]['selection'])[new_value] or 'Empty'
                elif field_type == 'MANY2MANY':
                    recordset = getattr(old_ticket, field)
                    old_value = self.build_list_name(recordset.mapped('name'))
                    new_ids = vals.get(field)[0][2]
                    new_recordset = recordset.browse(new_ids)
                    new_value = self.build_list_name(
                        new_recordset.mapped('name'))
                else:
                    old_value = getattr(old_ticket, field) or 'Empty'
                    new_value = vals[field] or 'Empty'

                if old_value == new_value:
                    continue

                change = {
                    'field_label': field_label,
                    'old_value': old_value,
                    'new_value': new_value
                }
                if str(field) == 'description':
                    if old_value != new_value:
                        description_change = change
                else:
                    changes.append(change)

        if len(changes) == 0 and not description_change:
            return False

        message = 'CHANGES: '
        for change in changes:
            message += '\n\t field %s: %s => %s, ' % (
                change['field_label'],
                change['old_value'], change['new_value'])

        vals_change = {
            'type': 'changelog',
            'name': str(fields.Datetime.now()),
            ticket_field_name: ids[0]}
        if description_change:
            message += '\n\t field description has been updated (more...)'
            vals_change[
                'description_change'] = 'FROM: \n\t %s\n\nTO: \n\t %s' % (
                description_change['old_value'],
                description_change['new_value'])

        if context.get('support_change_uid', False):
            # On forge ticket comment, add user changed the support ticket
            # and auto update on forge ticket
            vals_change.update({'author_id': context['support_change_uid']})

        vals_change['comment'] = message
        self.env['tms.ticket.comment'].create(vals_change)
        return True

    @api.model
    def build_list_name(self, name_list):
        result = []
        for name in name_list:
            try:
                name = str(name)
            except:
                name = name
            result.append(name)
        return result


    @api.model
    def get_last_modified_author(self, ids, ticket_model):
        res = {}
        ticket_comment_obj = self.env['tms.ticket.comment']
        for ticket in self.env[ticket_model].search([('id', 'in', ids)]):
            author = ticket and ticket.reporter_id and ticket.reporter_id and \
                ticket.reporter_id.id or False
            domain = [('type', '!=', 'poke')]
            if ticket_model == 'tms.forge.ticket':
                domain.append(('tms_forge_ticket_id', '=', ticket.id))
            elif ticket_model == 'tms.support.ticket':
                domain.append(('tms_support_ticket_id', '=', ticket.id))
            else:
                raise Warning(
                    'Error',
                    'Cannot find this model %s' % ticket_model)

            comments = ticket_comment_obj.search(
                domain, order='name DESC', limit=1)
            if comments:
                author = comments[0] and comments[0].author_id and \
                    comments[0].author_id.id or False
            res[ticket.id] = author
        return res

    @api.model
    def get_html_description(self, ids, ticket_model):
        for ticket in self.env[ticket_model].browse(ids):
            if ticket.description:
                return ticket.description.replace(
                    '\n', '<br/>').replace(' ', '&nbsp;')
            else:
                return 'No description available'
        return ''

    @api.model
    def get_last_changes(self, ids, ticket_model, field_name_comment_ids):
        """
        Returns a formatted list of changes build from the comments of the
        tickets with the field is_notification_sent set to False.
        """
        author_ids = self.get_last_modified_author(
            ids, ticket_model)

        for ticket in self.env[ticket_model].browse(ids):
            comment_list = []
            comment_ids = []
            for comment in getattr(ticket, field_name_comment_ids):

                if not comment.comment:
                    continue
                if not comment.is_notification_sent and comment.type != 'poke':
                    message = ''
                    if comment.type == 'changelog':
                        message_lines = comment.comment.split('\n')
                        first_line = True
                        message = '<br/>Change(s):<br/><ul>'
                        for message_line in message_lines:
                            if first_line:
                                first_line = False
                                continue
                            message = '%s<li>%s</li>' % (message, message_line)
                        message = '%s</ul>' % message
                        comment_ids.append(comment.id)
                    elif comment.type == 'comment':
                        message = '<br/>Comment:<br/><ul><li>%s</li></ul>' % (
                            comment.comment.replace(
                                '\n', '<br/>').replace(' ', '&nbsp;'))
                        comment_ids.append(comment.id)
                    elif comment.type == 'attachment':
                        message = \
                            '<br/><ul><li>%s</li></ul>' % (
                                comment.comment.replace(
                                    '\n', '<br/>').replace(' ', '&nbsp;'))
                        comment_ids.append(comment.id)
                    # if comment.type == 'invalid':
                    elif comment.type == 'invalid':
                        message = '<br/>' +\
                            'The below comment has been marked as <b>' +\
                            'invalid</b>:<br/><ul><li>%s</li></ul>' % (
                                comment.comment.replace('\n', '<br/>').
                                replace(' ', '&nbsp;'))
                        # author when set invalid is current user login
                        author_ids[ticket.id] = comment.user_set_invalid_id \
                            and comment.user_set_invalid_id.id or self._uid
                        comment_ids.append(comment.id)
                    comment_list.append(message)

            # self.env['tms.ticket.comment'].browse(comment_ids).write(
            #     {'is_notification_sent': True})

            if comment_list:
                author = self.env['res.users'].browse(author_ids[ticket.id])
                return 'By %s %s' % (author.name, ''.join(comment_list))
        return ''

    @api.multi
    def unlink(self):
        if self._uid != 1:
            raise Warning(
                'Forbidden action!',
                'It is not possible to delete a ticket,'
                ' instead, a ticket should be closed '
                'with the resolution "canceled" or "obsolete"!')
        return super(TmsTicket, self).unlink()

    @api.model
    def check_ticket_access(self, ticket_id, ticket_pool):
        """
            check access right of user to current
            model and current resource
        """
        try:
            pool = self.env.registry[ticket_pool._name]
            cr, uid, context = self.env.cr, self.env.uid, self.env.context

            pool.check_access_rights(cr, uid, 'read')
            pool.check_access_rule(cr, uid, [ticket_id], 'read', context)
            return True
        except (except_orm, AccessError) as e:
            _logger.info(e)
            return False

    @api.model
    def get_ticket_information(self, data):
        """
            This method is responsible for:

            - Get data for forge/support ticket to be displayed as tool-tip
            when user hover mouse on ticket link on mark-down field
                - summary
                - milestone
                - status
                - owner
                - priority

            - Get color (depending on status field of ticket) for
            forge/support ticket to display on mark-down field from
            ir.config.parameter

            - Check permission to ensure that a specific user has access right
            to read contents of a specific ticket:

                - because the system will automatically generate link for
                forge/support with matching format on form view so customer
                can accidently enter wrong support ticket number that allow
                him/her to access to support ticket of other projects.

            @param {dict} data: requested data should tricky follow the
            format below:

                data = {
                    'forge': ['12567', '12568', '12569'],
                    'support': ['8773', '8774', '8775']
                }

            @return {dict} result: returned data should tricky follow the
            format below:

                result = {
                    'forge': {
                        id: {
                            'valid': 'user has access right or not',
                            'tooltip': 'ticket tool-tip should be here',
                            'color': 'color to be displayed for the link',
                            'url': 'ticket URL with correct menu and action'
                        }
                    },
                    'support': {
                        id: {
                            'valid': 'user has access right or not',
                            'tooltip': 'ticket tool-tip should be here',
                            'color': 'color to be displayed for the link',
                            'url': 'ticket URL with correct menu and action'
                        }
                    }
                }
        """
        result = defaultdict(dict)

        # object references
        data_pool = self.env["ir.model.data"]
        config_pool = self.env["ir.config_parameter"]
        forge_pool = self.env["tms.forge.ticket"]
        support_pool = self.env["tms.support.ticket"]

        # get menu and action reference to forge ticket and support ticket
        forge_menu = data_pool.get_object(
            "tms_modules", "menu_tms_forge_ticket_list")
        support_menu = data_pool.get_object(
            "tms_modules", "menu_tms_support_ticket")

        # read color configuration as string
        config_name = "tickets_markdown_color_map"
        color_string = config_pool.get_param(config_name, "{}")
        # parse configuration string for color
        try:
            color_map = ast.literal_eval(color_string)
        except Exception:
            color_map = {}
            logging.error("System configuration for color is broken.!")

        # helper method to generate ticket link, use closure variable
        def generate_ticket_link(_type, ticket_id):
            _link = u"""
                /web#id={0}&menu_id={1}&action={2}&model={3}&view_type=form
            """
            return _link.format(
                ticket_id,
                _type == "forge" and forge_menu.id or support_menu.id,
                _type == "forge" and forge_menu.action.id or
                support_menu.action.id,
                _type == "forge" and "tms.forge.ticket" or "tms.support.ticket"
            )

        # process tickets from requested data source
        for _type, _tickets in data.iteritems():

            # original requested ticket information
            _tickets_origin_ids = map(int, _tickets)

            # decide which ticket pool, status, priority to be used
            if _type == "forge":
                _ticket_pool = forge_pool
                _ticket_status = dict(forge_pool.FORGE_STATES)
                _ticket_priority = dict(forge_pool.PRIORITY)
                _color_map = color_map.get("forge", {})
            else:
                _ticket_pool = support_pool
                _ticket_status = dict(support_pool.list_states)
                _ticket_priority = dict(support_pool.list_priority)
                _color_map = color_map.get("support", {})

            final_ticket_ids = []
            for _ticket_id in _tickets_origin_ids:
                if self.check_ticket_access(_ticket_id, _ticket_pool):
                    final_ticket_ids.append(_ticket_id)

            # browse data for these tickets and group by ID
            _tickets_map = dict(
                (_ticket.id, _ticket) for _ticket in _ticket_pool.browse(
                    final_ticket_ids
                )
            )

            for _ticket_id in _tickets_origin_ids:

                _ticket = _tickets_map.get(_ticket_id)

                # TODO: check for existence and permission
                if _ticket and _ticket.exists():
                    result[_type][_ticket_id] = {
                        "valid": True,
                        "color": _color_map.get(_ticket.state),
                        "url": generate_ticket_link(_type, _ticket_id),
                        "tooltip": u"""
                            <div>
                                <div>- Summary: {0}</div>
                                <div>- Milestone: {1}</div>
                                <div>- Status: {2}</div>
                                <div>- Assignee: {3}</div>
                                <div>- Priority: {4}</div>
                            </div>
                        """.strip().format(
                            _ticket.summary,
                            _ticket.milestone_id and
                            _ticket.milestone_id.exists() and
                            _ticket.milestone_id.name or '',
                            _ticket_status.get(
                                _ticket.state, "Undefined status"),
                            _ticket.owner_id and _ticket.owner_id.exists() and
                            _ticket.owner_id.name or '',
                            _ticket_priority.get(
                                _ticket.priority, "Undefined priority"),
                        )
                    }
                else:
                    result[_type][_ticket_id] = {
                        "valid": False,
                        "url": "#",
                        "tooltip": u"""
                            This ticket does not exist or you don't
                            have permission to view the contents, please
                            make sure the ticket number is correct.
                        """
                    }
        return result

    def get_name(self, ids):
        res = {}
        for ticket_id in ids:
            res[ticket_id] = ticket_id
        return res

    @api.model
    def _prepare_new_subscriber(self, notif_id, subs_ids,
                                new_subscriber_vals, old_subs_ids):
        new_vals_subscriber = []
        for sub_val in new_subscriber_vals:
            # Get Subscriber from new vals
            user_obj = False
            if sub_val[0] != 0:
                sub = self.env['tms.subscriber'].browse(sub_val[1])
                user_obj = sub.name
            else:
                user_id = sub_val[2]['name']
                if user_id:
                    user_obj = self.env['res.users'].browse(user_id)

            # Add/remove a user which is in list default subscriber of project.
            if user_obj and user_obj.id in subs_ids:
                if sub_val[0] == 0:
                    subs_ids.remove(user_obj.id)
                elif sub_val[0] == 2:
                    wrn = ''.join([
                        'You cannot remove subscriber %s, he/she '
                        'might be a default subscriber of the project or'
                        ' the assignee or something else... '
                        'Use notification preference to reduce'
                        ' the number of notifications.']) % user_obj.name
                    raise Warning('Forbidden action!', wrn)
                else:
                    assert "Unsupported case; this function only adds new \
                            (by force)."

        # List subscriber ready for new vals
        for subs_id in subs_ids:
            # There is a limitation and we can accept it:
            # when user changes the User in the list of Subscribers
            # from a user that needs to be added to another user.
            # For example when the assignee and the current user of the
            # subscriber are the same but the user manually updates the user
            # of that subscriber. In that case,
            # the assignee will (wrongly) not be added to the subscribers.

            if subs_id in old_subs_ids:
                # Skip all users which are in list subscriber of ticket.
                continue
            new = (0, 0, {'name': subs_id, 'tk_notif_pref_id': notif_id})
            new_vals_subscriber.append(new)
        return new_vals_subscriber

    @api.model
    def get_vals_ticket_subcribers(self, project, owner_id,
                                   vals, old_subscriber_ids):
        """
        1) Subscribers on Forge Ticket:
            - Default Forge subscribers of project.
            - assignee

        2) Subscribers on Support Ticket:
            - Default Support subscribers of project.
            - Assignee
            - Current user
            - Reporter

        IN CASE PRIORITY 'VERY HIGH' OR 'URGENT':
            - Add TPM and Tester of project.
        """
        ctx = self._context and self._context.copy() or {}

        if ctx.get('subscriber_from_forge_ticket', False):
            new_subscriber_vals = vals.get('forge_ticket_subscriber_ids', [])

            # Append forge subscribers of project to list subscriber
            subs_ids = [subscriber_obj.name.id for subscriber_obj in
                        project.forge_subscriber_ids]

        elif ctx.get('subscriber_from_support_ticket', False):
            new_subscriber_vals = vals.get('support_ticket_subscriber_ids', [])

            # Append support subscribers of project to list subscriber
            subs_ids = [subscriber_obj.name.id for subscriber_obj in
                        project.tms_project_support_subscriber_ids]

            # Append reporter of support ticket to list subscriber
            reporter_id = vals.get('reporter_id', self.reporter_id.id)
            if reporter_id and reporter_id not in subs_ids:
                subs_ids.append(reporter_id)

            # # Append current user of support ticket to list subscriber
            # if self._uid not in subs_ids:
            #     subs_ids.append(self._uid)
        else:
            subs_ids = []
            new_subscriber_vals = []

        # Append assignee of ticket to list subscriber
        if owner_id and owner_id not in subs_ids:
            subs_ids.append(owner_id)

        # Priority 'VERY HIGH' or 'URGENT': add TPM and Tester to list
        # subscriber
        new_priority = vals.get('priority', self.priority)
        if new_priority in ['very_high', 'urgent']:
            tpm_id = project.technical_project_manager_id.id
            tester_id = project.tester_id.id
            if tpm_id and tpm_id not in subs_ids:
                subs_ids.append(tpm_id)
            if tester_id and tester_id not in subs_ids:
                subs_ids.append(tester_id)

        # On support ticket, do not add a user as a subscriber if the user is
        # inactive or is not a supporter
        if ctx.get('subscriber_from_support_ticket', False):
            user_objs = self.env['res.users'].browse(subs_ids)
            for user_obj in user_objs:
                if not user_obj.active or \
                        not self.check_supporter(user_obj.id, project):
                    subs_ids.remove(user_obj.id)
        new_subscriber_vals += self._prepare_new_subscriber(
            None, subs_ids, new_subscriber_vals, old_subscriber_ids)

        if new_subscriber_vals:
            if ctx.get('subscriber_from_forge_ticket', False):
                vals['forge_ticket_subscriber_ids'] = new_subscriber_vals
            elif ctx.get('subscriber_from_support_ticket', False):
                vals['support_ticket_subscriber_ids'] = new_subscriber_vals
        return vals

    @api.model
    def search_subscriber_on_ticket(self, ticket_field, args):
        """
            Update domain in case of searching subscriber, default
            notification reference, notification reference
        """
        # TODO: Find solution to search with operator `or`. For now,
        #  can not handle cases that searching multi subscribers, multi default
        #  notification references, multi notification referencess.
        tms_subscriber_objs = self.env['tms.subscriber']
        ticket_ids = []
        subscriber_domain = []
        for arg in args:
            if arg[0] not in ['subscriber_id',
                              'tk_default_notif_pre_id',
                              'tk_notif_pref_id']:
                continue
            if arg[0] == 'subscriber_id':
                subscriber_domain.append(('name', arg[1], arg[2]))
            elif arg[0] in \
                    ['tk_default_notif_pre_id', 'tk_notif_pref_id'] and \
                    arg[1] == 'ilike':
                subscriber_domain.append(self.search_subscriber_ilike(arg))
            else:
                subscriber_domain.append(arg[:])
            if arg[1] != '=':
                arg[1] = '='
            arg[2] = False
        if subscriber_domain:
            subscriber_objs = tms_subscriber_objs.search(subscriber_domain)
            for subscriber_obj in subscriber_objs:
                if ticket_field == 'forge_id' and subscriber_obj.forge_id:
                    ticket_ids.append(subscriber_obj.forge_id.id)
                if ticket_field == 'support_id' and subscriber_obj.support_id:
                    ticket_ids.append(subscriber_obj.support_id.id)
            if ticket_ids:
                args.append(('id', 'in', list(set(ticket_ids))))
            else:
                if args[-1][0] != 'id':
                    args.append(('id', 'in', []))
        return args

    @api.model
    def search_subscriber_ilike(self, arg):
        notif_env = self.env['notification.preferences']
        notif_obj = notif_env.search(
            [('name', 'ilike', arg[2])], limit=1)
        if notif_obj:
            res = (arg[0], '=', notif_obj.id)
            return res
        return arg

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False,
                        submenu=False):
        res = super(TmsTicket, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if not self.env['res.users'].has_group('base.group_user') and \
                res.get('toolbar', False):
            toolbar_action = res['toolbar'].get('action', [])
            for action in toolbar_action:
                if action['display_name'] == 'Update Subcription':
                    index_act = toolbar_action.index(action)
                    del toolbar_action[index_act]
                    break
        return res

    @api.multi
    def button_subscribe(self, ticket, subscriber_field):
        """
        Button Subscribe Me
        Add current user into the ticket subscribers
        """
        notif_env = self.env['notification.preferences']
        notif_id = notif_env._get_subscribe_me_notif_id()
        vals = {
            subscriber_field: [(0, False, {'name': self._uid,
                                           'tk_notif_pref_id': notif_id})]
        }
        return ticket.write(vals)

    @api.model
    def check_supporter(self, user_id, project):
        """
        @return: True if given user is supporter of given project.
        """
        return (project.project_supporter_rel_ids and
                user_id in project.project_supporter_rel_ids.ids or False)

    @api.model
    def update_ticket_name(self, ticket_obj, model_name):
        # Using SQL to improve performance of creating ticket
        update_sql = """
            UPDATE %s
            SET name = %d
            WHERE id = %d;
        """ % (model_name, ticket_obj.id, ticket_obj.id)
        self._cr.execute(update_sql)

    @api.multi
    def check_sent_comment(self, field_name):
        self.mapped(field_name).\
            filtered(lambda x: not x.is_notification_sent).\
            write({'is_notification_sent': True})
