# -*- coding: utf-8 -*-
import operator
from openerp import http

from openerp.addons.web.controllers.main \
    import content_disposition, ExportFormat  # @UnresolvedImport
from openerp.addons.web.controllers.main \
    import Home, Binary, serialize_exception  # @UnresolvedImport
from openerp.addons.website.controllers.main \
    import Website  # @UnresolvedImport
from openerp.http import request
import base64
import simplejson  # @UnresolvedImport
from openerp.addons.web.controllers import main  # @UnresolvedImport
import openerp
import werkzeug.utils  # @UnresolvedImport


class Home(Home):

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        '''
        Except for Administrator, Do not allow user to login if
            - User has no group profile
            - User has group profile, but group profile has no inherited group
                and access rights
        '''
        redirect = ''
        main.ensure_db()
        method = request.httprequest.method  # @UndefinedVariable
        if method == 'GET' and redirect and \
                request.session.uid:  # @UndefinedVariable
            return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = openerp.SUPERUSER_ID

        values = request.params.copy()  # @UndefinedVariable
        if not redirect:
            redirect = '/web?' + \
                request.httprequest.query_string  # @UndefinedVariable
        values['redirect'] = redirect

        try:
            values['databases'] = http.db_list()
        except openerp.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':  # @UndefinedVariable
            old_uid = request.uid
            uid = request.session.authenticate(  # @UndefinedVariable
                request.session.db,  # @UndefinedVariable
                request.params['login'],
                request.params['password']
            )
            if uid:
                # Allowing Admin to login (Admin has no profile)
                if uid == 1:
                    return http.redirect_with_hash(redirect)

                user = request.env['res.users'].sudo().browse(request.uid)
                group = user.group_profile_id
                group_inherits = group and group.implied_ids or False
                model_access = group and group.model_access or False
                if group and (group_inherits or model_access):
                    return http.redirect_with_hash(redirect)
            request.uid = old_uid
            values['error'] = "Wrong login/password"
        if request.env.ref('web.login', False):  # @UndefinedVariable
            return request.render('web.login', values)  # @UndefinedVariable
        else:
            # probably not an odoo compatible database
            error = 'Unable to login on database %s' % \
                request.session.db  # @UndefinedVariable
            return werkzeug.utils.redirect(
                '/web/database/selector?error=%s' % error, 303)

    @http.route('/download/support_attachment', type='http', auth="none")
    def downloadattachment(self, path, id):
        f = open(path, 'rb')
        return request.make_response(f, [('Content-Type', 'application/zip')])


class Website(Website):

    @http.route('/', type='http', auth="user", website=True)
    def index(self, **kw):
        return http.local_redirect(
            '/web', query=request.params, keep_hash=True)


def ExportFormat_base(self, data, token):
    params = simplejson.loads(data)
    model, fields, ids, domain, import_compat = \
        operator.itemgetter('model', 'fields', 'ids', 'domain',
                            'import_compat')(
            params)

    Model = request.session.model(model)
    context = dict(request.context or {}, **params.get('context', {}))
    ids = ids or Model.search(domain, context=context)

    if not request.env[model]._is_an_ordinary_table():
        fields = [field for field in fields if field['name'] != 'id']

    field_names = map(operator.itemgetter('name'), fields)
    import_data = Model.export_data(
        ids, field_names, self.raw_data, context=context).get('datas', [])

    if import_compat:
        columns_headers = field_names
    else:
        columns_headers = [val['label'].strip() for val in fields]

    return request.make_response(
        self.from_data(columns_headers, import_data),
        headers=[('Content-Disposition',
                  content_disposition(self.filename(model))),
                 ('Content-Type', self.content_type)],
        cookies={'fileToken': token})


ExportFormat.base = ExportFormat_base


class tms_Binary(Binary):

    @http.route('/web/binary/upload_attachment', type='http', auth="user")
    @serialize_exception
    def upload_attachment(
            self, callback, model, id, ufile):  # @ReservedAssignment
        Model = request.session.model('ir.attachment')  # @UndefinedVariable
        out = """<script language="javascript" type="text/javascript">
                    var win = window.top.window;
                    win.jQuery(win).trigger(%s, %s);
                </script>"""
        try:
            name = ufile.filename.encode(
                'ascii', 'xmlcharrefreplace').encode('utf-8')
            attachment_id = Model.create({
                'name': name,
                'datas': base64.encodestring(ufile.read()),
                'datas_fname': name,
                'res_model': model,
                'res_id': int(id)
            }, request.context)
            args = {
                'filename': name,
                'id': attachment_id
            }
        except Exception as e:
            args = {'error': "%s" % e}
        return out % (simplejson.dumps(callback), simplejson.dumps(args))
