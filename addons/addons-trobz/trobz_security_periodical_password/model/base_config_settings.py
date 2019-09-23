from openerp.osv import osv, fields


class base_config_settings(osv.TransientModel):
    _inherit = 'base.config.settings'

    _columns = {
        'update_password_type': fields.selection(
            [('specified_date', 'Only on Specified Date'),
             ('periodically', 'Periodically')],
            string='Update Password'),
        'update_password_date': fields.date(string='Update Password Date'),
        'update_password_period': fields.integer(string='Period (Months)'),
    }

    _defaults = {
        'update_password_type': 'specified_date'
    }

    def get_default_update_password_type(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        res = {
            'update_password_type': icp.get_param(
                cr, uid, 'config_update_password_type'),
            'update_password_date': icp.get_param(
                cr, uid, 'config_update_password_date'),
            'update_password_period': eval(icp.get_param(
                cr, uid, 'config_update_password_period'))
        }
        return res

    def set_update_password_type(self, cr, uid, ids, context=None):

        config = self.browse(cr, uid, ids[0], context=context)
        icp = self.pool.get('ir.config_parameter')

        icp.set_param(
            cr, uid, 'config_update_password_type',
            config.update_password_type)
        icp.set_param(
            cr, uid, 'config_update_password_date',
            config.update_password_date)
        icp.set_param(
            cr, uid, 'config_update_password_period',
            config.update_password_period)
