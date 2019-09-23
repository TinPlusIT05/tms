# -*- coding: utf-8 -*-
{
    "name": "Drop Database hidden from UI",
    "version": "1.0",
    "author": "Trobz",
    "license": "AGPL-3",
    "category": "Hidden/Dependency",
    "summary": "Drop Database hidden from UI if current instance is Production",
    "description": "This module should be in the list of --load parameter when starting the server",
    "depends": [
        'web'
    ],
    "data": [
    ],
    "qweb": [
        'static/src/xml/*.xml',
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
    "external_dependencies": {
        'python': [],
    },
}
