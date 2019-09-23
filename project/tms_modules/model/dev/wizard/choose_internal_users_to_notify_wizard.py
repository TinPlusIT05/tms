# -*- encoding: UTF-8 -*-
import tower_cli
import yaml

from openerp import models, api, fields
from openerp.tools.safe_eval import safe_eval


class ChooseInternalUserstoNotifyWizard(models.TransientModel):

    _name = 'choose.internal.users.to.notify.wizard'
    _description = 'Choose Internal Users to Notify'

    instance_user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='choose_internal_notify_user_rel',
        column1='choose_id',
        column2='user_id',
        string="Notify users")
    notify_type = fields.Selection(
        [('tms.docker.repo', 'Docker Repo'),
         ('tms.instance', 'Instance'),
         ('tms.host', 'Host'),
         ('tms.internal.tools', 'Internal Tools')],
        string='Notify Type'
    )
    host_id = fields.Many2one(
        'tms.host',
        'Host',
    )
    database_name = fields.Char(
        'Database'
    )

    @api.multi
    def regenerate_http_auth(self):
        ctx = dict(self._context) or {}
        if ctx.get('extra_vars_name'):
            uid = self._uid
            active_id = ctx.get('active_id')
            extra_vars_name = ctx.get('extra_vars_name')
            trobz_awx_job_param = self.env['ir.config_parameter'].get_param(
                'trobz_awx_job_param', '{}'
            )
            for rec in self:
                model = rec.notify_type
                record = self.env[model].browse(active_id)
                slack_note = ''
                limit = ''
                if model == 'tms.instance':
                    job_template_key = 'httpauth_instance'
                    extra_vars = [
                        yaml.safe_dump({'INSTANCE': extra_vars_name}),
                    ]
                    slack_note = '%s(%s)' % (job_template_key, extra_vars_name)
                elif model == 'tms.host':
                    job_template_key = 'sshauth_host'
                    extra_vars = [
                        yaml.safe_dump({'HOST': extra_vars_name}),
                    ]
                    slack_note = '%s(%s)' % (job_template_key, extra_vars_name)
                elif model == 'tms.docker.repo':
                    job_template_key = 'dockerize_db_instance'
                    instance = record.instance_id
                    instance_name = instance and instance.name or ''
                    db_name = rec.database_name or ''
                    extra_vars = [
                        yaml.safe_dump({
                            'INSTANCE': instance_name,
                            'DATABASE': db_name}),
                    ]
                    slack_note = '%s(%s, %s)' % (
                        job_template_key, instance_name, db_name)
                    limit = rec.host_id.name or ''
                elif model == 'tms.internal.tools':
                    job_template_key = 'deploy_%s' % extra_vars_name
                    limit = ''
                    if record.host_group:
                        limit = record.host_group
                    else:
                        limit = ','.join(record.host_ids.mapped('name'))
                    slack_note = '%s (%s)' % (
                        job_template_key, limit)
                    extra_vars = []

                trobz_awx_job_param = safe_eval(trobz_awx_job_param)
                job_template = trobz_awx_job_param.get(
                    job_template_key, {}).get('id', False)
                vals = {}
                # execute awx job `httpauth_instance`
                try:
                    res = tower_cli.get_resource('job').launch(
                        job_template=job_template, extra_vars=extra_vars,
                        limit=limit)

                except Exception, e:
                    raise Warning(e.message)

                if res:
                    instance_user_ids = rec.instance_user_ids.ids + [uid]
                    vals.update({
                        'name': res.get('name'),
                        'job_id': res.get('id'),
                        'status': res.get('status'),
                        'slack_note': slack_note,
                        'instance_user_ids': [
                            (6, 0, instance_user_ids)]
                    })
                    if model == 'tms.instance':
                        vals.update({
                            'instance_id': record.id,
                            'host_id': record.host_id.id
                        })
                    elif model == 'tms.host':
                        record = record.with_context(bypass_security=True)
                        vals.update({
                            'host_id': record.id,
                        })
                    elif model == 'tms.docker.repo':
                        vals.update({
                            'instance_id': instance.id,
                            'host_id': rec.host_id.id
                        })
                    record.awx_job_history_ids = [
                        (0, 0, vals)]
