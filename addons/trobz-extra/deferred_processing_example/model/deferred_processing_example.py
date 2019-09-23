# -*- coding: utf-8 -*-
import logging
from openerp import api, models, fields

_logger = logging.getLogger(__name__)


class DeferredProcessingExample(models.Model):
    _name = 'deferred.processing.example'

    name = fields.Char('Name', required=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirm'),
                              ('done', 'Done')], 'State')

    @api.multi
    def test_deferred_function(self):
        deferred_env = self.env['deferred_processing.task']
        function = 'normal_deferred_function'
        defer_object = 'deferred.processing.example'
        return deferred_env.create_deferred_function(function, defer_object,
                                                     self.ids)

    @api.multi
    def test_deferred_workflow(self):
        deferred_task_env = self.env['deferred_processing.task']
        deferred_args = ('deferred.processing.example', self.ids[0], 'confirm')
        return deferred_task_env.\
            create_deferred_workflow('trg_validate', self.ids,
                                     deferred_args=deferred_args)

    @api.multi
    def test_deferred_function_with_args(self):
        deferred_env = self.env['deferred_processing.task']
        function = 'normal_deferred_function_with_args'
        defer_object = 'deferred.processing.example'
        send_email = True
        deferred_args = ('a', 'b')
        deferred_kwargs = {'c': 'c', 'd': 'd'}
        return deferred_env.create_deferred_function(function, defer_object,
                                                     self.ids, send_email,
                                                     deferred_args,
                                                     deferred_kwargs)

    @api.multi
    def test_deferred_report(self):
        partner_recs = self.env['res.partner'].search([])
        deferred_task_env = self.env['deferred_processing.task']
        return deferred_task_env.\
            create_deferred_report(partner_recs.ids,
                                   'base.res_partner_address_report')

    # can use api.multi / api.model Here
    @api.v8
    def normal_deferred_function(self):
        # Test case: get on param
        param = self.env['ir.config_parameter']
        param.get_param('test')
        # Test case: try to search some users
        users = self.env['res.users'].search([], limit=10)
        for user in users:
            _logger.info("User login: %s" % user.login)

        # do some tasks
        i = 0
        while i < 20000:
            i += 1
            _logger.info("Current Defer Task, items: %s" % i)
        return True

    @api.v8
    def do_action_confirm(self):
        self.normal_deferred_function()
        self.write({'state': 'confirm'})

    @api.v8
    def normal_deferred_function_with_args(self, a, b, c='c', d='d'):
        i = 0
        while i < 20000:
            i += 1
            _logger.info("Current Defer Task, items: %s" % i)
        return True
