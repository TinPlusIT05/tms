# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for Odoo
#   Copyright (C) 2015 Trobz (http://www.trobz.com).
#   @author Tran Quang Tri <tri@trobz.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import os
import base64

from openerp import http
from openerp.http import request
from openerp.service import security
from openerp.exceptions import AccessDenied


class SecureFieldController(http.Controller):

    def generate_token(self):
        """
            Generate token as base64 format.

            This method can be enhanced by generating
            user-specific token (based on IP..), for now it
            just random base64 string
        """
        _res = os.urandom(32)
        return base64.b64encode(_res)

    def ensure_token(self):
        """
            Create default token.
            Make sure that tokens is always up
        """
        session = http.request.session
        session.secure_tokens = hasattr(session, "secure_tokens") \
            and getattr(session, "secure_tokens") or []
        return session.secure_tokens

    def get_tokens(self):
        """
            Get a list of all stored tokens
        """
        self.ensure_token()
        return http.request.session.secure_tokens

    def token_valid(self, token):
        """
            check if user token is valid to perform read/write
            on Secure field
        """
        tokens = self.get_tokens()
        return token and token in tokens

    def remove_token(self, token):
        """
            Remove specific token from the list
            (after finishing execution/user close the pop-up)
        """
        tokens = self.get_tokens()
        if token in tokens:
            tokens.remove(token)
            return True
        return False

    @http.route("/web/secure/remove_token", type="json", auth="user")
    def remove_server_token(self, token):
        """
            Remote specific token after finishing a session

            @param {str} token: token to be removed
            @return {bool} token removal successful or not
        """
        return self.remove_token(token)

    @http.route('/web/secure/authenticate', type='json', auth="user")
    def request_authority(self, ids, password, model, field):
        """
            Check user authentication to work with Secure field
            on Secure model

            @param {list} ids: recordset's ids to work with
            @param {str} password: current user password to check
            @param {str} model: name of Secure model
            @param {str} field: name of Secure field

            @param {dict} response message
        """
        tokens = self.get_tokens()
        model_object = request.env[model]
        field_object = getattr(model_object, "_fields").get(field)

        try:
            # check for user authentication
            security.check(
                request.session.db, http.request.session.uid, password
            )
        except AccessDenied:
            return {
                "token": False,
                "authorized": False,
                "message": "You are not authorized",
            }

        # check field security on record-set
        records = model_object.browse(ids)
        security_checks = field_object.security(records)

        if not security_checks:
            return {
                "token": False,
                "authorized": False,
                "message": "You are not allowed to access this field",
            }

        # use token to prevent bypassing authentication process
        token = self.generate_token()

        # add token into the list
        token and tokens.append(token)

        return {
            "token": token,
            "authorized": True,
            "message": "You are authorized",
        }

    @http.route("/web/secure/read", type="json", auth="user")
    def request_read(self, ids, model, field, token):
        """
            Request to read contents of Secure field on Secure model

            @param {list} ids: recordset's ids to work with
            @param {str} model: name of Secure model
            @param {str} field: name of Secure field
            @param {str} token: access token

            @param {dict} response message
        """
        if self.token_valid(token) and ids:
            model_object = request.env[model]
            records = model_object.browse(ids)
            vals = records.read_secure(fields=[field])
            return {
                "result": vals
            }
        return {
            "authorized": False,
            "message": "Your token is expired",
        }

    @http.route("/web/secure/write", type="json", auth="user")
    def request_write(self, ids, model, field, value, token):
        """
            Request to update contents of Secure field on Secure model

            @param {list} ids: recordset's ids to work with
            @param {str} model: name of Secure model
            @param {str} field: name of Secure field
            @param {str} value: raw value to be updated
            @param {str} token: access token

            @param {dict} response message
        """
        if self.token_valid(token) and ids:
            model_object = request.env[model]
            records = model_object.browse(ids)
            result = records.write({field: value})
            return {
                "authorized": result,
                "message": result
                and "Saved successfully"
                or "Value is failed to update"
            }
        return {
            "authorized": False,
            "message": "Your token is expired",
        }
