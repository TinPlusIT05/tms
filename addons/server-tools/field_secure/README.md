# 1. Documentation & Requirements:

- http://www.di-mgt.com.au/cryptopad.html#whatispadding
- http://www.codekoala.com/posts/aes-encryption-python-using-pycrypto
- https://www.dlitz.net/software/pycrypto/api/current/Crypto.Cipher.AES-module.html
- http://security.stackexchange.com/questions/52665/which-is-the-best-cipher-mode-and-padding-mode-for-aes-encryption

To use this module, please make sure the following libraries is installed on the host machine:

- `PyCrypto` is the main package provides encryption methods such as AES...

```sh
sudo pip install pycrypto
```

# 2. Example:

1. create new model which inherits from `SecureModel`
2. create new field with type `Secure`
3. override some function to work with secure field (in parameters)

    1. `security`: 
        - Define how this field should be restricted to some people.
        - Override this function to define custom security check.
        - Return boolean value (True, False).
    2. `secret_key`: 
        - Define how to get the contents of the key.
        - Default implementation of this function is to take value from the configuration file 
        (through the --config parameter when calling openerp-server) with name "field_secure_secret_key"
        - Override this function to provide custom secret key, new secret key should be considered as specified in **3. Notice** part.
        - Return contents of the key (string value).
    3. `encrypt`:
        - Define how value of the field should be encrypted.
        - Default implementation of this function is to be used in-combination with `secret_key` to encrypt the raw contents to cipher contents.
        - This function is not intended to be overriden except that you want to use another algorithm to encrypt the contents instead of AES.
        - Return encrypted contents (cipher contents).
    4. `decrypt`:
        - Define how value of the field should be decrypted.
        - Default implementation of this function is the same as `encrypt` but used to decrypt the cipher contents back to raw contents using `secret_key`
        - This function is not intended to be overriden, the same purpose as `encrypt`.
        - return decrypted contents (raw contents).
    5. `multiline`:
        - Define how secure field is displayed when user change value,  possible value would be True or False (bool type)
            - `True`: secure field will be displayed as an textarea.
            - `False`: secure field will be displayed as an input.
        - default value for this option is `False`.
    6. `password`:
        - Define how secure field is used, possible value would be True or False (bool type)
            - `True`: 
                - User need to input password in a popup to check for authorization, viewing or updating contents of secure field will be done on this popup.
                - In Create mode, it's **unable** to set contents for secure field by open popup as it's done with View mode or Edit mode, it's only available after record is created.
            - `False`:
                - User does not need to input password to check for authorization.
                - Any action like Viewing / Inputing / Changing contents of secure field directly on Form view or List view (with editable mode enabled).
        - Default value of this option is `True`.

FULL EXAMPLE:

```python

    from openerp import fields
    from openerp.addons.field_secure import models
    
    # inherit your model from SecureModel provided by the module
    class users(models.SecureModel):

        _name = "users"
    
        # define Secure field
        user_password: fields.Secure(
            string="Password",
            security="_secure_user_password_security",
            secret_key="_secure_user_password_secret_key",

            # use these below only when you want to 
            # handle encryption/decryption by yourself
            encrypt="_secure_user_password_encrypt",
            decrypt="_secure_user_password_decrypt",

            # user does not need to enter password
            password=True,

            # should display input box
            multiline=False
        )
    
        def _secure_user_password_security(self):
            # define how this field should be restricted to some people
            # receive `self` parameter as recordset
            return True|False
            
        def _secure_user_password_secret_key(self):
            # get the secret key
            # receive `self` parameter as recordset
            secret_key = ..........
            return secret_key
            
        def _secure_user_password_encrypt(self, raw):
            # encrypt raw contents to cipher contents
            # receive `self` parameter as recordset
            encypted_contents = ..........
            return encypted_contents
            
        def _secure_user_password_decrypt(self, cipher):
            # decrypt cipher contents back to raw contents
            # receive `self` parameter as recordset
            decrypted_contents = ..........
            return decrypted_contents
```

# 3. Notice:

- The key used in AES algorithm should be in 32 bytes length string and should be the same as `block size` of AES.

- There are ways to generate this automatically as below:
    - Using CLI:
    
        ```sh
        dd if=/dev/urandom bs=16 count=1 2>/dev/null | md5sum | cut -d' ' -f1
        ```

    - Using Python:

        ```python
        import os
        os.urandom(32)
        ```

# 4. Installation:

- This module can be installed as normal and should be loaded when starting openerp-server
- Please put this module in the list of `--load` parameter when starting openerp-server
