# -*- coding: utf-8 -*-
from datetime import date
from openerp import fields, api, _
from openerp.exceptions import Warning
from openerp.addons.booking_chart.mixin import mixin  # @UnresolvedImport


class HrDedicatedResourceContract(mixin.resource):

    """
    Dedicated Resource Contract
    """
    _name = 'hr.dedicated.resource.contract'
    _description = 'Dedicated Resource Contract'
    _order = 'start_date,end_date'

    name = fields.Many2one(
        'res.partner', string="Dedicated To Partner", required=True)
    start_date = fields.Date("Start Date", required=True)
    end_date = fields.Date('End Date')
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True)
    comment = fields.Text('Comment')

    @api.constrains('start_date', 'end_date', 'employee_id')
    def _check_overlap_date(self):
        """
        Overlapping Dedicated Resource Contract
        """
        for contract in self.read(['employee_id', 'start_date', 'end_date']):
            overlap_ids = []
            if contract['end_date']:
                overlap_ids = self.search(
                    [('employee_id', '=', contract['employee_id'][0]),
                     ('id', 'not in', self._ids),
                     ('start_date', '<=', contract['end_date']),
                     "|", ('end_date', '>=', contract['start_date']),
                     ('end_date', '=', False)],)
            else:
                overlap_ids = self.search(
                    [('employee_id', '=', contract['employee_id'][0]),
                     ('id', 'not in', self._ids),
                     "|", ('end_date', '>=', contract['start_date']),
                     ('end_date', '=', False)],)

            if overlap_ids:
                raise Warning(_("""Overlapping Dedicated Resource Contract:
                This employee is already associated to a
                Dedicated Resource Contract during this period."""))
        return True

    def _get_name(self, resource):
        """
        """
        dedicated_to_partner = resource.name and resource.name.name
        start_date = resource.start_date
        end_date = resource.end_date or ''
        name = '[Dedicated To Partner: %s] %s' % (dedicated_to_partner,
                                                  start_date)
        name = end_date and '%s - %s' % (name, end_date) or name
        return name

    def _get_hr_employee_id(self, resource_allocation):
        return 'hr.employee,%s' % resource_allocation.employee_id.id

    def _get_description(self, resource):
        """
        """
        return resource.comment

    def _get_color(self, resource):
        color = 'blue'
        if not resource.end_date:
            color = 'green'
        return color

    def _get_end_date(self, resource):
        res = resource.end_date
        if not resource.end_date:
            res = str(date(2020, 1, 1))
        return res

    _booking_chart_mapping = {
        'tms_modules.dedicated_resource_contract_chart': {
            'name': _get_name,
            'resource_ref': _get_hr_employee_id,
            'origin_ref': 'id',
            'message': _get_description,
            'date_start': 'start_date',
            'date_end': _get_end_date,
            'css_class': _get_color,

        }
    }
