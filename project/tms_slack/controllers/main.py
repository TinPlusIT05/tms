# -*- coding: utf-8 -*-

import re

from openerp import SUPERUSER_ID, tools
from openerp.addons import web  # @UnresolvedImport
from openerp.modules.registry import RegistryManager
from openerp.addons.tms_slack.lib.slack import SlackClient  # @UnresolvedImport

openerpweb = web.http


class WebhookClient(openerpweb.Controller):
    _cp_path = "/web/hooks"

    _reg = None
    _cr = None

    @openerpweb.jsonrequest
    def gitlab_build(self, req):
        """
        Handle Gitlab CI build status request (webhook)
        and post message to Slack chat service
        """

        # has to be done at this time, before logging has not been configured
        # by openerp
        import logging
        _logger = logging.getLogger('webhooks')

        data = req.jsonrequest
        db = req.httprequest.args.get('db')
        channel = req.httprequest.args.get('channel', 'general')
        status = data.get('build_status')
        ret = {'info': 'nothing to do...'}
        build_ret = None

        if not db or not channel:
            _logger.error(
                'missing "db" or "channel" in gitlab-ci request GET parameter')
            return {
                'error': 'missing "db" or "channel" parameter in request',
                'code': 500}

        _logger.info(
            'Process gitlab-ci hook for slack channel %s with status %s',
            channel,
            status)

        project = self.get_project_from_data(db, data)

        if not project:
            _logger.warning(
                'No project found for %s url...',
                data.get('gitlab_url'))

            if status == 'failed':
                ret = self.publish_failed_report(db, channel, data)

        else:
            _logger.info('gitlab-ci build %s on project', project.name)

            cr = self.cursor(db)

            cr.commit()
        _logger.debug('Build model has returned: %s', build_ret)
        _logger.debug('Gitlab CI TMS hook response: %s', ret)
        return ret

    def publish_report(self, db, channel, data, status, build=None):
        if status == 'failed':
            return self.publish_failed_report(db, channel, data)
        else:
            return self.publish_success_report(db, channel, data, build)

    def publish_success_report(self, db, channel, data, build):
        gitlab_ci_url = self.get_param(db, 'gitlab_ci_url')
        ci_url = "%s/projects/%s/builds/%s" % (
            gitlab_ci_url,
            data.get('project_id'),
            data.get('build_id')
        )
        title = '<%s|Build Success>' % ci_url
        message = 'Build fixed for project %s, branch %s, thanks %s !\n' % \
                  (data.get('project_name'),
                   data.get('ref'),
                      data.get('push_data').get('user_name'))

        if build.status_duration:
            nb = build.status_counter
            message += 'Project branch was sick during %s and' \
                       ' %s commit%s tried to cure it...' % \
                       (build.status_duration, nb,
                        's have' if nb > 1 else ' has')

        return self.publish(db, channel, title, message,
                            message_type='success',
                            icons=(':syringe:', ':pill:', ':ambulance:',
                                   ':heart:', ':heartpulse:', ':pray:'))

    def publish_failed_report(self, db, channel, data):
        gitlab_ci_url = self.get_param(db, 'gitlab_ci_url')
        ci_url = "%s/projects/%s/builds/%s" % (
            gitlab_ci_url,
            data.get('project_id'),
            data.get('build_id')
        )
        title = '<%s|Build Failed>' % ci_url
        message = 'Build failed for project %s, branch %s (%s),' \
                  ' with a commit made by %s.' % \
                  (data.get('project_name'),
                   data.get('ref'),
                      data.get('sha')[:9],
                      data.get('push_data').get('user_name'))

        return self.publish(db, channel, title, message, message_type='error',
                            icons=(':rotating_light:', ':fire:',
                                   ':collision:', ':rage:', ':broken_heart:',
                                   ':scream_cat:'))

    def publish(self, db, channel, title, message, message_type='success',
                icons=None):
        slack_url = self.get_param(db, 'webhook_slack_access')
        slack_token = tools.config.get('slack_token', '')
        slack_url += slack_token
        slack = SlackClient(slack_url, username='Gitlab CI')

        if icons:
            ret = getattr(slack, message_type)('#%s' % channel, title, message,
                                               icons)
        else:
            ret = getattr(slack, message_type)('#%s' % channel, title, message)

        if ret.status_code > 400:
            return {'code': ret.status_code, 'error': ret.text}
        else:
            return {'info': ret.text}

    def get_project(self, db, name):
        # has to be done at this time, before logging has not been configured
        # by openerp
        import logging
        _logger = logging.getLogger('webhooks')

        cr, uid = self.cursor(db), SUPERUSER_ID

        project = None
        project_model = self.pool(db, 'tms.project')
        ids = project_model.search(
            cr, uid, [
                ('project_branch_list', 'like', name)])

        if ids:
            if len(ids) > 1:
                _logger.warn(
                    'More than 1 project is matching with name %s,'
                    ' use the first one...', name)

            project = project_model.browse(cr, uid, ids[0])

        return project

    def get_project_from_data(self, db, data):
        project = None

        # get project matching with git repository name
        project_exp = re.compile(r"(?P<name>[^/]+)/[^/]+$")
        gitlab_url = data.get('gitlab_url')
        found = project_exp.search(gitlab_url)

        if found:
            project = self.get_project(db, found.group('name'))

        return project

    def get_param(self, db, name):
        cr, uid = self.cursor(db), SUPERUSER_ID

        config_param = self.pool(db, 'ir.config_parameter')
        param = config_param.get_param(cr, uid, name, default=None)

        if not param:
            raise Exception('"%s" config parameter not found.' % name)

        return param

    def pool(self, db, model_name):
        registry = self.registry(db)
        return registry[model_name]

    def cursor(self, db):
        if not self._cr:
            self._cr = self.registry(db).db.cursor()
        return self._cr

    def registry(self, db):
        if not self._reg:
            self._reg = RegistryManager.get(db)
        return self._reg
