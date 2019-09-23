# -*- coding: utf-8 -*-
##############################################################################
import time

from openerp import api, models, fields


class trobz_maintenance_connection(models.Model):
    _name = 'trobz.maintenance.connection'

    delay = fields.Integer('Delays')

    @api.multi
    def test_connection(self):
        time.sleep(self.delay)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
