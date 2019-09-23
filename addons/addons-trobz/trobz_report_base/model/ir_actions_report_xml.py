# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import fields, osv
from openerp.tools.safe_eval import safe_eval

class ir_action_report_xml(osv.osv):
    _inherit ="ir.actions.report.xml"

    _columns={
        'test_record_ids' : fields.one2many('test.report.record', 'report_id', 'Records'),
        'params': fields.text('Parameters', help="Input the parameter follow dictionary format")
    }
    
    def print_test_report(self, cr, uid, ids, context={}):
        context = context or {}
        obj = self.browse(cr, uid, ids[0], context=context)
        print_ids = []
        if obj.test_record_ids:
            for record in obj.test_record_ids:
                print_ids.append(record.res_id)
            context['active_ids'] = print_ids
            context['active_id'] = print_ids[0]
        context['active_model'] = obj.model
        data = {'model':obj.model, 'ids':print_ids, 'id':print_ids and print_ids[0], 'report_type': 'aeroo'}
        if obj.params:
            try:
                data['form'] = safe_eval(obj.params)
            except:
                raise osv.except_osv(_('Warning'), _("Parameters field is wrong format!"))
                
        return {
            'type': 'ir.actions.report.xml',
            'report_name': obj.report_name,
            'datas': data,
            'context':context
        }
