# -*- encoding: utf-8 -*-
from openerp import fields, models


class TmsDockerRepoTags(models.Model):
    _name = "tms.docker.repo.tags"
    _description = "Tms docker repository tags"
    _order = "create_date desc"

    name = fields.Char('Name')
    create_date = fields.Datetime('Creation Date')
    size = fields.Float('Size (MB)')
    active = fields.Boolean('Active', default=True)
    tms_docker_repo_id = fields.Many2one(
        'tms.docker.repo', string='Tms docker repository')
    db_file = fields.Char('Database file')
    meta_data = fields.Serialized('Meta Data', readonly=True)
