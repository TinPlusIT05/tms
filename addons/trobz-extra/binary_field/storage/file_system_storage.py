# -*- coding: utf-8 -*-
from openerp import tools
from openerp import SUPERUSER_ID
from .storage import Storage

import os
import sys
import hashlib

import logging
_logger = logging.getLogger(__name__)


class FileSystemStorage(Storage):
    """ Storage allow to store resource as filesystem """

    # =======================================================
    # INTERNAL METHODS (SHOULD NOT BE ACCESSED FROM OUTSIDE)
    # =======================================================

    def _full_path(self, cr, uid, fname):
        """
            Override this method from ir.attachment to
            Get full path to store binary data as file system on hard disk

            :return {string}: path to store data
        """
        data_dir = tools.config.get("data_dir")
        return os.path.join(
            data_dir, self.env.cr.dbname,
            '%s-%s' % (self.model_name, self.field_name), fname
        )

    # =======================================================
    # Code extracted from Odoo V8 in ir_attachment.py
    # Copyright (C) 2004-2014 OPENERP SA
    # License AGPL V3
    # =======================================================
    def _get_path(self, cr, uid, bin_data):
        sha = hashlib.sha1(bin_data).hexdigest()
        # scatter files across 256 dirs
        # we use '/' in the db (even on windows)
        fname = sha[:2] + '/' + sha
        full_path = self._full_path(cr, uid, fname)
        dirname = os.path.dirname(full_path)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        return fname, full_path

    def _file_read(self, cr, uid, fname, bin_size=False):
        full_path = self._full_path(cr, uid, fname)
        r = ''
        try:
            if bin_size:
                r = os.path.getsize(full_path)
            else:
                r = open(full_path, 'rb').read().encode('base64')
        except IOError:
            _logger.error("_read_file reading %s", full_path)
        return r

    def _file_write(self, cr, uid, value):
        bin_value = value.decode('base64')
        fname, full_path = self._get_path(cr, uid, bin_value)
        if not os.path.exists(full_path):
            try:
                with open(full_path, 'wb') as fp:
                    fp.write(bin_value)
            except IOError:
                _logger.error("_file_write writing %s", full_path)
        return fname

    def _file_delete(self, cr, uid, fname):
        obj = self.pool[self.model_name]
        count = obj.search(cr, SUPERUSER_ID, [
            ('%s_uid' % self.field_name, '=', fname),
        ], count=True)
        full_path = self._full_path(cr, uid, fname)
        if count <= 1 and os.path.exists(full_path):
            try:
                os.unlink(full_path)
            except OSError:
                _logger.error("_file_delete could not unlink %s", full_path)
            except IOError:
                # Harmless and needed for race conditions
                _logger.error("_file_delete could not unlink %s", full_path)

    # =======================================================
    # END of extraction
    # =======================================================

    # =======================================================
    # PUCLIC METHODS - WILL BE USED DIRECTLY
    # =======================================================

    def get_url(self, binary_uid):
        """
            Compose full file path, the result should be as bellow
            ..binary-data-dir/db-name/<model-name>-<field-name>/binary-uid
        """
        if not binary_uid:
            return None
        return os.path.join(
            self.config["binary_data_dir"], self.env.cr.dbname,
            "%s-%s" % (self.model_name, self.field_name), binary_uid
        )

    def add(self, value):
        """
            Store new file (binary) to file system

            :param {} value: binary data in string need to be stored

            :return {dict}: stored binary meta information
        """
        if not value:
            return {}
        file_size = sys.getsizeof(value.decode('base64'))
        _logger.debug(
            'Add binary to model: %s, field: %s' % (
                self.model_name, self.field_name
            )
        )
        binary_uid = self._file_write(self.env.cr, self.env.uid, value)
        return {
            'binary_uid': binary_uid,
            'file_size': file_size,
        }

    def update(self, binary_uid, value):
        """
            Update existing file system with new value

            :param {string} binary_uid:
                binary UID info stored in database, this is the name of the
                file stored as file system on hard disk

            :param {string} value: binary data in string need to be stored

            :return {dict}: stored binary meta information
        """
        _logger.debug(
            'Delete binary model: %s, field: %s, uid: %s' % (
                self.model_name, self.field_name, binary_uid
            )
        )
        self._file_delete(self.env.cr, self.env.uid, binary_uid)
        if not value:
            return {}
        return self.add(value)

    def get(self, binary_uid):
        """
            Read binary from stored filesystem

            :param {string} binary_uid:
                binary UID info stored in database, this is the name of the
                file stored as file system on hard disk

            :return {string} binary data presented as string
        """
        if not binary_uid:
            return None
        return self._file_read(self.env.cr, self.env.uid, binary_uid)
