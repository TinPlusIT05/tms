# -*- coding: utf-8 -*-

from openerp.osv import fields, osv


class hr_department(osv.osv):
    _inherit = 'hr.department'

    def get_departments(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for dept in self.browse(cr, uid, ids, context=context):
            root_department_id = False
            team_id = False
            sub_team_id = False
            if dept:
                if not dept.parent_id:
                    root_department_id = dept.id
                else:
                    if not dept.parent_id.parent_id:
                        root_department_id = dept.parent_id.id
                        team_id = dept.id
                    else:
                        root_department_id = dept.parent_id.parent_id.id
                        team_id = dept.parent_id.id
                        sub_team_id = dept.id
            res[dept.id] = {
                'root_department_id': root_department_id,
                'team_id': team_id,
                'sub_team_id': sub_team_id,
            }
        return res

    def get_department_ids_change(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        hr_department_pool = self.pool['hr.department']
        hr_department_ids = hr_department_pool.search(
            cr, uid, ['|', ('id', 'in', ids), ('parent_id', 'in', ids)]
        )
        return hr_department_ids

    _columns = {
        'root_department_id': fields.function(
            get_departments, string='Root Department',
            track_visibility='onchange',
            type='many2one', method='True',
            store={
                'hr.department': (lambda self, cr, uid, ids, c={}: ids,
                                  ['name'], 10),
                'hr.department': (get_department_ids_change, ['parent_id'], 10)
            },
            relation="hr.department", multi='get_department_root'
        ),
        'team_id': fields.function(
            get_departments, string='Team',
            track_visibility='onchange',
            type='many2one', method='True',
            store={
                'hr.department': (lambda self, cr, uid, ids, c={}: ids,
                                  ['name'], 10),
                'hr.department': (get_department_ids_change,
                                  ['parent_id'], 10)
            },
            relation="hr.department", multi='get_department_root'
        ),
        'sub_team_id': fields.function(
            get_departments, string='Sub-team',
            track_visibility='onchange',
            type='many2one', method='True',
            store={
                'hr.department': (lambda self, cr, uid, ids, c={}: ids,
                                  ['name'], 10),
                'hr.department': (get_department_ids_change,
                                  ['parent_id'], 10)
            },
            relation="hr.department", multi='get_department_root'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
