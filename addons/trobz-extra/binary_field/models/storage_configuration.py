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
from openerp import _
from openerp import api, models, fields

# custom storages derived from base Storage
from ..storage.file_system_storage import FileSystemStorage

# supported storage types
STORAGE_TYPES = [
    ("filesystem", _("File System"))
]
STORAGE_CLASSES_MAP = {
    "filesystem": FileSystemStorage
}


class StorageConfiguration(models.Model):

    _name = "storage.configuration"
    _description = "Storage Configuration"

    # ==================================================================
    # FIELD DEFINITIONS
    # ==================================================================

    name = fields.Char("Name")

    type = fields.Selection(
        STORAGE_TYPES, string="Type", help="Type of storage"
    )

    is_default = fields.Boolean(
        string="Is default",
        help=(
            "Tick that box in order to select the default storage "
            "configuration"
        )
    )

    external_storage_server = fields.Boolean(
        string="External Storage Server",
        help=(
            "Tick that box if you want to server the file with an "
            "external server. For example, if you choose the storage "
            "on File system, the binary file can be serve directly with "
            "nginx or apache..."
        )
    )

    base_external_url = fields.Char(
        string="Base external URL",
        help=(
            "When you use an external server for storing the binary "
            "you have to enter the base of the url where the binary can "
            "be accessible."
        )
    )

    # ==================================================================
    # BASE ORM METHODS
    # ==================================================================

    @api.model
    def create(self, vals):
        if vals.get("is_default"):
            self._remove_default()
        return super(StorageConfiguration, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get("is_default"):
            self._remove_default()
        return super(StorageConfiguration, self).write(vals)

    # ==================================================================
    # CUSTOM METHODS
    # ==================================================================

    def _remove_default(self):
        """
            > For internal use

            When a new configuration is created or when an existing
            configuration is updated with `default` flag set, the
            other configurations need to be reset back to non-default

            called by the "create" and "write" method
        """
        configs = self.search([("is_default", "=", True)])
        configs.exists() and configs.write({"is_default": False})

    def _get_config(self, model_name, field_name):
        """
            > For internal use

            BinaryField | ImageField can be used to store image as filesystem
            based on configuration (this class) for all field instances

            :param {string} model_name:
                name of model to get configuration, it's usually the
                model which has fields of type BinaryField or ImageField

            :param {string} field_name:
                name of field which is an instance
                of BinaryField or ImageField

            :return {dict}: read data from storage.configuration object
        """
        field_pool = self.env["ir.model.fields"]
        field_domain = [("model", "=", model_name), ("name", "=", field_name)]
        field = field_pool.search(field_domain)

        # get attached storage of BinaryField or ImageField in ir.model.fields
        storage = field.storage_id

        # if no fields like this on current system after module installtion
        if not field.exists():
            raise orm.except_orm(
                _("Dev Error"),
                _("The field %s with do not exist on the model %s")
                % (field_name, model_name)
            )

        # if no configuration found on ir.model.fields record, get it directly
        if not field.storage_id.exists():
            storage = self.search([("is_default", "=", True)])
            if not storage.exists():
                raise orm.except_orm(
                    _("User Error"),
                    _("There is no default storage config, please add one")
                )

        config = storage.read(self._fields.keys())
        return config and config[0] or False

    def get_storage(self, field_name, record):
        """
            This method will be internally called by the instance of
            BinaryField or ImageField when it needs to write contents of
            image it's holding.

            :param {string} field_name:
                name of BinaryField or ImageField field

            :param {openerp.models.BaseModel} record:
                recordset which has field of type BinaryField or ImageField,
                in this case is the record we are working on

            :return {binary_field.storage.Storage} storage:
                storage object (FileSystemStorage inherits from Storage)
        """
        # read config (storage.configuration)
        config = self._get_config(record._name, field_name)
        storage_class = STORAGE_CLASSES_MAP.get(config["type"])
        return storage_class(self.env, field_name, record._name, config)

