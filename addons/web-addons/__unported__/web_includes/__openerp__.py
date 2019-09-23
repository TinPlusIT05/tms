# -*- coding: utf-8 -*-
{
    'name': 'Trobz Web Includes',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
Change OpenERP web behavior

+ change default options for WYSIWYG cleditor 
+ enhanced progress bar
+ add document.pages with a colorbox on views ???
+ add crash report on form view ???

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
        'static/lib/colorbox/colorbox.css',
        
        'static/src/css/progress_bar_enhanced.css',
    ],
       
    'js': [
        # lib
        'static/lib/colorbox/jquery.colorbox-min.js',
        
        # collections
        'static/src/js/collections/document_pages.js',
        
        # includes
        'static/src/js/cleditor_text_html.js',
        'static/src/js/progress_bar_enhanced.js',
        'static/src/js/view_document_page.js',
        'static/src/js/form_view_crash.js'
    ],
    
    'test': [
    ]
}