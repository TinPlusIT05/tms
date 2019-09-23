# -*- coding: utf-8 -*-
from openerp import models, api
from openerp.exceptions import Warning
from openerp.tools.translate import _


class HrApplicant(models.Model):
    _inherit = "hr.applicant"

    @api.cr_uid_ids_context
    def create_employee_from_applicant(self, cr, uid, ids, context=None):
            """ Create an hr.employee from the hr.applicants """
            if context is None:
                context = {}
            hr_employee = self.pool.get('hr.employee')
            model_data = self.pool.get('ir.model.data')
            act_window = self.pool.get('ir.actions.act_window')
            res_partner = self.pool.get('res.partner')
            hr_job = self.pool.get('hr.job')
            # Get broadcast_message value from ir.config_parameter
            config_parameter = self.pool.get('ir.config_parameter')
            mail_broadcast = \
                eval(config_parameter.get_param(cr, uid, 'mail_broadcast',
                     default=False, context=context))

            emp_id = False
            for applicant in self.browse(cr, uid, ids, context=context):
                address_id = contact_name = False
                if applicant.partner_id:
                    address_id = \
                        res_partner.address_get(cr, uid,
                                                [applicant.partner_id.id],
                                                ['contact'])['contact']
                    contact_name = \
                        res_partner.name_get(cr, uid,
                                             [applicant.partner_id.id])[0][1]
                if applicant.job_id and \
                   (applicant.partner_name or contact_name):
                    applicant.job_id.write(
                        {'no_of_hired_employee':
                         applicant.job_id.no_of_hired_employee + 1})
                    create_ctx = dict(context, mail_broadcast=mail_broadcast)
                    emp_id = hr_employee.create(
                        cr, uid, {'name':
                                  applicant.partner_name or contact_name,
                                  'job_id': applicant.job_id.id,
                                  'address_home_id': address_id,
                                  'applicant_id': applicant.id or False,
                                  'department_id':
                                  applicant.department_id.id or False,
                                  'address_id': applicant.company_id and
                                  applicant.company_id.partner_id and
                                  applicant.company_id.partner_id.id or False,
                                  'work_email': applicant.department_id and
                                  applicant.department_id.company_id and
                                  applicant.department_id.company_id.email or
                                  False,
                                  'work_phone': applicant.department_id and
                                  applicant.department_id.company_id and
                                  applicant.department_id.company_id.phone or
                                  False,
                                  }, context=create_ctx)
                    self.write(cr, uid, [applicant.id],
                               {'emp_id': emp_id},
                               context=context)
                    hr_job.message_post(
                        cr, uid, [applicant.job_id.id],
                        body=_('New Employee %s Hired') %
                        applicant.partner_name
                        if applicant.partner_name else applicant.name,
                        subtype="hr_recruitment.mt_job_applicant_hired",
                        context=context)
                else:
                    raise Warning(
                            _('Warning !'),
                            _('You must define an Applied Job and ' +
                              'a Contact Name for this applicant.'))
            action_model, action_id = \
                model_data.get_object_reference(
                    cr, uid, 'hr', 'open_view_employee_list')
            dict_act_window = act_window.read(cr, uid, [action_id], [])[0]
            if emp_id:
                dict_act_window['res_id'] = emp_id
            dict_act_window['view_mode'] = 'form,tree'
            return dict_act_window
