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

from openerp import SUPERUSER_ID
from openerp import fields, osv
from openerp.tools import config
from openerp.exceptions import Warning

from Crypto.Cipher import AES
import base64
import logging
_logger = logging.getLogger(__name__)


class Secure(fields.Field):

    type = 'secure'

    # The character used for padding
    # with a block cipher such as AES, the value you encrypt must be a
    # multiple of BLOCK_SIZE in length. This character is used to ensure
    # that your value is always a multiple of BLOCK_SIZE
    _PADDING = '{'

    # The block size for the cipher object; must be 16, 24, or 32 for AES
    _BLOCK_SIZE = 32

    def _ensure_cipher(self, record):
        """
            ensure that cipher object is always available to
            perform encryption/decryption

            @param record: recordset
            @return: cipher object used for encryption/decryption
        """

        if not hasattr(self, "_cipher"):

            # get raw secret key
            raw_key = self.secret_key(record)

            # set cipher for current field self
            setattr(self, "_cipher", AES.new(raw_key))

        return getattr(self, "_cipher")

    # Sufficiently pad the text to be encrypted
    def _pad(self, text):
        return text + (
            Secure._BLOCK_SIZE - len(text) % Secure._BLOCK_SIZE
        ) * Secure._PADDING

    def _default_secret_key(self, record):
        """
            Get secret key, this method should be overridden to provide
            custom secret key for each field instance if user wants to
            get secret key somewhere other than configuration file.

            + Secret key can be auto-generated as shown below:
            ```
             os.urandom(BLOCK_SIZE)
             # where BLOCK SIZE is the block size of cipher object
            ```

            + Using CLI
            ```
            dd if=/dev/urandom bs=16 count=1 2>/dev/null | md5sum | cut -d' ' -f1
            ```
            @param record: recordset
        """
        _logger.debug("Calling default get secret key")
        key_config = config.get('field_secure_secret_key')
        key_config = key_config and key_config.decode('utf-8')

        if not key_config:
            raise Warning(
                'Missing secret key',
                'No secret key configured'
            )
        return key_config

    def _default_encrypt(self, record, raw_contents):
        """
            Encrypt raw contents and encode it to base64

            @param record: recordset
            @param raw_contents: content from text box
            @return: base64 encrypted string (AES algorithm)
        """
        _logger.debug("Calling default enryption")
        _cipher = self._ensure_cipher(record)
        raw_cipher_text = _cipher.encrypt(self._pad(raw_contents))

        return base64.b64encode(raw_cipher_text)

    def _default_decrypt(self, record, cipher_text):
        """
            Decode base64 contents to get cipher text then decrypt the text
            back to raw contents

            @param record: recordset
            @param cipher_text: encrypted text using AES algorithm
            @return: raw contents (decrypted contents)
        """
        _logger.debug("Calling default decryption")
        _cipher = self._ensure_cipher(record)
        _raw_cipher_text = base64.b64decode(cipher_text)
        _decrypt = _cipher.decrypt(_raw_cipher_text)

        return _decrypt.rstrip(Secure._PADDING)

    def _default_security(self, record):
        """
            User must specify `security` option in field definition
            to provide custom validation on reading/writing field value

            @param record: recordset
        """
        _logger.debug("Calling default security check")
        return record.env.uid == SUPERUSER_ID

    def __init__(
            self,
            encrypt=None, decrypt=None, secret_key=None, security=None,
            password=None, multiline=None, *args, **kwargs):
        """
            @param encrypt:
                method used to encrypt the contents (optional).

            @param decrypt:
                method used to decrypt the contents (optional).

            @param secret_key:
                method used to get secret key (optional).
                the content of the secret key should be 32 bytes length string

            @param security:
                method to provide security check for authorization,
                this is just a part of security check
        """
        super(Secure, self).__init__(
            _encrypt=encrypt,
            _decrypt=decrypt,
            _secret_key=secret_key,
            _security=security,
            _is_pwd_auth_required=password,
            _is_multiline_required=multiline,
            *args, **kwargs
        )

    def _get_field_method(self, record, name):

        default_method = '_default%s' % name

        if hasattr(self, name):

            # get user defined version
            field_method = getattr(self, name)

            if isinstance(field_method, (str, unicode)):
                if hasattr(record.__class__, field_method):
                    field_method = getattr(record.__class__, field_method)
                else:
                    raise Warning(
                        "Method not found",
                        "Method \"%s\" not found on model %s." % (
                            field_method, getattr(record, "_name")
                        )
                    )

        elif hasattr(self, default_method):
            field_method = getattr(self, default_method)
        else:
            raise Warning(
                "Method not found",
                "Secure field method %s not found." % name
            )

        return field_method

    # ==================================================================
    # Getter methods to get by default or user defined
    # encrypt/decrypt/secret_key/security.
    # ---------------------------------------------------------
    # methods below are high level implementation of
    # security/decrypt/encrypt/secret_key feature which
    # are not intended to be overridden
    # ==================================================================

    def secret_key(self, record):
        """
            get the secret key
            @param record: current recordset
            @return: secret key
        """
        return self._get_field_method(record, "_secret_key")(record)

    def security(self, record):
        """
            Default security implementation is not implemented on
            the `SecureModel` but on its subclasses

            @param record: current recordset
            @return Boolean: True|False
        """
        return self._get_field_method(record, "_security")(record)

    def encrypt(self, record, raw_text):
        """
            encrypt raw contents to cipher contents,
            This method is not intended to be overridden

            @param record: current recordset
            @param raw_text: raw text to be encrypted
            @return: encrypted text
        """
        try:
            encrypt_method = self._get_field_method(record, "_encrypt")
            return encrypt_method(record, raw_text.encode("utf-8"))

        except UnicodeEncodeError:
            raise Warning(
                "Incorrect value format",
                "Value to be encrypted should not be in unicode format"
            )

    def decrypt(self, record, cipher_text):
        """
            decrypt cipher contents back to raw contents,
            This method is not intended to be overridden

            @param record: current recordset
            @param cipher_text: encrypted text to be decrypted
            @return: decrypted text
        """
        try:
            decrypt_method = self._get_field_method(record, "_decrypt")
            raw_contents = decrypt_method(record, cipher_text)

            # assume secret key is wrong if we can not decode raw text as UTF-8
            raw_contents.decode("utf-8")

            return raw_contents

        except UnicodeDecodeError:
            raise Warning(
                "Incorrect secret key",
                "The secret key used to decrypt the data is not correct."
            )
        except (ValueError, TypeError):
            raise Warning(
                "Incorrect format",
                "The value to be decrypted is not in a correct format"
            )

    def is_pwd_auth_required(self):
        """
            getter method to indicate password mode is enabled or not
        """
        return getattr(self, "_is_pwd_auth_required", True)

    def is_multiline_required(self):
        """
            getter method to indicate multiple line mode is enabled or not
        """
        return getattr(self, "_is_multiline_required", False)

    # ==================================================================
    # Helper methods to transform the value of field `self` of the record
    # to a specific correct display format - for consume purpose.
    # Overrides from BaseModel
    # ==================================================================

    def convert_to_cache(self, value, env, validate=True):
        if value:
            return value
        return ""

# ==========================================
# make a patch to current fields system (V8)
# ==========================================
setattr(fields, "Secure", Secure)
