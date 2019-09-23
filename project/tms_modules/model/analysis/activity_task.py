# -*- coding: utf-8 -*-

from openerp import models, fields


class ActivityTask(models.Model):
    _name = 'activity.task'
    _order = 'deadline desc'
    name = fields.Char(
        string='Name')
    description = fields.Text(
        string='Description')
    deadline = fields.Date(
        string='Deadline')
    active = fields.Boolean(
        string='Active',
        default=True)
    activity_id = fields.Many2one(
        string='Activity',
        comodel_name='tms.activity')
