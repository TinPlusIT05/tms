from openerp.osv import osv

class res_users(osv.osv):
    _inherit = "res.users"

    def client_check_access_rights(self, cr, uid, model_name, operation, context=None):
        """
            allow to check access right from client script (user only 
            need to pass the "model_name" and "operation" to be checked
            @param {object} cr: database cursor
            @param {int}    uid: current logged-in user's id
            @param {string} model_name: the name of the model to be checked (example: "res.users")
            @param {string} operation: the opearation to check, can be in [create, read, write, unlink, export]
        """
        if context is None: context = {}
        return bool(self.pool.get('ir.model.access').client_check(cr, uid, model_name, operation))
    
res_users();
    
