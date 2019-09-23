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

from openerp import models, api

from .fields import secure_v7
from .fields import secure_v8

import copy
import logging
_logger = logging.getLogger(__name__)


class SecureModel(models.BaseModel):

    # automatically create a corresponding table
    _auto = True

    # not visible in ORM registry, meant to be python-inherited only
    _register = False

    # True in a TransientModel
    _transient = False

    def __init__(self, pool, cr):
        """
            Add custom cache to store secure field defined
            by the model for later use
        """
        cls = type(self)
        cls._secure_fields = {}
        super(SecureModel, self).__init__(pool, cr)

    # ========================================================================
    # READ AREA :: READ CONTENTS FROM SECURE FIELD
    # ========================================================================

    @api.v8
    def _read_secure(self, fields=None, load="_classic_read", strict=True):
        """
            Private implementation of read method to read contents from
            Secure Field after checking authentication.

            @param {list} fields: list of field names to read, including
                secure field.

            @param {bool} strict: this mode is enabled by default

            @return {list}: read data.
        """

        # get all fields objects from the object
        fields_def = getattr(self, "_fields")

        # get fields name to read
        fields = fields or fields_def.keys()

        # read raw data except for `secure` column, receive ***
        read_results = super(SecureModel, self).read(fields=fields, load=load)

        # mapping record for quick reference purpose
        records_map = {_record.id: _record for _record in self}

        for result in read_results:
            for field_name in result:
                field = fields_def.get(field_name)

                if field.type == "secure":

                    # current singleton record-set
                    _record = records_map.get(result.get("id"))

                    # check if current field requires password to see value
                    _password_required = field.is_pwd_auth_required()

                    # default value for secure field
                    _value = "******************"

                    # user is able to access field
                    if field.security(_record):

                        # only show password directly when password is not
                        # required or required with strict mode disabled
                        if not _password_required or not strict:

                            # get value stored in the cache
                            ecr_value = _record._cache.get(field_name)

                            # value to read should be decrypted
                            _value = ecr_value and field.decrypt(
                                self, ecr_value
                            )

                    # user is unable to access field
                    else:
                        if not _password_required:
                            # in non-password mode > show directly warning
                            # message
                            _value = "You don’t have access to this information"

                    # update value for current record's field
                    result.update({field_name: _value})

        return read_results

    @api.v7
    def read_secure(self, cr, user, ids, fields=None, context=None,
                    load='_classic_read'):
        records = self.browse(cr, user, ids, context)

        # change context by calling function from class scope
        return records._read_secure(fields=fields, load=load, strict=False)

    @api.v8
    def read_secure(self, fields, load='_classic_read'):

        return self._read_secure(fields=fields, load=load, strict=False)

    @api.v7
    def read(self, cr, user, ids, fields=None, context=None,
             load='_classic_read'):
        records = self.browse(cr, user, ids, context)
        result = SecureModel._read_secure(records, fields=fields, load=load)
        return result if isinstance(ids, list) else (bool(result) and result[0])

    @api.v8
    def read(self, fields=None, load="_classic_read"):

        return self._read_secure(fields=fields, load=load)

    # ========================================================================
    # WRITE AREA :: UPDATE CONTENTS OF SECURE FIELD
    # ========================================================================

    def _secure_write(self, vals):
        """
            Private implementation of write method to update contents of
            Secure field.

            @param {dict} vals: value to be updated
            @return {dict}: processed value
        """
        fields = getattr(self, "_fields")
        secure_fields = self._get_secure_fields()

        # make a copy of vals due to size change during loop (pop)
        for _field, value in copy.deepcopy(vals).iteritems():

            field = fields.get(_field)

            if _field in secure_fields:

                if field.security(self):
                    value = value and field.encrypt(self, value) or ""
                    vals.update({_field: value})
                else:
                    vals.pop(_field)

        return super(SecureModel, self).write(vals)

    @api.multi
    def write(self, vals):

        return self._secure_write(vals)

    # ========================================================================
    # CREATE AREA :: FOR NEWLY CREATED RECORD
    # ========================================================================

    @api.model
    def create(self, vals):

        fields = getattr(self, "_fields")
        secure_fields = self._get_secure_fields()

        # size of vals can be changed so it's better to make a copy
        for _field, value in copy.deepcopy(vals).iteritems():

            field = fields.get(_field)

            if _field in secure_fields:
                if field.security(self):
                    value = value and field.encrypt(self, value) or ""
                    vals.update({_field: value})
                else:
                    vals.update({ _field: False }) \
                        if field and field.required else vals.pop(_field)

        return super(SecureModel, self).create(vals)

    # ========================================================================
    # BUILD LIST OF SECURE FIELDS AVAILABLE IN THE MODEL
    # ========================================================================

    def fields_get(self, cr, user,
                   allfields=None, context=None,
                   write_access=True, attributes=None):
        """
            Add extra information for each secure field to be rendered
            on the client side
        """
        # super call
        result_fields_get = super(SecureModel, self).fields_get(
            cr, user, allfields=allfields, context=context,
            write_access=write_access, attributes=attributes
        )
        # current model fields
        fields = getattr(self, "_fields")

        # list of secure fields defined in this model
        secure_fields = self._get_secure_fields()

        # if secure fields are used on the model > add extra information
        for field_name in secure_fields:
            if field_name in result_fields_get:
                field = fields.get(field_name)
                field_get = result_fields_get.get(field_name)

                field_get.update({
                    "is_pwd_auth_required": field.is_pwd_auth_required(),
                    "is_multiline_required": field.is_multiline_required()
                })

        return result_fields_get

    @api.model
    def _setup_complete(self):
        """
            Cache secure fields defined by the model
        """
        complete_setup = super(SecureModel, self)._setup_complete()
        fields = getattr(self, "_fields")
        for _field_name in fields:
            if issubclass(secure_v8.Secure, type(self._fields[_field_name])):
                self._secure_fields[_field_name] = self._fields[_field_name]

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _get_secure_fields(self):
        """
            get a list of secure fields defined by the model
        """
        return self._secure_fields

setattr(models, "SecureModel", SecureModel)
