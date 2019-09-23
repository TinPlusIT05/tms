# -*- coding: utf-8 -*-

# update HTTP Password Bcrypt Hashed for all users

import erppeek
import sys
import bcrypt

client = erppeek.Client.from_config(sys.argv[1])

users = client.model('res.users').browse([("is_trobz_member", "=", True)])

if users:
    print "========== UPDATE HTTP PASSWORD BCRYPT HASHED =========="
    print 'Total Users: %s' % len(users)
    for user in users:
        https_password = client.execute('res.users',
                                        'read_secure', user.id,
                                        ['https_password'])[0].get(
            'https_password')
        if https_password:
            password_bcrypt_hash = bcrypt.hashpw(https_password,
                                                 bcrypt.gensalt())
            if password_bcrypt_hash:
                password_bcrypt_hash.encode("utf-8")
                res = user.write(
                    {'https_password_bcrypt_hashed': password_bcrypt_hash})
                if res:
                    print 'Update user with id', user.id, 'success'
    print "========= UPDATE HTTP PASSWORD BCRYPT HASHED ==========="
    print "===================== DONE ============================="
