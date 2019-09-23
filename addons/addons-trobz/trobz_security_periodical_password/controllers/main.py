from openerp.addons.web.controllers.main import DataSet
from openerp.http import request
import openerp
from openerp import http, tools, _
import datetime as dt
from dateutil import relativedelta as rl
from openerp.exceptions import except_orm


class DataSet(DataSet):

    @http.route(['/web/dataset/call_kw', '/web/dataset/call_kw/<path:path>'],
                type='json', auth="user")
    def call_kw(self, model, method, args, kwargs, path=None):
        if model != 'res.users' and method in ('write', 'create', 'unlink'):
            uid = request.uid
            self.localcontext = request.env['res.users'].context_get()

            config_password_type = request.env['ir.config_parameter']\
                .get_param('config_update_password_type')
            config_password_date = request.env['ir.config_parameter']\
                .get_param('config_update_password_date')
            period_time = int(
                request.env['ir.config_parameter'].get_param(
                    'config_update_password_period'))
            today = dt.date.today()
            """
            + Before browsing uid to get new object of current res_user,
            we need to reset the key "res.users" in prefetch dict
            of environment to empty set to ensure that
            env.prefetch['res_users'] only have one current uid element
            (look: env.prefetch[cls._name].update(ids) in _browse function)
            + If Not reset key res_users in prefetch value of environment, we
            will have extra Administrator (uid=1) will be added to list ids
            when execute function `_read_from_database` in `models.py`.
            This produces missing = res.users(1) which raises
            an weird accesss rule error
            ref: F#17359
            """
            request.env.prefetch['res.users'] = set()  # @UndefinedVariable
            # envt reseted prefetch "res.users"
            res_user = request.env['res.users'].browse(uid)
            if config_password_type == 'periodically':
                time = dt.date.strftime(
                    today - rl.relativedelta(months=period_time),
                    tools.DEFAULT_SERVER_DATE_FORMAT)
                if res_user and res_user.last_password_update and\
                        res_user.last_password_update < time:
                    raise except_orm(_("Warning !"),
                                     _("Your password has not been changed for" +
                                       " the past %s months. Please update your" +
                                       " password before using the system (click" +
                                       " on your name at the top right of" +
                                       " the screen, then 'Preferences', then" +
                                       " 'Change password')") % (period_time,))
            elif config_password_type == 'specified_date':
                if res_user and res_user.last_password_update and\
                    today.strftime('%Y-%m-%d') >= config_password_date and\
                        res_user.last_password_update < config_password_date:
                    raise except_orm(_("Warning !"),
                                     _("Your password must be changed from %s. " +
                                       "Please update your password before using the system " +
                                       "(click on your name at the top right of the screen, " +
                                       "then 'Preferences', then 'Change password')") % (config_password_date,))

        return super(DataSet, self)._call_kw(model, method, args, kwargs)
