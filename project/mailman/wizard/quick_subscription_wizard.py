# -*- coding: utf-8 -*-
from openerp import models, fields, api


class quick_subscription_wizard(models.TransientModel):
    _name = "quick.subscription.wizard"

    email_list = fields.Text(string="Input email addresses", required=True)
    result = fields.Text(readonly=True)

    @api.multi
    def button_add_subscribers(self):
        list = self._context.get('email_list')
        mailman_env = self.env['mailman.list']
        partner_env = self.env['res.partner']

        email_list = list.splitlines()

        new_subscribers = []
        unknown_emails = []
        count_success = 0
        rs = []
        context = self._context
        for email in email_list:
            if not email:
                continue

            partners = partner_env.search([('email', '=', email)], limit=1)

            if partners:
                new_subscribers.append((4, partners[0].id, 0))
                count_success += 1
            else:
                unknown_emails.append(u'<li>{0}</li>'.format(email))
        if context.get('active_model') == 'mailman.list':
            mailman_objs = mailman_env.search(
                [('id', 'in', context['active_ids'])])
            mailman_objs.write({'subscriber_ids': new_subscribers})

        if count_success > 0:
            rs.append(
                u"""<ul class="list_type"><li>%s partner(s) added successfully
                </li></ul>""" % count_success)
        if unknown_emails:
            recommended = "{0}".format(
                ''.join(unknown_emails)
            )
            rs.append(
                u"""
                <ul class="list_type"><li>
                    <span>{0} unrecognized email address(es); </span>
                    <span>create a partner with this email address first</span>
                    <ul>{1}</ul>
                </ul>
                """.format(len(unknown_emails), recommended)
            )

        result = '\n'.join(rs)
        self.write({'result': result})

        # Return result wizard
        models_data = self.env['ir.model.data']
        form_view = models_data.get_object_reference(
            'mailman', 'quick_subscription_rs_wizard_form')

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'quick.subscription.wizard',
            'view_id': form_view and form_view[1] or False,
            'target': 'new',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
        }
