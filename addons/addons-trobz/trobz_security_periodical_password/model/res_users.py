from openerp.osv import osv, fields


class res_users(osv.Model):

    _inherit = "res.users"

    _columns = {
        'last_password_update': fields.date(string="Last password update",
                                            required=True)
    }

    _defaults = {
        'last_password_update': fields.date.context_today,
    }

    def change_password(self, cr, uid, old_passwd, new_passwd, context=None):
        self.write(
            cr, uid, uid, {'last_password_update': fields.date.today()},
            context=context)
        return super(res_users, self).change_password(
            cr, uid, old_passwd, new_passwd, context=context)

res_users()
