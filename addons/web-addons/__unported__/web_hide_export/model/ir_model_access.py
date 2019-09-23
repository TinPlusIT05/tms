import logging
from openerp import tools
from openerp.osv import osv, fields
from openerp.osv.orm import browse_record

_logger = logging.getLogger(__name__)

class ir_model_access(osv.osv):
    _inherit = "ir.model.access"

    _columns = {
        "perm_export": fields.boolean("Export Access")
    }

    _defaults = {
        "perm_export": lambda self, *args, **kwargs: True
    }
    
    @tools.ormcache()
    def client_check(self, cr, uid, model, mode='read', context=None):
        if uid==1:
            # User root have all accesses
            # TODO: exclude xml-rpc requests
            return True

        if isinstance(model, browse_record):
            assert model._table_name == 'ir.model', 'Invalid model object'
            model_name = model.model
        else:
            model_name = model

        # TransientModel records have no access rights, only an implicit access rule
        if not self.pool.get(model_name):
            _logger.error('Missing model %s' % (model_name, ))
        elif self.pool.get(model_name).is_transient():
            return True

        # We check if a specific rule exists
        cr.execute('SELECT MAX(CASE WHEN perm_' + mode + ' THEN 1 ELSE 0 END) '
                   '  FROM ir_model_access a '
                   '  JOIN ir_model m ON (m.id = a.model_id) '
                   '  JOIN res_groups_users_rel gu ON (gu.gid = a.group_id) '
                   ' WHERE m.model = %s '
                   '   AND gu.uid = %s '
                   '   AND a.active IS True '
                   , (model_name, uid,)
                   )
        r = cr.fetchone()[0]

        if r is None:
            # there is no specific rule. We check the generic rule
            cr.execute('SELECT MAX(CASE WHEN perm_' + mode + ' THEN 1 ELSE 0 END) '
                       '  FROM ir_model_access a '
                       '  JOIN ir_model m ON (m.id = a.model_id) '
                       ' WHERE a.group_id IS NULL '
                       '   AND m.model = %s '
                       '   AND a.active IS True '
                       , (model_name,)
                       )
            r = cr.fetchone()[0]
        return r or False

ir_model_access()