#!/usr/bin/env python
# -*- coding: utf-8 -*-

{
    "name": "Trobz HR Employee Image",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    'description': """
Trobz HR Employee Image Store Image:

    - All Employee's Images will be store on the file system by default and not in the database.
    - The default Storage class will store the field on the file system and build the path like that
    - HR Employee:
        + Field image_medium

BASE_LOCATION/DB_NAME/MODEL-FIELD/XX/YYYYY

with
    - BASE_LOCATION: the base location configured in ir.config_parameter
    - DB_NAME:  your database name
    - MODEL-FIELD: the concatenation of the name of the model with the name of the
    field, for example 'product.product-image'
    - XX: the first 2 letter of the file name build with their sha1 hash
    - YYYYYY: file name build with their sha1 hash
    """,
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'depends': [
        'hr',
        'binary_field',
    ],
    'init_xml': [],
    'data': [
        'data/post_object_functions_data.xml',
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: