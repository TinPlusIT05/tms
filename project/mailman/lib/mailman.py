# -*- coding: utf-8 -*-

import logging
import requests

_logger = logging.getLogger('mailman')


class MailmanException(Exception):

    def __init__(self, response):
        self.response = response
        super(MailmanException, self).__init__(response.text)


class MailmanClient(object):

    def __init__(self, url, timeout=120):
        if url[-1] != '/':
            url += '/'
        self.url = url
        self.timeout = int(timeout)

    def has_list(self, listname):
        response = self.list_lists()
        return listname in response.json()

    def list_lists(self):
        _logger.info("Mailman API list_lists: url: %s", self.url)
        return self._mailman_request('get')

    def members(self, listname, raise_exception=True):
        _logger.info("Mailman API members get request: url: %s", self.url)
        return self._mailman_request('get', uri=listname)

    def subscribe(self, listname, address, fullname):
        data = {'address': address.lower(), 'fullname': fullname}
        _logger.info("Mailman API subscribe: url: %s, listname: %s, data: %s",
                     self.url, listname, data)
        return self._mailman_request('put', uri=listname, data=data)

    def unsubscribe(self, listname, address):
        data = {'address': address}
        _logger.info("Mailman API unsubscribe: url: %s, listname: %s, " +
                     "data: %s", self.url, listname, data)
        return self._mailman_request('delete', uri=listname, data=data)

    def _mailman_request(self, method, uri='', *args, **kw):

        request_args = [self.url + uri] + list(args)
        kw['timeout'] = self.timeout
        response = getattr(requests, method)(*request_args, **kw)

        if response.status_code > 400:
            raise MailmanException(response)
        return response
