# -*- encoding: utf-8 -*-
from openerp import fields, models, api
from datetime import datetime
from requests.auth import HTTPBasicAuth
from openerp import tools

import urllib2
import requests
import json
import logging


class TmsDockerRepo(models.Model):
    _name = "tms.docker.repo"
    _description = "Docker Repository"

    repo_type = fields.Selection([
        ('project_db', 'Project DB'),
        ('project_odoo', 'Project Odoo'),
        ('other', 'Other')
    ], default='project_db', string='Repository Type')
    project_id = fields.Many2one('tms.project', 'Project')
    instance_id = fields.Many2one('tms.instance', 'Instance')
    host_id = fields.Many2one('tms.host', 'Host')
    name = fields.Char('Repository', required=True)
    db_backup_location = fields.Char('DB Backup Location')
    active = fields.Boolean('Active', default=True)
    tms_docker_repo_user_ids = fields.One2many(
        'tms.docker.repo.users', 'tms_docker_repo_id',
        string='Docker Users')
    tms_docker_repo_tag_ids = fields.One2many(
        'tms.docker.repo.tags', 'tms_docker_repo_id',
        string='Docker Tags')
    pg_version = fields.Char('PG version', default='9.6')
    everyone_can_pull = fields.Boolean('Everyone can pull')
    database_id = fields.Many2one(
        'instance.database', string='Database')
    database_name = fields.Char(
        related='database_id.name',
        readonly=True
    )
    note = fields.Text(string='Internal Notes')
    latest_tag_id = fields.Many2one(
        'tms.docker.repo.tags',
        string='Latest Version',
        compute='_compute_latest_active_tag'
    )
    track_update_status = fields.Boolean('Track Update Status', default=False)
    update_alert = fields.Selection([
        ('nothing', 'Nothing'),
        ('uptodate', 'Up to date'),
        ('warning', 'Warning'),
        ('danger', 'Danger')],
        string='Update Alert', compute='_compute_update_alert')
    auto_update_tag = fields.Boolean('Auto Update Tags', default=False)
    awx_job_history_ids = fields.One2many(
        comodel_name='tms.awx.job.history',
        inverse_name='docker_repo_id', string='AWX Job History')

    @api.onchange('project_id', 'repo_type', 'database_id')
    def _onchange_project_id(self):
        if self.project_id and self.repo_type == 'project_db':
            project_name = self.project_id.name
            database_name = self.database_id.name or ''
            docker_repo_link = self.env['ir.config_parameter'].get_param(
                'default_docker_repository', '')
            self.name = docker_repo_link % (project_name, database_name)

    @api.onchange('database_id')
    def _onchange_database_id(self):
        if self.database_id:
            self.host_id = self.instance_id.host_id or False
            instance_name = self.instance_id.name or ''
            database_name = self.database_id.name or ''
            db_backup_location_link = self.env[
                'ir.config_parameter'].get_param(
                'default_db_backup_location', '')
            self.db_backup_location = db_backup_location_link % (
                instance_name, database_name)

    @api.onchange('instance_id')
    def _onchange_instance_id(self):
        if self.instance_id:
            database_instance_ids = self.instance_id.instance_database_ids or\
                False
            if database_instance_ids:
                self.database_id = database_instance_ids[0].id

    @api.constrains('name')
    def check_unique_name(self):
        """
        Check docker repository must be unique
        """
        msg = "The docker repository must be unique"
        for docker_repo in self:
            if docker_repo.search_count(
                [('name', '=', docker_repo.name),
                 ('id', '!=', docker_repo.id)]):
                raise Warning(msg)

    @api.multi
    def show_full_tags(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tms.docker.repo',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'context': {'active_test': False, }
        }

    @api.multi
    @api.depends('tms_docker_repo_tag_ids')
    def _compute_latest_active_tag(self):
        for record in self:
            repo_tag_env = record.env['tms.docker.repo.tags']
            record.latest_tag_id = repo_tag_env or repo_tag_env\
                .search([('active', '=', True),
                         ('tms_docker_repo_id', '=', record.id)],
                        order='create_date DESC',
                        limit=1).id

    @api.multi
    def _compute_update_alert(self):
        for record in self:
            now = datetime.now()
            latest_tag = record.env['tms.docker.repo.tags']\
                .search([('active', '=', True),
                         ('tms_docker_repo_id', '=', record.id)],
                        order='create_date DESC',
                        limit=1)
            if latest_tag and record.track_update_status:
                latest_date = datetime.strptime(
                    latest_tag.create_date, '%Y-%m-%d %H:%M:%S')
                delta_date = (now - latest_date).total_seconds() / \
                    (24.0 * 3600)
                if delta_date <= 1:
                    record.update_alert = 'uptodate'
                elif delta_date > 1 and delta_date < 2:
                    record.update_alert = 'warning'
                elif delta_date >= 2:
                    record.update_alert = 'danger'
            else:
                record.update_alert = 'nothing'

    def get_www_authenticate_header(self, api_url):
        try:
            req = urllib2.Request(api_url)
            request = urllib2.urlopen(req)
            response = request.read()
        except urllib2.HTTPError as error:
            response = error.info()['Www-Authenticate']
        return response

    def find_between(self, s, first, last):
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""

    def get_token(self, user, password, service, scope, realm):
        data = {"scope": scope, "service": service, "account": user}
        r = requests.post(realm, auth=HTTPBasicAuth(user, password), data=data)
        token = self.find_between(str(r.content), 'token":"', '"')
        return token

    def get_result(self, api_url, token):
        r = requests.get(api_url, headers={'Authorization': 'Bearer ' + token})
        return r.content

    @api.model
    def check_and_create_tag_docker_repository(self):
        docker_repos = self.env['tms.docker.repo'].search(
            [('auto_update_tag', '=', True)])
        if not docker_repos:
            return True
        logging.info(" Run Check and create tag for docker repository")
        docker_tag_env = self.env['tms.docker.repo.tags']
        param_obj = self.env['ir.config_parameter']

        # Docker Hub credentials
        docker_hub_api_url = param_obj.get_param('docker_hub_api_url', '')
        docker_hub_root_url = param_obj.get_param('docker_hub_root_url', '')
        docker_hub_user = tools.config.get('docker_hub_user', '').strip()
        if not docker_hub_user:
            logging.info(
                'Docker hub user is not correctly configured on TMS, '
                'please set "docker_hub_user" in configuration file')
        docker_hub_pass = tools.config.get('docker_hub_pass', '').strip()
        if not docker_hub_pass:
            logging.info(
                'Docker hub pass is not correctly configured on TMS, '
                'please set "docker_hub_pass" in configuration file')
        for docker_repo in docker_repos:
            docker_id = docker_repo.id
            # https://docker-hub.trobz.com/v2/production_data/tms80/database/tags/list
            request_url = \
                "%s/%s/tags/list" % (docker_hub_api_url,
                                     docker_repo.name.replace(
                                         docker_hub_root_url, ""))
            # get the Www-Authenticate header
            params = docker_repo.get_www_authenticate_header(request_url)
            # parse the params required for the token
            if not params:
                logging.info('404 : Not Found...')
                continue
            service = docker_repo.find_between(params, 'service="', '"')
            scope = docker_repo.find_between(params, 'scope="', '"')
            realm = docker_repo.find_between(params, 'realm="', '"')

            # retrieve token
            token = docker_repo.get_token(docker_hub_user,
                                          docker_hub_pass,
                                          service, scope, realm)
            res = docker_repo.get_result(request_url, token)
            res = json.loads(res)
            repo_tags = res.get('tags')
            if not repo_tags:
                logging.info('Nothing to do, no docker image found')
                continue
            for tag in repo_tags:
                # search if exists
                found_tag = \
                    docker_tag_env.search(
                        [('name', '=', tag),
                         ('tms_docker_repo_id', '=', docker_id)])
                if found_tag:
                    logging.info("Tag: %s exists" % tag)
                    continue
                tag_data = {'tms_docker_repo_id': docker_id, 'name': tag}
                docker_tag_env.create(tag_data)
                logging.info("Created tag: %s" % tag)
