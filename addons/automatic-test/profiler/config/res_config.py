# -*- coding: utf-8 -*-

from openerp.osv import osv, fields
from openerp.tools.safe_eval import safe_eval

class base_config_settings(osv.TransientModel):
    _inherit = 'base.config.settings'

    _columns = {
        'profiler_enabled': fields.boolean('Enable Profiler',
            help="""Enable the model profiler, see profiler module description."""),
        'profiler_csv_file': fields.char('Profiler CSV path',
            help="Profiler output CSV path"),
    }

    def get_default_profiler_enabled(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {
            'profiler_enabled': safe_eval(icp.get_param(cr, uid, 'profiler.enabled', 'False')),
            'profiler_csv_file': icp.get_param(cr, uid, 'profiler.csv_file', '')
        }

    def set_profiler_enabled(self, cr, uid, ids, context=None):
        
        config = self.browse(cr, uid, ids[0], context=context)
        icp = self.pool.get('ir.config_parameter')
        
        icp.set_param(cr, uid, 'profiler.enabled', repr(config.profiler_enabled))
        icp.set_param(cr, uid, 'profiler.csv_file', config.profiler_csv_file)

        from openerp.addons.profiler.profilers.tracker import tracker

        if config.profiler_enabled:
            tracker.enable()
        else:
            tracker.disable()


base_config_settings()