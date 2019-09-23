import tower_cli
import logging
from openerp.addons.tms_slack.lib.slack import SlackClient
from openerp import tools
from openerp import fields, models, api


class TmsAwxJobHistory(models.Model):
    _name = 'tms.awx.job.history'
    _description = 'Tms AWX Job History'
    _order = 'create_date desc'

    name = fields.Char(string='Name')
    job_id = fields.Integer(string='Job Id')
    instance_id = fields.Many2one(
        comodel_name='tms.instance', string='Instance')
    host_id = fields.Many2one(comodel_name='tms.host', string='Host')
    docker_repo_id = fields.Many2one(
        comodel_name='tms.docker.repo', string='Docker Repo')
    internal_tools_id = fields.Many2one(
        comodel_name='tms.internal.tools', string='Internal Tools')
    status = fields.Char(string='Status')
    instance_user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='tms_awx_job_user_rel',
        column1='tms_awx_job_id',
        column2='user_id',
        string="Notify users",)
    slack_note = fields.Char(
        'Slack Note'
    )

    @api.model
    def _check_ongoing_awx_jobs(self):
        job_histories = self.search([('status', 'in', ['running', 'pending'])])
        ir_config_env = self.env['ir.config_parameter']
        slack_url = ir_config_env.get_param(
            'webhook_slack_access', default=False)
        if not slack_url:
            logging.warn(
                'Slack is not correctly configured on TMS, \
                    please set "webhook_slack_access" config parameter')
        slack_token = tools.config.get('slack_token', '')
        if not slack_token:
            logging.warn(
                'Slack is not correctly configured on TMS, '
                'please set "slack_token"in dev config')
        slack_url += slack_token

        slack = SlackClient(slack_url)
        for rec in job_histories:
            res = tower_cli.get_resource('job').list(
                query=[('id', rec.job_id)])

            for i in res.get('results', []):
                job_status = i.get('status', '')
                if rec.status != job_status:
                    # Update job's status if it's changed
                    rec.status = job_status

                list_user = ', '.join(['<@%s>' % name for name in
                                       rec.instance_user_ids.mapped('login')
                                       if name])

                if list_user and job_status in ['failed', 'successful']:
                    # Notify to relevant users on slack
                    channel = '#chatops'
                    title = rec.name
                    message = ':point_right: %(list_user)s!\n' \
                              'The task: `%(slack_note)s` has been ' \
                              '%(status)s!' % ({
                        'status': job_status,
                        'slack_note': rec.slack_note,
                        'list_user': list_user,
                    })

                    if job_status == 'failed':
                        slack.error(channel, title, message)
                    else:
                        slack.success(channel, title, message)

    @api.model
    def _delete_completed_failed_awx_jobs(self):
        logging.info('START: Delete completed/failed AWX jobs')
        to_delete = self.search([
            ('status', 'in', ['canceled', 'failed', 'successful'])])
        logging.info('Delete %s jobs', len(to_delete))
        to_delete.unlink()
        logging.info('END: Delete completed/failed AWX jobs')
        return True
