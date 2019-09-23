from openerp.osv import osv

class trobz_base(osv.osv_abstract):
    _inherit = "trobz.base"
    
    def extra_permission_hook(self, cr, uid, vals, permissions, context=None):
        if context is None: context = {}
        perm_export = permissions[4] if (len(permissions) > 4) else 1
        vals.update({
            "perm_export": perm_export
        })
        return vals

trobz_base()
