# -*- coding: utf-8 -*-

from openerp.osv import fields, osv


class hr_contract(osv.osv):
    _inherit = 'hr.contract'

    def get_departments(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for current_contract in self.browse(cr, uid, ids, context=context):
            root_department_id = False
            team_id = False
            sub_team_id = False
            if current_contract.employee_id \
               and current_contract.employee_id.department_id:
                department = current_contract.employee_id.department_id
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
            res[current_contract.id] = {
                'root_department_id': root_department_id,
                'team_id': team_id,
                'sub_team_id': sub_team_id,
            }
        return res

    def get_contract_ids_from_department_id(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        hr_department_ids = self.search(
            cr, uid, ['|', ('id', 'in', ids), ('parent_id', 'in', ids)]
        )
        employee_ids = self.pool['hr.employee'].search(
            cr, uid, [('department_id', 'in', hr_department_ids)]
        )
        contract_ids = self.pool['hr.contract'].search(
            cr, uid, [('employee_id', 'in', employee_ids)], context=context
        )
        return contract_ids

    def get_contract_ids_from_employee_id(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        contract_ids = self.pool['hr.contract'].search(
            cr, uid, [('employee_id', 'in', ids)], context=context
        )
        return contract_ids

    _columns = {
        'root_department_id': fields.function(
            get_departments, string='Root Department',
            track_visibility='onchange',
            type='many2one', method='True',
            store={
                'hr.contract': (lambda self, cr, uid, ids, c=None: ids,
                                ['employee_id'], 10),
                'hr.department': (get_contract_ids_from_department_id,
                                  ['parent_id'], 11),
                'hr.employee': (get_contract_ids_from_employee_id,
                                ['department_id'], 12)
            },
            relation="hr.department", multi='get_department_root'
        ),

        'team_id': fields.function(
            get_departments, string='Team', track_visibility='onchange',
            type='many2one', method='True',
            store={
                'hr.contract': (lambda self, cr, uid, ids, c=None: ids,
                                ['employee_id'], 10),
                'hr.department': (get_contract_ids_from_department_id,
                                  ['parent_id'], 11),
                'hr.employee': (get_contract_ids_from_employee_id,
                                ['department_id'], 12)
            },
            relation="hr.department", multi='get_department_root'
        ),
        'sub_team_id': fields.function(
            get_departments, string='Sub-team', track_visibility='onchange',
            type='many2one', method='True',
            store={
                'hr.contract': (lambda self, cr, uid, ids, c=None: ids,
                                ['employee_id'], 10),
                'hr.department': (get_contract_ids_from_department_id,
                                  ['parent_id'], 11),
                'hr.employee': (get_contract_ids_from_employee_id,
                                ['department_id'], 12)
            },
            relation="hr.department", multi='get_department_root'
        ),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
