# -*- coding: utf-8 -*-
{
    "name": 'web_button_enhanced',
    "category": 'Web',
    "version": "0.1",
    "description":"""
=====================================================================================
SUPPORT USING BUTTON WITH CUSTOM CSS CLASS
=====================================================================================

+ full example:

    <button name="button_name" type="object|action|workflow" icon="icon_name"
        string="buton_display_name" help="help_message_for_the_button" class="custom_css_class" />

+ This module is intended to allow user to use fontawesome on the button to have a nice button icon
instead of default icon from OpenERP, so there is no need to use `icon` attribute, use classes supported
`fontawesome` instead, as the example below:

    <button name="button_name" type="object|action|workflow"
        help="help_message_for_the_button" class="icon-...." />

    The `icon-` is the prefix used by `fontawesome` libraries and can be changed throughout versions.

+ Current supported fontawesome version 3.2.1:

    Link reference (github):
        http://fortawesome.github.io/Font-Awesome/3.2.1/icons

    Homepage:
        http://fontawesome.io
    """,
    "depends": [
        'base', 'web_unleashed_extra'
    ],
    'data': [
        'views/web_button_enhanced.xml'
    ],
    'qweb':[
        'static/src/xml/base.xml'
    ],
    "css": [
    ],
    "js": [
    ],
    "author": "Trobz",
    "installable" : True,
    "active" : False,
}