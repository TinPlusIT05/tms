# -*- encoding: utf-8 -*-
import logging

from openerp import fields, api, models
from datetime import datetime
from openerp import tools
from openerp.addons.tms_slack.lib.slack import SlackClient  # @UnresolvedImport
from openerp.exceptions import Warning

from .tms_instance import server_type_array


_logger = logging.getLogger(__name__)


'''
    More logs than usual for this class because often called through API.
'''


class tms_delivery(models.Model):

    _name = "tms.delivery"
    _description = "Delivery"
    _order = "name desc"

    @api.onchange('instance_id')
    def on_change_instance_id(self):
        if self.instance_id:
            self.project_id = self.instance_id and \
                self.instance_id.project_id and self.instance_id.project_id
            self.milestone_id = self.instance_id and \
                self.instance_id.milestone_id and \
                self.instance_id.milestone_id.id

    # Columns
    create_uid = fields.Many2one('res.users', 'Creator')
    name = fields.Datetime('Delivery Date', required=True)
    project_id = fields.Many2one(
        comodel_name='tms.project',
        string='Project', readonly=True,
        store=True)
    milestone_id = fields.Many2one(
        'tms.milestone', 'Milestone',
        domain="[('project_id','=',project_id)]")
    instance_id = fields.Many2one(
        'tms.instance', 'Instance', required=True)
    server_type = fields.Selection(
        server_type_array, 'Server', related='instance_id.server_type',
        readonly=True, store=True)
    state = fields.Selection(
        [('in_progress', 'In Progress'),
         ('exception', 'Exception'),
         ('done', 'Done')],
        'Status', default='in_progress', required=True)

    note = fields.Text('Notes')
    forge_ticket_ids = fields.Many2many(
        'tms.forge.ticket', 'tms_delivery_forge_ticket_rel',
        'delivery_id', 'ticket_id', 'Related Tickets')

    # TODO: JC: re-check this function after migration of tms.milestone has
    # been taken into account.
    @api.model
    def _set_milestone_status_deployed(self, instance):
        """
        Set current milestone's state to deployment
            and next milestone's state is development
        If server_type of instance is production,
            set current milestone's state to production
        """
        milestone_env = self.env['tms.milestone']
        if instance.milestone_id and \
                instance.milestone_id.state != 'production':
            if instance.server_type == 'production':
                milestone_vals = {'state': 'production'}
            else:
                milestone_vals = {'state': 'deployment'}

            instance.milestone_id.write(milestone_vals)

        next_mst_id = instance.milestone_id.get_next_milestone(
            instance.project_id.id)
        # TODO: This function should not take any
        # arguments:instance.milestone_id.get_next_milestone()

        if next_mst_id:
            next_mst_obj = milestone_env.browse(next_mst_id)
            if next_mst_obj.state == 'planned':
                next_mst_obj.write({'state': 'development'})
        else:
            # TODO: Is this a warning or an error? I think it is an error
            # because it is blocking.
            raise Warning(
                'Warning',
                'You can not deliver this milestone; '
                'you need to create a next milestone first.')

        return True

    @api.model
    def _set_milestone_status_done(self, instance):
        """
        When delivering production,
            set previous milestone's state to done
        """
        milestone_env = self.env['tms.milestone']
        if instance.server_type == 'production':
            # TODO: This function should not take any
            # arguments and could do the job directly:
            # instance.milestone_id.set_previous_milestone_as_done()
            pre_mst_id = instance.milestone_id.get_previous_milestone(
                instance.project_id.id)

            if pre_mst_id:
                pre_mst_obj = milestone_env.browse(pre_mst_id)
                pre_mst_obj.write({'state': 'done'})

        return True

    @api.model
    def _get_delivery_list(self):
        return self.env['tms.forge.ticket'].search(
            [('milestone_id', '=', self.milestone_id.id),
             ('state', 'in', ['ready_to_deploy', 'in_qa', 'closed']),
             ('delivery_status', '!=', 'no_development')
             ]
        )

    @api.model
    def _update_related_forge_tickets(self):
        logging.info('Entered update_related_forge_tickets...')
        context = self._context and self._context.copy() or {}
        context.update({'updating_forge_tickets_from_delivery': True})

        # get the list of forge tickets delivered
        forge_tickets = self._get_delivery_list()
        if forge_tickets:
            self.with_context(context).write(
                {'forge_ticket_ids': [(6, False, forge_tickets.ids)]})

        logging.info('Leaving update_related_forge_tickets...')
        return True

    @api.multi
    def _update_delivery_status_forge_ticket(self):
        """
        Update Delivery Status of related forge tickets
        """
        logging.info('Prepare to update forge tickets\' delivery status...')

        context = self._context and self._context.copy() or {}

        if context.get('update_delivery_status_forge_ticket', False):
            return True

        context['update_delivery_status_forge_ticket'] = True
        forge_env = self.env['tms.forge.ticket']

        for delivery in self:
            if not delivery.forge_ticket_ids:
                continue

            forge_objs = []
            delivery_status = 'in_development'

            if delivery.server_type == 'integration':
                delivery_status = 'in_integration'
                current_forge_objs = self._get_delivery_list()
                if current_forge_objs:
                    # For tickets which are delivered to staging or production
                    # but are not delivered yet to integration,
                    # when they are delivered to integration,
                    # do NOT change the delivery status back to
                    # “In Integration”.
                    forge_objs = forge_env.search([
                        ('id', 'in', current_forge_objs.ids),
                        ('delivery_status', 'in',
                         ['no_development', 'in_development'])
                    ])

            elif delivery.server_type == 'staging':
                delivery_status = 'in_staging'
                current_forge_objs = self._get_delivery_list()
                if current_forge_objs:
                    # For tickets which are delivered to production but are not
                    # delivered yet to staging, when they are delivered to
                    # staging, do NOT change the delivery status back to
                    # “In Staging”.
                    forge_objs = forge_env.search([
                        ('id', 'in', current_forge_objs.ids),
                        ('delivery_status', 'in',
                         ['no_development', 'in_development',
                          'in_integration', 'ready_for_staging'])
                    ])

            elif delivery.server_type == 'production':
                delivery_status = 'in_production'
                forge_objs = self._get_delivery_list()

            if forge_objs:
                forge_objs.with_context(context).write(
                    {'delivery_status': delivery_status}
                )

        logging.info('Forge tickets\' delivery status updated...')
        return True

    @api.multi
    def write(self, vals):
        context = self._context and self._context.copy() or {}
        if context.get('update_delivery_status_forge_ticket', False):
            return super(tms_delivery, self).write(vals)
        tms_instance_env = self.env['tms.instance']
        for old_delivery in self:
            logging.info('Processing old delivery...')
            if 'instance_id' in vals:
                instance_obj = tms_instance_env.browse(vals['instance_id'])
                if not instance_obj.milestone_id:
                    raise Warning(
                        'Warning',
                        'This instance does not have milestone; '
                        'please add milestone to this instance.')
                vals['milestone_id'] = instance_obj.milestone_id and \
                    instance_obj.milestone_id.id or False
                if old_delivery.project_id and instance_obj.project_id\
                        and old_delivery.project_id.id !=\
                        instance_obj.project_id.id:
                    vals['project_id'] = instance_obj.project_id.id

            logging.info('Writing new information to old delivery: %s' % vals)
            result = super(tms_delivery, old_delivery).write(vals)
            if vals.get('state', False) == 'done':
                old_delivery._update_related_forge_tickets()
                old_delivery._update_delivery_status_forge_ticket()
                old_delivery.slack_notification()
                # Set current milestone's state to production
                #     and next milestone's state is development
                old_delivery._set_milestone_status_deployed(
                    old_delivery.instance_id)
                if old_delivery.instance_id.server_type == 'production':
                    # When delivering production,
                    #    set previous milestone's state to done
                    old_delivery._set_milestone_status_done(
                        old_delivery.instance_id)
                    # Update for Release dates on Milestone
                    self._add_release_date_on_milestone(old_delivery)
            elif vals.get('state', False) == 'exception':
                old_delivery.slack_notification(success=False)

        logging.info('Leaving write of tms_delivery...')

        return result

    @api.model
    def create(self, vals):
        instance = self.env['tms.instance'].browse(
            vals['instance_id'])

        vals.update({
            'milestone_id': instance.milestone_id.id,
            'project_id': instance.project_id and
            instance.project_id.id or False
        })

        logging.info('Creating a new delivery with data: %s' % vals)
        result = super(tms_delivery, self).create(vals)
        if vals.get('state', False) == 'done':
            # Log because this function is often call through API
            logging.info('Updating related forge tickets of delivery: %s'
                         % result)
            result._update_related_forge_tickets()
            result._update_delivery_status_forge_ticket()

            # Set current milestone's state to deployment
            # and next milestone's state is development
            self._set_milestone_status_deployed(instance)
            if instance.server_type == 'production':
                # When delivering production,
                #    set previous milestone's state to done
                self._set_milestone_status_done(instance)
                # Update for Release dates on Milestone
                self._add_release_date_on_milestone(result)
        if vals.get('state', False) != 'in_progress':
            success = vals.get('state', False) != 'exception'
            result.slack_notification(success=success)

        logging.info('Leaving create of tms_delivery...')
        return result

    @api.model
    def _add_release_date_on_milestone(self, result):
        release_date = \
            datetime.strptime(result.name, "%Y-%m-%d %H:%M:%S").date()
        if not result.milestone_id.release_dates:
            result.milestone_id.release_dates = str(release_date)
        else:
            result.milestone_id.release_dates += ', ' + str(release_date)

    @api.multi
    def slack_notification(self, success=True):
        """
        Post a deployment notification message on Slack service.
        """
        is_production_instance = tools.config.get(
            'is_production_instance', False)

        if not is_production_instance:
            logging.warning('Slack notification skipped because this is not a '
                            'production instance')
            return
        slack_url = self.env['ir.config_parameter'].get_param(
            'webhook_slack_access', default=False)
        if not slack_url:
            logging.warn(
                'Slack is not correctly configured on TMS, '
                'please set "webhook_slack_access" config parameter')
        slack_token = tools.config.get('slack_token', '')
        if not slack_token:
            logging.warn(
                'Slack is not correctly configured on TMS, '
                'please set "slack_token"in dev config')
        slack_url += slack_token

        slack = SlackClient(slack_url)

        for delivery in self:

            project_obj = delivery.instance_id and\
                delivery.instance_id.project_id or False
            milestone_obj = delivery.milestone_id
            instance_obj = delivery.instance_id

            channel = '#%s' % project_obj.name or ''

            if success:
                title = 'Successful deployment on instance <%s|%s>' % (
                    instance_obj.url or '', instance_obj.name or '')
                message = '%s milestone on %s project has been ' % \
                    (milestone_obj.name or '',
                     project_obj.name or '') +\
                    'successfully deployed on instance %s.' % \
                    (instance_obj.name or '')
                slack.success(channel, title, message)
            else:
                title = 'Failed to deployment on instance <%s|%s>' % (
                    instance_obj.url or '', instance_obj.name or '')
                message = '%s milestone on %s project has failed' \
                          ' on instance %s.' % (milestone_obj.name or '',
                                                project_obj.name or '',
                                                instance_obj.name or '')
                slack.error(channel, title, message)
