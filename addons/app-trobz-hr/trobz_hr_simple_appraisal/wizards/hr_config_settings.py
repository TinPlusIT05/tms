# -*- coding: utf-8 -*-
from openerp import models, fields, api


class hr_config_settings(models.TransientModel):
    _inherit = 'hr.config.settings'

    # Columns
    default_appraisal_mailing_list = fields.Char(
        string="Appraisal Mailing List")

    @api.model
    def get_default_appraisal_mailing_list(self, fields):
        param_obj = self.env['ir.config_parameter']
        default_appraisal_mailing_list = param_obj.get_param(
            'default_appraisal_mailing_list', 'False'
        )
        return {
            'default_appraisal_mailing_list':default_appraisal_mailing_list
        }

    @api.one
    def set_default_appraisal_mailing_list(self):
        param_obj = self.env['ir.config_parameter']
        param_obj.set_param(
            'default_appraisal_mailing_list',
            self.default_appraisal_mailing_list or 'False'
        )
