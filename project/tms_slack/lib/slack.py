# -*- coding: utf-8 -*-

import requests
import json
import random

import logging

_logger = logging.getLogger('slack')


class SlackClient(object):

    def __init__(self, url, username='TMS'):
        self.url = url
        self.username = username

    def error(self, channel, title, message, icons=(':fire:',)):
        return self.post(channel, extra={
            'icon_emoji': random.choice(icons),
            'attachments': [
                {
                    'fallback': title,
                    'pretext': title,
                    'color': 'danger',
                    'fields': [
                        {
                            'value': message,
                            'short': True
                        }
                    ]
                }
            ]
        })

    def success(self, channel, title, message, icons=(':thumbsup:',)):
        return self.post(channel, extra={
            'icon_emoji': random.choice(icons),
            'attachments': [
                {
                    'fallback': title,
                    'pretext': title,
                    'color': 'good',
                    'fields': [
                        {
                            'value': message,
                            'short': True
                        }
                    ]
                }
            ]
        })

    def post(self, channel, extra={}):
        """
        Post a slack message in a project channel
        """

        base = {
            'channel': channel,
            'username': self.username
        }
        base.update(extra)

        _logger.debug(
            "Slack post request: \n - url: %s\n- payload: %s",
            self.url,
            base)
        try:
            response = requests.post(
                self.url,
                data=json.dumps(base),
                allow_redirects=True,
                timeout=10,
            )
        except Exception as e:
            _logger.warning("Slack post failed to many times... Abort it.")
            response = {'status_code': 666, 'text': str(e)}

        return response
