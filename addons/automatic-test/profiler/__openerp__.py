# -*- coding: utf-8 -*-
{
    'name': 'Profiling Tool',
    'version': '1',
    'category': 'Debug',
    'description': """
Add OpenERP model profiling facilities, enable model method tracking.


in `General Parameters`:

- enable profiling feature
- set the csv path


usage:

::

from openerp.addons.profiler.profilers.tracker import tracker

# track mrp.production
tracker.model('mrp.production', [
    'action_confirm',
    'button_confirm_merge',
    'write',
], {'object_name': True, 'arguments': True})


Options:

- object_name: resolve `ids` parameter by adding object names in the CSV file (object name column)
- arguments: add custom parameters to the CSV file (arguments column)

Note:

- the CSV file include profiling data automatically recorded at each call on these methods.
- the CSV file will be truncated at every server restart
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'base_setup'
    ],
    'data' : [
         # default configuration
        'config/ir_config_parameter_default.xml',

        # extend general settings
        'config/res_config.xml',
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'active': False,
    'application': True,

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
