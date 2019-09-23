# -*- coding: utf-8 -*-

import email
import logging
import xmlrpclib
from openerp import models, api


_logger = logging.getLogger(__name__)


class mail_thread(models.AbstractModel):

    _inherit = 'mail.thread'

    @api.model
    def message_process(self, model, message, custom_values=None,
                        save_original=False, strip_attachments=False,
                        thread_id=None):
        """
        Override function
        Remove the previous contents if the incoming mail server
        with field `only_message` check
        """
        context = self._context and self._context.copy() or {}

        # extract message bytes - we are forced to pass the message as binary
        # because we don't know its encoding until we parse its headers and
        # hence can't convert it to utf-8 for transport between
        # the mailgate script and here.
        if isinstance(message, xmlrpclib.Binary):
            message = str(message.data)
        # Warning: message_from_string doesn't always work correctly on unicode
        # we must use utf-8 strings here :-(
        if isinstance(message, unicode):
            message = message.encode('utf-8')
        msg_txt = email.message_from_string(message)

        # parse the message, verify we are not in a loop by checking message_id
        # is not duplicated
        msg = self.message_parse(
            msg_txt, save_original=save_original)

        # if 'only_message' in context, we get only content message reply
        # Remove previous content and signature from reply
        if context.get('only_message', False):
            msg['body'] = msg['body'][:msg['body'].find('_quote')][
                :msg['body'][:msg['body'].find('quote')].rfind(
                    '<div class', 0)][:msg['body'][:msg['body'].find(
                        '_signature')].rfind('<div class', 0)]
        if strip_attachments:
            msg.pop('attachments', None)

        # should always be True as message_parse generate one if missing
        if msg.get('message_id'):
            existing_msg_objs = self.env['mail.message'].search(
                [('message_id', '=', msg.get('message_id'))])
            if existing_msg_objs:
                _logger.info('Ignored mail from %s to %s with Message-Id %s:'
                             ' found duplicated Message-Id during processing',
                             msg.get('from'), msg.get('to'),
                             msg.get('message_id'))
                return False

        # find possible routes for the message
        routes = self.message_route(
            msg_txt, msg, model, thread_id, custom_values)
        thread_id = self.message_route_process(msg_txt, msg, routes)
        return thread_id
