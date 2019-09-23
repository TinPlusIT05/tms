# -*- coding: utf-8 -*-
from openerp import fields, api, models
from datetime import datetime


class ManageDeadlineSpTicketWizard(models.TransientModel):
    _name = "manage.deadline.sp.ticket.wizard"

    comments = fields.Text(string='Comments')
    deadline = fields.Date(
        "Deadline")

    @api.multi
    def button_assign(self):
        self.ensure_one()
        context = self._context
        active_model = context.get('active_model', False)
        active_id = context.get('active_id', False)
        default_trobz_supporter_for_project = context.get(
            'default_trobz_supporter_for_project', False)
        deadline = self.deadline
        if active_model and active_id:
            active_record = self.env[active_model].browse(active_id)
            comment = ("%s" + "\n" + "Deadline: %s") % (
                self.comments, deadline)
            self.env['tms.ticket.comment'].create({
                'name': datetime.now(),
                'comment': comment,
                'author_id': self._uid,
                'tms_support_ticket_id': active_id
            })
            if deadline:
                active_record.write({'deadline': deadline})
            if default_trobz_supporter_for_project:
                active_record.write(
                    {'owner_id': default_trobz_supporter_for_project,
                     'state': 'assigned'})
            else:
                users_pool = self.env['res.users']
                data_pool = self.env['ir.model.data']
                user_login = data_pool.get_object(
                    "tms_modules", "trobz_default_project_supporter_login"
                ).value
                users = users_pool.search(
                    [('login', '=', user_login)]
                )
                if users:
                    active_record.write(
                        {'owner_id': users[0].id,
                         'state': 'assigned'})
                else:
                    raise Warning(
                        "Warning!",
                        "No default project supporter"
                        "configuration found on system"
                    )
        return True
