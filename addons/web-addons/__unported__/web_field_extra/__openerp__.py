# -*- coding: utf-8 -*-
{
    'name': 'Trobz Web Extra Fields',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Add extra fields for form view.

- date_us: display a datepicker in US format
- barcode: commit on keyup event ?
- TabCharWidget: ??
- image_viewer: display image in a lightbox
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'web_unleashed'
    ],
    
    'data': [
    ],
    
    'qweb' : [
    ],
    
    
    'css' : [
        'static/lib/lightbox/css/lightbox.css',
        
        'static/src/css/image_viewer.css',
    ],
       
    'js': [
        'static/lib/lightbox/js/lightbox.js',
           
        'static/src/js/field_barcode.js',
        'static/src/js/field_date_us.js',
        'static/src/js/field_lightbox_image.js',
        'static/src/js/field_tab_char.js',
    ],
    
    'test': [
    ]
}