# -*- encoding: utf-8 -*-
from openerp import models, fields, api
# @UnresolvedImport
from openerp.addons.mailman.lib.mailman import MailmanClient


class mailman_list(models.Model):

    """
        Vocabulary:
            - Subscribers: a res.partner, on odoo side
            - Member: an email of a mailing list, on mailman side
    """

    _name = "mailman.list"
    _order = "name"
    _description = "Mailman Mailing List"

    @api.model
    def _get_mailman(self):
        conf_env = self.env['ir.config_parameter']
        url = conf_env.get_param('mailman-api-url')
        timeout = conf_env.get_param('request-timeout')
        if not timeout:
            timeout = 120

        if not url:
            raise Warning('Error!', 'Mailing API is missing the url ' +
                          'for the ir.config_parameter ' +
                          'mailman-api-url')

        return MailmanClient(url, timeout)

    # Columns
    name = fields.Char('Name', size=256, required=True)
    subscriber_ids = fields.Many2many(
        'res.partner', string='Subscribers')
    mailman_response = fields.Text('Mailman Response')
    description = fields.Char('Description')
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [('mailman_list_unique', 'unique(name)',
                         'This mailing-list already exists!')]

    def _get_sync_actions(self, old_subscribers, new_subscribers, members):
        """
            old_subscribers: {'partner_id':'email',}
            new_subscribers: {'partner_id':('email','name'),}
            members: ['email',]
            return:
            sync_actions = {'odoo': {'add':[email]},
                            'mailman': {'add':[(email,fullname)],
                                        'del':[email]
                                        },
                            }
        """

        mailman_del = [old_subscribers[sub] for sub in old_subscribers
                       if sub not in new_subscribers and
                       old_subscribers[sub] in members]

        mailman_add = []
        subscribers_mail = []
        for subscriber in new_subscribers:
            subscribers_mail.append(new_subscribers[subscriber][0])
            if not new_subscribers[subscriber][0]:
                raise Warning(
                    'Error!',
                    'Subscriber %s has no email address' %
                    new_subscribers[subscriber][1])
            if new_subscribers[subscriber][0].lower() not in members:
                mailman_add.append(new_subscribers[subscriber])

        odoo_add = [m for m in members
                    if m not in subscribers_mail and m not in mailman_del]

        sync_actions = {'odoo': {'add': odoo_add},
                        'mailman': {'add': mailman_add,
                                    'del': mailman_del
                                    },
                        }

        return sync_actions

    @api.one
    def _process_sync_actions(self, mailman, listname, sync_actions):
        partner_env = self.env['res.partner']

        for email in sync_actions['mailman']['del']:
            mailman.unsubscribe(listname, email)

        for partner in sync_actions['mailman']['add']:
            mailman.subscribe(listname, partner[0], partner[1])

        new_subscribers = []
        unknown_members = []
        vals = {}
        for member in sync_actions['odoo']['add']:
            partners = partner_env.search([('email', '=', member)])
            if partners:
                new_subscribers.append((4, partners[0].id, 0))
            else:
                unknown_members.append(member)
        vals.update({'subscriber_ids': new_subscribers})

        if unknown_members:
            vals.update(
                {'mailman_response': 'Those email addresses exist in ' +
                 'mailman, but no partner with those emails can be ' +
                 'found. Please, create the partners first or ' +
                 'delete this "dangling" emails directly from ' +
                 'mailman. \n' +
                 'Unknown emails: %s' % unknown_members}
            )
        else:
            vals.update({'mailman_response': None})

        super(mailman_list, self).write(vals)
        return True

    def _recordset_to_list_ids(self, recordset):
        list_ids = []
        for record in recordset:
            list_ids.append(record.id)
        return list_ids

    @api.one
    def _save_in_mailman(self, mailman, old_subscribers):
        listname = self.name

        if mailman.has_list(listname):
            new_subscribers = {s.id: (s.email, s.name)
                               for s in self.subscriber_ids}

            members = [m.lower() for m in mailman.members(listname).json()]

            sync_actions = self._get_sync_actions(
                old_subscribers, new_subscribers, members)

            self._process_sync_actions(
                mailman, listname, sync_actions)

        else:
            vals = {'mailman_response':
                    "This mailing list does not exist in mailman."}

            super(mailman_list, self).write(vals)

    @api.model
    def create(self, vals):
        mailman = self._get_mailman()

        list = super(mailman_list, self).create(vals)
        list._save_in_mailman(mailman, {})

        return list

    @api.multi
    def write(self, vals):
        mailman = self._get_mailman()
        for list_obj in self:
            old_subscribers = {s.id: s.email
                               for s in list_obj.subscriber_ids}

            super(mailman_list, list_obj).write(vals)
            # Only field name and subscriber_ids will be synchronized
            if 'name' in vals or 'subscriber_ids' in vals:
                list_obj._save_in_mailman(mailman, old_subscribers)

        return True

    @api.multi
    def button_quick_subscription(self):
        models_data = self.env['ir.model.data']
        form_view = models_data.get_object_reference(
            'mailman', 'quick_subscription_wizard_form_view')
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'quick.subscription.wizard',
            'view_id': form_view and form_view[1] or False,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
