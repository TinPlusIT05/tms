# -*- coding: utf-8 -*-
from openerp import fields, models


class erppeek_report_config(models.Model):
    _name = "erppeek.report.config"
    _description = "ERP Peeks Report Config"

    # Columns
    tms_instance_id = fields.Many2one(
        "tms.instance", "Instance", required=True)
    database_id = fields.Many2one(
        'instance.database', 'Database', required=True)
    file_path = fields.Char(
        'File Path',
        help="In the erppeek folder, example: "
        "performance_report/generate_performance_report.py", required=True)
    command = fields.Char(
        "Command", default="python [file] [env] [options]",
        help='Input here the command to be executed with the position '
        'for environment_options and command_options marked with "[env]" '
        'and "options", example: python generate_performance_report.py '
        '[env] [options]')
    command_options_guide = fields.Char(
        "Command Options Guide", help='Input here an guide for the options '
        'to be added to the command to be executed, example "date_start '
        'date_end [team]" for insance "2016-01-01 2016-01-30 cc"')
    profile_ids = fields.Many2many(
        'res.groups', 'res_groups_implied_rel', 'hid', 'gid')
