from openerp import SUPERUSER_ID
from openerp.osv import fields


# monkey patch to get "get" method back for many2one field
def get(self, cr, obj, ids, name, user=None, context=None, values=None):
    if context is None:
        context = {}
    if values is None:
        values = {}

    res = {}
    for r in values:
        res[r['id']] = r[name]
    for iid in ids:
        res.setdefault(iid, '')
    obj = obj.pool.get(self._obj)

    # build a dictionary of the form {'id_of_distant_resource':
    # name_of_distant_resource}
    # we use uid=1 because the visibility
    # of a many2one field value (just id and name)
    # must be the access right of the parent form and
    # not the linked object itself.
    records = dict(obj.name_get(
        cr, SUPERUSER_ID,
        list(set([x for x in res.values()
                  if x and isinstance(x, (int, long))])), context=context))
    for iid in res:
        if res[iid] in records:
            res[iid] = (res[iid], records[res[iid]])
        else:
            res[iid] = False
    return res


fields.many2one.get = get
