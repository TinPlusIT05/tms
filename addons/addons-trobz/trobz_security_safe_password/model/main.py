# -*- coding: utf-8 -*-
import operator
import openerp
from openerp import http
from openerp.http import request
from openerp.tools.translate import _
from openerp.addons.web.controllers.main import Session
import logging


class Session(Session):

    @http.route('/web/session/change_password', type='json', auth="user")
    def change_password(self, fields):
        """
        Override function:
            - from Session class in web/controllers/main.py
        Reason:
            - Show more detail for except_orm exception.
            - Add unexpected error to log.
        """
        old_passwd, new_passwd, confirm_passwd = \
            operator.itemgetter('old_pwd', 'new_password', 'confirm_pwd')(
                dict(map(operator.itemgetter('name', 'value'), fields)))
        if not (old_passwd.strip() and new_passwd.strip() and
                confirm_passwd.strip()):
            return {'error': _('You cannot leave any password empty.'),
                    'title': _('Change Password')}
        if new_passwd != confirm_passwd:
            return {'error': _('The new password and its confirmation must be '
                               'identical.'),
                    'title': _('Change Password')}
        try:
            if request.session.model('res.users').change_password(old_passwd,
                                                                  new_passwd):
                return {'new_password': new_passwd}
        except Exception, e:
            logging.warning("The below error is logged just " +
                            "in case we would face an unexpected error.")
            logging.error(e)
            if not isinstance(e, openerp.exceptions.except_orm):
                e = (_('Change Password'),
                     _('The old password you provided is incorrect, '
                       'your password was not changed.'))
            return {'error': e[1], 'title': e[0]}
        return {'error': _('Error, password not changed !'),
                'title': _('Change Password')}


# vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:
