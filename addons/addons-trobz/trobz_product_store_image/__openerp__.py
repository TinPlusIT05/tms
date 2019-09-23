# -*- coding: utf-8 -*-

{
    'name': 'Trobz Product Store Image',
    'version': '1.0',
    'category': 'Trobz',
    'description': """
Trobz Product Store Image:

    - All Product's Images will be store on the file system by default and not in the database.
    - The default Storage class will store the field on the file system and build the path like that
    - Product Template:
        - Field image_medium
        - Field image_small
    - Product Product
        - Field image_medium
        - Field image_small
        - Field image_variant
        
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
        'binary_field',
        'product'
    ],
    'init_xml': [],
    'data': [
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
