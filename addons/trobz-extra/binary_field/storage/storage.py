# -*- coding: utf-8 -*-


class Storage(object):
    """
        Base class for all kind of storages
    """

    def __init__(self, env, field_name, model_name, storage_configuration):
        """
            Init Storage object to store file depending on configuration

            :param {object} env:
                environment which hold database cursor

            :param {string} field_name:
                BinaryField | ImageField field name

            :param {string} model_name:
                Working model_name which contains BinaryField or ImageField

            :param {storage.configuration dict} storage_configuration:
                Storage configuration from database, should be taken into
                account default record in storage.configuration object or
                setting on BinaryField | ImageField in ir.model.fields object
        """
        self.env = env
        self.pool = env.registry  # for version compatibility so we keep pool

        self.field_name = field_name
        self.model_name = model_name

        self.config = storage_configuration
        self.external_storage_server = self.config["external_storage_server"]

