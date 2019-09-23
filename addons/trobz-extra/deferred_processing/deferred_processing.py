# -*- encoding: utf-8 -*-
import threading
import time
import logging
import base64
from datetime import datetime
import openerp
from openerp import api, models, fields
from openerp.tools.translate import _
from openerp import workflow
from openerp.sql_db import db_connect
from openerp.modules.registry import RegistryManager
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from openerp.exceptions import Warning


class Deferred(threading.Thread):

    def __init__(self, dbname, uid, process_id):
        # threading.Thread.__init__(self)
        super(Deferred, self).__init__()
        self._process_id = process_id
        self._ids = []
        self._total = 0.0
        self._processed_ids = []
        self._processed = 0.0
        self._progress = 0.0
        self._intercept_value = 1.0
        self._state = 'start'
        self._start_time = None
        self._time_elapsed = 0.0
        self._time_left = 0.0
        self._speed = 0.0

        # Add attribute self.workflow
        self.workflow = False
        # Add attribute self.report
        self.report = False
        # Add a flag to control the email notification
        self.send_email = True
        self.method = None
        self.args = []
        self.kwargs = {}

        self.result = None
        self._result_parser = "result[0]"
        self.dbname = dbname
        self.uid = uid

    def run(self):
        # Add logging messages
        logging.info('Enter new process...')
        cr = db_connect(self.dbname).cursor()

        with openerp.api.Environment.manage():
            RegistryManager.check_registry_signaling(self.dbname)
            # create an Environment
            env = openerp.api.Environment(cr, self.uid, {})
            deferred_obj = env['deferred_processing.task'].\
                browse(self._process_id)
            self._start_time = time.time()

            deferred_obj.write({'state': 'process'})
            logging.info('Executing deferred task %s' % self._process_id)

            cr.commit()
            self._state = 'process'
            if 'context' in self.kwargs:
                self.kwargs['context'].update({'deferred_process': self})

            # Prepare the template to send notification
            if self.send_email:
                template_env = env['email.template']
                mail_template = template_env.\
                    search([('name', '=', 'Deferred Processing')], limit=1)
                m_template_id = mail_template and mail_template.id or False
                if not m_template_id:
                    self.send_email = False
            try:
                # Add a new way to Call workflow function
                if self.workflow:
                    # Call workflow function
                    self.result = self.method(self.uid, *(self.args + (cr,)))
                elif self.report:
                    # call report function
                    # Because the core report module still use old API
                    # so, need use cr, uid here
                    self.result = self.method(cr, self.uid, *self.args)
                else:
                    # Call method New API
                    instance = self.method.__self__
                    # Because old cursor was closed, replace new env here
                    instance.env = env
                    self.result = self.method(*self.args, **self.kwargs)
            except Exception as exc:
                # Handling all exceptions.
                # Record the exception into field
                # note.
                cr.rollback()
                # update state (interrupt) and note
                logging.error(exc)
                deferred_obj.write({'state': 'interrupt',
                                    'note': exc})
                # Control the notification
                if self.send_email:
                    logging.warning('Sending email notification...')
                    mail_template.send_mail(self._process_id, force_send=True)
                cr.commit()
                cr.close()
                return

            self.refresh_status()
            self.get_speed()
            self._state = 'done'
            self._processed = self._total
            self._progress = 100.0
            to_write = {'state': 'done'}
            # type(self.result) != bool
            # Because self._result_parser = "result[0]",
            # Error if self.result is a
            # dictionary/number
            if self.result and type(self.result) in (list, tuple):
                if self._result_parser:
                    self.result = eval(
                        self._result_parser, {}, {'result': self.result})
                    to_write['result'] = base64.encodestring(self.result)

            # Face the problem with cr.rollback()
            # Nothing change after run deferred task
            cr.commit()
            deferred_obj.write(to_write)
            # Control the notification
            if self.send_email:
                logging.info('Sending email notification...')
                mail_template.send_mail(self._process_id, force_send=True)
            cr.commit()
            logging.info('Closing transaction...')
            cr.close()
            return
        return

    def progress_update(self, rate=1):
        if self._processed < self._total:
            self._processed += 1
        if rate > 1:
            rate = 1
        self._progress += rate * self._intercept_value
        return self._progress

    def refresh_status(self):
        if self._start_time and self._state not in ('done', 'interrupt'):
            self._time_elapsed = (time.time() - self._start_time) / 60.0
            if self._processed:
                self._time_left = (
                    self._time_elapsed / self._processed) *\
                    (self._total - self._processed)
        self._speed = self._processed and self._time_elapsed / \
            self._processed or False
        return {
            'time_elapsed': self._time_elapsed,
            'time_left': self._time_left,
            'progress': self._progress,
            'processed': self._processed,
            'speed': self._speed
        }

    def get_speed(self):
        self._speed = self._processed and self._time_elapsed / \
            self._processed or False
        return self._speed

    def set_total_items(self, ids):
        self._ids = ids
        self._total = len(ids)
        self._intercept_value = 100.0 / self._total

    def get_processed(self):
        return self._processed

    def get_total(self):
        return self._total

    def get_state(self):
        return self._state


class deferred_processing_task(models.Model):
    _name = 'deferred_processing.task'
    _processed = {}

    @api.v8
    def new_process(self, process_id):
        deferred = Deferred(self.env.cr.dbname, self.env.uid, process_id)
        self._processed[process_id] = deferred
        return deferred

    @api.v8
    def start_process_object(self, process_id, model, method, ids,
                             args, kwargs={}):
        """
        """
        # TODO: To use use self.env here, you must fix the way
        # to run self.method in Deffered object
        obj = self.env[model]
        deferred = self._processed[process_id]
        deferred.set_total_items(ids)
        deferred.method = getattr(obj, method)
        deferred.args = args
        deferred.kwargs = kwargs
        current_task = self.browse(process_id)
        # if current_task and current_task.send_email:
        deferred.send_email = current_task and current_task.send_email \
            or False
        # To write process_id into DB before run() thread
        self.env.cr.commit()
        deferred.start()
        return True

    @api.v8
    def start_process_report(self, process_id, ids, report_xml_id):
        context = self._context.copy()
        deferred = self._processed[process_id]
        deferred.set_total_items(ids)
        context['active_ids'] = ids
#         report = self.env['ir.actions.report.xml'].browse(report_id)
        report = self.env.ref(report_xml_id)
        report_name = report.report_name
        if context.get('datas'):
            data = context['datas']
        else:
            data = {'model':  report.model, 'id': context['active_ids'][0],
                    'name': report_name,
                    'report_type': report.report_type}
        deferred.report = True
        deferred.method = openerp.report.render_report
        deferred.args = (ids, report_name, data, context)

        # Control the email notification
        current_task = self.browse(process_id)
        # if current_task and current_task.send_email:
        deferred.send_email = current_task and current_task.send_email or False
        # To write process_id into DB before run() thread
        self.env.cr.commit()
        deferred.start()
        return True

    @api.v8
    def start_process_workflow(self, process_id, method, ids, args,
                               kwargs={}):
        """
        # Trobz: call functions of workflow_service: trg_create, trg_delete,
        trg_write..
        @param process_id: ID of deferred_processing_task record
        @param method: trg_create, trg_delete, trg_write..
        @param args: the arguments of method that wants to call. For Ex:
            trg_create(self, uid, res_type, res_id, cr)
            self.args = (res_type, res_id)
        """
        deferred = self._processed[process_id]
        deferred.set_total_items(ids)
        deferred.method = getattr(workflow, method)
        deferred.workflow = True
        deferred.args = args
        deferred.kwargs = kwargs
        # Control the email notification
        current_task = self.browse(process_id)
        # To write process_id into DB before run() thread
        deferred.send_email = current_task and current_task.send_email or False
        self.env.cr.commit()
        deferred.start()
        return True

    @api.v8
    def show_process(self, process_id):
        """
        @return: act_window that link to the running deferred process
        """
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']

        ModelData = mod_obj.search(
            [('name', '=',
              'action_deferred_processing_task_deferred_processing')])
        res_id = ModelData.res_id
        ActWindow = act_obj.browse(res_id)
        result = {
            'name': ActWindow.name,
            'res_id': process_id,
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': ActWindow.res_model,
            'context': ActWindow.context,
            'type': 'ir.actions.act_window'
        }

        return result

    @api.multi
    def refresh_status(self):
        """
        Update the list of these fields: progress, time_left,
        time_elapsed, speed, processed
        """
        to_check_task = self.search([('id', 'in', self.ids),
                                    ('state', 'not in',
                                    ('done', 'interrupt'))])
        for task in to_check_task:
            # progress, time_left, time_elapsed, speed, processed
            deferred = self._processed.get(task.id)
            if not deferred:
                continue
            res = deferred.refresh_status()
            task.write(res)
        return True

    @api.model
    def create(self, vals):
        if not vals.get('user_id'):
            vals['user_id'] = self.env.uid
        if vals.get('ref', False):
            model_ref, model_ref_id = vals['ref'].split(',')
            model_datas = self.env[model_ref].read(model_ref_id, ['name'])
            if model_datas.get('name', False):
                vals.update({'ref_char': model_datas['name']})
        return super(deferred_processing_task, self).create(vals)

    @api.multi
    def write(self, vals):
        """
        Update deferred tasks' information when it is done.
        """
        if vals.get('state', False) in ('done', 'interrupt'):
            self.refresh_status()
        return super(deferred_processing_task, self).write(vals)

    @api.model
    def _get_default_recipient_email(self):
        email = self.env.user.email or ''
        return email

    @api.v8
    def get_url(self):
        web_base_url = self.env['ir.config_parameter'].get_param(
            'web.base.url', False)
        url = web_base_url + \
            '/#id=%s&view_type=form&model=deferred_processing.task' % \
            self.ids[0]
        return url

    _order = 'id desc'

    ref = fields.Reference(
        lambda self: [
            (m.model, m.name)
            for m in self.env['ir.model'].search([])
        ],
        string='Reference')
    ref_char = fields.Char('Reference', size=128)
    state = fields.Selection((('start', 'To Start'),
                             ('process', 'In Progress'),
                             ('interrupt', 'Interrupted'),
                             ('done', 'Done')), 'State', size=64,
                             required=False, readonly=False,
                             default='start')
    # Convert the following fields to normal fields for better
    # performance and avoid concurrent access issue.
    progress = fields.Float('Progress')
    time_left = fields.Float('Time Left', help='Estimated time left.')
    time_elapsed = fields.Float('Time Elapsed')
    speed = fields.Float('Sec. per Entry',
                         help='Average number of seconds per entry.')
    total = fields.Integer('Total Entries',
                           help='Number of entries to be processed.')
    processed = fields.Integer('Processed Entries',
                               help='Number of processed entries so far.')
    result = fields.Binary('Result Data', required=False,
                           readonly=False, help='')
    user_id = fields.Many2one('res.users', 'User',
                              default=lambda self: self._uid)

    name = fields.Char('Name', required=True, readonly=True,
                       translate=False, help='')
    filename = fields.Char('File Name', required=True,
                           readonly=True, translate=False, help='')
    # Add field note to record the exception in case it occurs
    # during the execution.
    note = fields.Text('Note')
    send_email = fields.Boolean(
        'Send Email?', help='Send an email when this task finishes.',
        default=True)
    recipient = fields.Char('Recipient(s)', size=64,
                            default=_get_default_recipient_email)
    create_date = fields.Datetime('Creation Date', readonly=1)
    write_date = fields.Datetime('Last Modification Date', readonly=1)

    @api.multi
    def done_manual(self):
        InProgressTasks = self.search([('id', 'in', self.ids),
                                       ('state', '!=', 'done'),
                                       ('progress', '=', 100)])
        if InProgressTasks and InProgressTasks.ids != self.ids:
            raise Warning(
                _('Invalid Action'),
                _('You cannot done the deferred records ' +
                  'if their progress are less than 100%.'))
        if InProgressTasks:
            InProgressTasks.write({'state': 'done'})

        return True

    @api.v8
    def create_deferred_function(self, function, defer_object, total_ids,
                                 send_email=False, deferred_args=[],
                                 deferred_kwargs={}):
        """
        The wrapper function which help to create defer task to run
        a function in background
        @param function: function to run in background
        @param defer_object: Object which contain function to run
        @param total_ids: total ids record need to run function
        """
        deferred_obj = self.env['deferred_processing.task']
        now_datetime = fields.Datetime.context_timestamp(self, datetime.now())
        now_datetime = now_datetime.strftime(DATETIME_FORMAT)
        deferred_vals = {
            'name': 'Deferred object [%s] - function %s - %s' %
            (defer_object, function, now_datetime),
            'filename': '/',
            'send_email': send_email
        }
        deferred_task = deferred_obj.create(deferred_vals)
        deferred_obj.new_process(deferred_task.id)
        new_ctx = deferred_kwargs.get('context', {})
        deferred_obj.with_context(new_ctx).start_process_object(
            deferred_task.id, defer_object,
            function, total_ids,
            deferred_args, deferred_kwargs
        )
        return deferred_obj.show_process(deferred_task.id)

    @api.v8
    def create_deferred_workflow(self, function, total_ids,
                                 send_email=False, deferred_args=[],
                                 deferred_kwargs={}):
        """
        The wrapper function which help to create defer task to run
        a function in background
        @param function: function to run in background
        @param defer_object: Object which contain function to run
        @param total_ids: total ids record need to run function
        """
        deferred_obj = self.env['deferred_processing.task']
        now_datetime = fields.Datetime.context_timestamp(self, datetime.now())
        now_datetime = now_datetime.strftime(DATETIME_FORMAT)
        deferred_vals = {
            'name': 'Deferred workflow function %s - %s' %
            (function, now_datetime),
            'filename': '/',
            'send_email': send_email
        }
        deferred_task = deferred_obj.create(deferred_vals)
        deferred_obj.new_process(deferred_task.id)
        new_ctx = deferred_kwargs.get('context', {})
        deferred_obj.with_context(new_ctx).start_process_workflow(
            deferred_task.id,
            function, total_ids,
            deferred_args, deferred_kwargs
        )
        return deferred_obj.show_process(deferred_task.id)

    @api.v8
    def create_deferred_report(self, defer_ids, report_xml_id,
                               send_email=False):
        """
        """
        deferred_obj = self.env['deferred_processing.task']
        now_datetime = fields.Datetime.context_timestamp(self, datetime.now())
        now_datetime = now_datetime.strftime(DATETIME_FORMAT)
        report = self.env.ref(report_xml_id)
        deferred_vals = {
            'name': 'Deferred report %s - %s' % (report.report_name,
                                                 now_datetime),
            'filename': '/',
            'send_email': send_email
        }
        deferred_task = deferred_obj.create(deferred_vals)
        deferred_obj.new_process(deferred_task.id)
        deferred_obj.start_process_report(
            deferred_task.id,
            defer_ids,
            report_xml_id
        )
        return deferred_obj.show_process(deferred_task.id)
