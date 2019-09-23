# -*- coding: utf-8 -*-
{
    "name": "Remote IDE debugging",
    "version": "1.0",
    "author": "Trobz",
    "complexity": "normal",
    "description": """
    Allow remote debugging with IDE like Eclipse or PyCharm

    Add an extra option to openerp-server:
    --remote-debug=[IP:port]

    defaults:
    - IP: the IP from the host inside a container (presuming docker image is
    used)
    - port: 5678

    The addon has to be loaded as server-wide module.
    """,
    "category": "Tools",
    "depends": [
    ],
    "data": [
    ],
    "js": [
    ],
    "css": [
    ],
    "auto_install": False,
    "installable": True,
    "external_dependencies": {
        'python': [ 'pydevd' ],
    },
}
