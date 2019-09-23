# -*- coding: utf-8 -*-
##############################################################################
from openerp.osv import osv
from openerp.tools.translate import _


def str2tuple(s):
    return eval('tuple(%s)' % (s or ''))


class ir_cron(osv.Model):
    _inherit = "ir.cron"

    def btn_run_schedule(self, cr, uid, ids, context=None):
        for scheduler in self.browse(cr, uid, ids, context):
            args = str2tuple(scheduler.args)
            model = self.pool[scheduler.model]
            if model and hasattr(model, scheduler.function):
                method = getattr(model, scheduler.function)
                method(cr, uid, *args)
            else:
                raise osv.except_osv(_('Error'), _('Could not find the method\
                    %s in the model %s.') % (scheduler.function, model))
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
