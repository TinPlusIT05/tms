# -*- encoding: UTF-8 -*-
from openerp import fields, models

REPOSITORY_OWNER_HELP = """
The person in charge of consolidating the requirements,
guarantee that we build a generic module taking into account only
generic requirements, reviewing the source code
"""


class repository(models.Model):

    _name = "repository"
    _description = "Reposity"

    name = fields.Char(string='Name', size=256)
    uri = fields.Char(
        string='URI', size=256, required=True,
        help="give the url so we can start using external sources")
    repository_owner_id = fields.Many2one(
        'res.users', string="Repository Assignee", help=REPOSITORY_OWNER_HELP)
