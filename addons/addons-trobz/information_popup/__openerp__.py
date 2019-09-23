# -*- coding: utf-8 -*-

{
    'name': 'Information Popup',
    'version': '1.0',
    'description': """
Define Popup Dialog
===================
Return a Popup Dialog without rollback data when you press a button.
- How to use:
    - Return self.env['information.popup'].warning('Your Title', 'Your Warning Message') in your button.
    """,
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'depends': [
    ],
    'data': [
        # View
        'information_popup_view.xml',
    ],
    'installable': True,
    'active': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
