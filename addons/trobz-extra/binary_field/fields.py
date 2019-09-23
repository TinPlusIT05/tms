# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2014 Akretion (http://www.akretion.com).
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
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

from openerp import tools
from openerp import api, models, fields
from openerp.tools import image_resize_image

from operator import attrgetter

import copy
from collections import defaultdict

import logging
_logger = logging.getLogger(__name__)


class BinaryField(fields.Binary):
    """
        This is base class for all type of Binary field
    """

    def __init__(self, **kwargs):
        """
            Initialize a BinaryField

            Override default parameter to make this kind of field work
        """
        super(BinaryField, self).__init__(
            readonly=False,
            compute=self._compute_read,
            inverse=self._compute_write,
            **kwargs
        )

    def _prepare_binary_meta(self, field_name, binary_info):
        """
            Prepare binary meta data that should be updated to database
            right after binary file has been processed successfully
            (stored in hard disk as file system with filesystem in
            storage configuration)

            :param {string} field_name:
                current BinaryField field name

            :param {dict} binary_info:
                binary meta data for binary field

            :return {dict}:
                data to be update to database (binary meta)
        """
        return {
            '%s_uid' % field_name: binary_info.get('binary_uid'),
            '%s_file_size' % field_name: binary_info.get('file_size'),
        }

    def _compute_read(self, records):
        """
            Control how value of Binary should be read, and it depends on
            storage configuration type:

            + filesystem (File System):
                contents of this field should be read from file system based
                on UID stored in database.

            :param {openerp.fields.BinaryField} self:
                current field instance

            :param {opnerp.models.BaseModel} record:
                current recordset
        """
        field_name = self.name
        config_pool = records.env["storage.configuration"]

        # for safety - do it for each record in the set
        for record in records:

            # get corresponding storage based on configuration
            storage = config_pool.get_storage(field_name, record)

            # get stored UID in database (location of the file)
            binary_uid = record['%s_uid' % field_name]

            # read binary data depend on the configuration
            record[field_name] = binary_uid and self._read_binary(
                storage, record, binary_uid
            ) or None

    def _compute_write(self, records):
        """
            Control how value of BinaryField should be updated
            and it depends on storage configuration type:

            + filesystem (File System):
                contents of this field should be stored as file system, then
                information related to this stored file system should be
                updated to database for the next retrieval (read)

            :param {openerp.fields.BinaryField} self:
                current field instance

            :param {opnerp.models.BaseModel} record:
                current working recordset
        """


        # for safety - do it for each record in the set
        for record in records:

            # current binary field name
            field_name = self.name

            # binary value of field taken from the form view
            binary_value = record[field_name]

            # write value
            self._write_binary(record, field_name, binary_value)

        return True

    def _read_binary(self, storage, record, binary_uid):
        """
            Internal method to read contents from binary field
            depending on storage configuration

            :param {dict} storage:
                default storage configuration

            :param {openerp.models.BaseModel} record:
                current recordset to read data from

            :param {string} binary_uid:
                binary UID (file name) of binary file
        """
        # FIXME: should process context
        context = record.env.context
        field_name = self.name

        binary_size = context.get(
            "bin_size_%s" % field_name, context.get("bin_size")
        )

        # Compatibility with existing binary field
        if binary_size:
            size = record["%s_file_size" % field_name]
            return tools.human_size(long(size))
        return storage.get(binary_uid)

    def _write_binary(self, record, field_name, value):
        """
            Internal method to write binary contents depending on storage
            configuration

            :param {openerp.models.BaseModel} record:
                current working recordset, in this case is single record

            :param {string} field_name:
                field to write binary contents

            :param {string} value:
                binary value to write in string format
        """

        config_pool = record.env["storage.configuration"]

        # get corresponding storage based on configuration
        storage = config_pool.get_storage(field_name, record)

        # previous binary UID in database (hashed file name + SHA1)
        binary_uid = record["%s_uid" % field_name]

        # binary value of field taken from the form view
        binary_value = value

        # write binary data based on configuration (store as file system)
        binary_info = binary_uid \
                and storage.update(binary_uid, binary_value) \
                or storage.add(binary_value)

        # binary info ready to write to database
        uid_size_info = self._prepare_binary_meta(field_name, binary_info)

        # write binary info to database related meta information
        record.write(uid_size_info)

class ImageField(BinaryField):
    """
        Class for all ImageField type

        The __init__ should take optional parameters as bellow

        :param {string} resize_based_on:
            name of the field that should be resized

        :param {integer} width:
            width of the image resized

        :param {integer} height:
            height of the image resized
    """

    def _compute_write(self, records):
        """
            Control how a value of ImageField should be updated, when an
            ImageField field is updated should consider the case:

            - current field is parent field or child field:
                the parent field should be always update first, then update
                related child fields.

            :param {openerp.models.BaseModel} records:
                current working recordset
        """
        field_name = self.name

        # for safety - do it for each record in the set
        for record in records:

            # get context on record
            context = record.env.context

            # current ImageField binary value to write
            binary_value = record[field_name]

            # get current field object
            field_object = record._fields[field_name]

            # if current field is child field, get parent field
            parent_field = field_object._attrs.get("resize_based_on")

            # when user updates child field DIRECTLY
            #   > update parent field first
            # when refresh image cache means update child field INDIRECTLY
            #   > skip the update because it will cause infinite loop,
            #     so go to the `else` instead
            if parent_field and not record.env.context.get("refresh_image_cache"):
                record[parent_field] = binary_value
                return
            else:
                width = field_object._attrs.get("height")
                height = field_object._attrs.get("width")
                if width or height:
                    size = (height or 64, width or 64)
                    binary_value = image_resize_image(binary_value, size)

                # write resized binary image
                self._write_binary(record, field_name, binary_value)

                # refresh child field cached (if has)
                for _name, _field in record._fields.items():

                    # if current field is instance of BinaryField
                    if not isinstance(_field, BinaryField): continue

                    # if current field is child field of binary field
                    if _field._attrs.get("resize_based_on") == field_name:
                        _field._refresh_cache(record)
        return

    def _refresh_cache(self, record):
        """
            Refresh the cache of the child field to resize again based on new
            binary value from parent field or totally remove all if parent
            field is not set.

            :params {openerp.models.BaseModel} record:
                current recordset (one) to update value for binary field
        """
        field = record._fields[self.name]
        parent_field = field._attrs.get("resize_based_on")

        _logger.debug(
            'Refreshing Image Cache from the field %s of object '
            '%s id : %s' % (field.name, record._name, record.id)
        )

        ctx = record.env.context.copy()
        # skip update parent field again in `_compute_write`
        # otherwise we will see infinite loop
        ctx['refresh_image_cache'] = True
        ctx["bin_base64_%s" % field._attrs.get("resize_based_on")] = True

        resized_image = None
        if parent_field:
            original_binary = getattr(record, parent_field)
            size = (field._attrs.get("height"), field._attrs.get("width"))
            resized_image = image_resize_image(original_binary, size)

        record.with_context(**ctx)[field.name] = resized_image

    def _read_binary(self, storage, record, binary_uid):
        """
            Internal method to read contents from binary field
            depending on storage configuration.

            :param {dict} storage:
                default storage configuration

            :param {openerp.models.BaseModel} record:
                current recordset to read data from

            :param {string} binary_uid:
                binary UID (file name) of binary file
        """
        context = record.env.context
        field_name = self.name

        if not context.get('bin_size_%s' % field_name)\
                and not context.get('bin_base64_%s' % field_name)\
                and storage.external_storage_server:
            if context.get('bin_size'):
                # To avoid useless call by default for the image
                # We never return the bin size but the url
                # SO I remove the key in order to avoid the
                # automatic conversion in the orm
                context.pop('bin_size')
            return storage.get_url(binary_uid)
        else:
            return super(ImageField, self)._read_binary(
                storage, record, binary_uid
            )

# ===============================================
# Enable registering field by fields.<field-type>
# from openerp import fields
# ===============================================

fields.BinaryField = BinaryField
fields.ImageField = ImageField

# ===============================================
# Hack to support new code from OCA
# ===============================================

@api.model
def _setup_fields(self):
    """ Setup the fields, except for re-computation triggers. """
    cls = type(self)

    # set up fields, and determine their corresponding column
    cls._columns = {}

    # hack
    copy_fields = cls._fields.copy()

    def add(name, field):
        if name not in cls._fields:
            cls._add_field(name, field)

    # weird bug that inside setup fields lose context
    # for `fields` from `openerp`, re-import fields
    from openerp import fields

    for name in copy_fields:
        field = copy_fields[name]
        if field and isinstance(field, BinaryField):
            image_uid = fields.Char('%s UID' % field.string)
            image_file_size = fields.Integer('%s File Size' % field.string)
            add('%s_uid' % name, image_uid)
            add('%s_file_size' % name, image_file_size)

    for name, field in cls._fields.iteritems():

        field.setup(self.env)
        column = field.to_column()
        if column:
            cls._columns[name] = column

    # determine field.computed_fields
    computed_fields = defaultdict(list)
    for field in cls._fields.itervalues():
        if field.compute:
            computed_fields[field.compute].append(field)

    for fields in computed_fields.itervalues():
        for field in fields:
            field.computed_fields = fields

models.BaseModel._setup_fields = _setup_fields
