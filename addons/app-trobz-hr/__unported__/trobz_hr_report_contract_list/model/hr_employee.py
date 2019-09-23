# -*- encoding: utf-8 -*-

from openerp.osv import fields, osv


class hr_employee(osv.osv):
    _inherit = 'hr.employee'

    def get_departments(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for current_employee in self.browse(cr, uid, ids, context=context):
            root_department_id = False
            team_id = False
            sub_team_id = False
            department = current_employee.department_id
            if department:
                if not department.parent_id:
                    root_department_id = department.id
                else:
                    if not department.parent_id.parent_id:
                        root_department_id = department.parent_id.id
                        team_id = department.id
                    else:
                        root_department_id = department.parent_id.parent_id.id
                        team_id = department.parent_id.id
                        sub_team_id = department.id

            res[current_employee.id] = {
                'root_department_id': root_department_id,
                'team_id': team_id,
                'sub_team_id': sub_team_id,
            }
        return res

    def get_employee_ids_from_department_id(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        hr_employee_pool = self.pool.get('hr.employee')
        hr_department_pool = self.pool['hr.department']

        hr_department_ids = hr_department_pool.search(
            cr, uid, ['|', ('id', 'in', ids), ('parent_id', 'in', ids)]
        )
        employee_ids = hr_employee_pool.search(
            cr, uid, [('department_id', 'in', hr_department_ids)]
        )
        return employee_ids

    _columns = {
        'root_department_id': fields.function(
            get_departments, string='Root Department',
            track_visibility='onchange',
            type='many2one', method='True',
            store={'hr.employee': (lambda self, cr, uid, ids, c={}: ids,
                                   ['department_id'], 10),
                   'hr.department': (get_employee_ids_from_department_id,
                                     ['parent_id'], 10)},
            relation="hr.department", multi='get_department_root'
        ),

        'team_id': fields.function(
            get_departments, string='Team',
            track_visibility='onchange',
            type='many2one', method='True',
            store={'hr.employee': (lambda self, cr, uid, ids, c={}: ids,
                                    ['department_id'], 10),
                   'hr.department': (get_employee_ids_from_department_id,
                                     ['parent_id'], 10)
                   },
            relation="hr.department", multi='get_department_root'
        ),

        'sub_team_id': fields.function(
            get_departments, string='Sub-team',
            track_visibility='onchange',
            type='many2one', method='True',
            store={'hr.employee': (lambda self, cr, uid, ids, c={}: ids,
                                   ['department_id'], 10),
                   'hr.department': (get_employee_ids_from_department_id,
                                     ['parent_id'], 10)
                   },
            relation="hr.department", multi='get_department_root'
        ),
    }
