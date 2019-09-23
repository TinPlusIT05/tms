# -*- encoding: utf-8 -*-
from openerp import fields, models, api


class TmsDockerRepoUsers(models.Model):
    _name = "tms.docker.repo.users"
    _description = "Tms docker repository users"

    user_id = fields.Many2one('res.users', required=True, string='User')
    pull = fields.Boolean('Pull', help='Allow to pull the docker image')
    push = fields.Boolean('Push', help='Allow to push the docker image')
    tms_docker_repo_id = fields.Many2one(
        'tms.docker.repo', string='Tms docker repository')

    @api.onchange('push')
    def _onchange_push(self):
        if self.push:
            self.pull = True

    @api.model
    def create(self, vals):
        # Set pull = True if push = True
        if vals.get('push', False):
            vals.update({'pull': True})
        return super(TmsDockerRepoUsers, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('push', False):
            vals.update({'pull': True})
        res = super(TmsDockerRepoUsers, self).write(vals)
        return res

    @api.constrains('user_id')
    def check_unique_user_in_repository(self):
        msg = "Can not add duplicated user in this repository"
        for docker_user in self:
            if docker_user.search_count(
                [('user_id', '=', docker_user.user_id.id),
                 ('tms_docker_repo_id', '=',
                  docker_user.tms_docker_repo_id.id),
                 ('id', '!=', docker_user.id)]):
                raise Warning(msg)
