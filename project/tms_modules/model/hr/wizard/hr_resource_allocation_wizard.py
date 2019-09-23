# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import Warning


class hr_resource_allocation_wizard(models.TransientModel):
    _name = 'hr.resource.allocation.wizard'
    _description = 'Create Resource Allocation for x more sprints'

    number_of_sprint = fields.Integer(
        'Number of Sprint', required=True,
        help="The user input the number of sprint for"
        " which he wants to add new Resource Allocation")

    @api.multi
    def create_resource_allocation(self):
        """
        Button create resource allocation for x more sprints
        """
        context = self._context
        res_ids = context.get('active_ids', False)
        res_allo_obj = self.env['hr.resource.allocation']
        for record in self:
            if record.number_of_sprint <= 0:
                return True
            resources = res_allo_obj.browse(res_ids)
            for resource in resources:
                if not resource.sprint:
                    raise Warning(
                        "There is no sprint linked to the current"
                        " resource allocation. Please select a sprint"
                        " before extending.")
                list_sprint = res_allo_obj.get_sprint(
                    resource.sprint, record.number_of_sprint)
                for sprint in list_sprint:
                    vals = {'employee_id': resource.employee_id.id,
                            'activity_id': resource.activity_id.id,
                            'sprint': sprint}
                    res_allo_obj.create(vals)
        return True
