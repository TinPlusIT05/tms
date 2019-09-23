# -*- coding: utf-8 -*-
##############################################################################
from openerp import models, fields, api

REOPENING_TYPES = [
    ('defect', 'Defect'),
    ('mis_analysis', 'Mis-analysis'),
    ('new_requirement', 'New requirement'),
    ('refactor', 'Refactoring Source Code'),
    ('deployment_issue', 'Deployment Issue')
]

REOPENING_TYPES_HELP = """
* Defect: the ticket has not been implemented as specified in the summary and
  description of the ticket.
* Mis-Analysis: The developer did implement the ticket as specified but
  the solution cannot solve fully the requirement of the user.
* New Requirement: this is not linked to the initial requirement and
  could not have been guessed by the developer
* Refactoring Source Code: this is used when TPM wants to reopen related ticket
  to ask DEV to adjust the source code.
* Deployment Issue: this is problem comes from deployment
  This value will not be calculated in KPI for Reopening Rate\n
"""


class reopen_ticket_wizard(models.TransientModel):

    _name = 'reopen.ticket.wizard'
    _description = 'Reopen Forge Ticket'

    reopening_type = fields.Selection(
        selection=REOPENING_TYPES,
        string='Re-opening type',
        required=True,
        help=REOPENING_TYPES_HELP)
    # Apply for New requirement
    reopen_sprint = fields.Date(string='Sprint')
    comment = fields.Text('Comment', required=True)

    @api.multi
    def re_open_ticket(self):
        context = self._context and self._context.copy() or {}
        reopening_dict = {
            'defect': 'Defect',
            'mis_analysis': 'Mis-analysis',
            'new_requirement': 'New requirement',
            'refactor': 'Refactoring Source Code',
            'deployment_issue': 'Deployment Issue',
        }
        if self.ids and context.get('active_ids', False):
            forge_ticket_ids = context['active_ids']
            wizard_obj = self.browse(self.ids[0])
            reopening_type = wizard_obj.reopening_type or False
            comment = wizard_obj.comment or False
            context.update({
                'reopening_type': reopening_type,
                'comment': comment
            })

            forge_ticket_env = self.env['tms.forge.ticket']
            ticket_comment_env = self.env['tms.ticket.comment']
            forge_ticket_objs = forge_ticket_env.with_context(
                context
            ).browse(forge_ticket_ids)
            for forge_ticket in forge_ticket_objs:
                if reopening_type in reopening_dict.keys():
                    reopening_type = reopening_dict[reopening_type]

                # Write new comment for forge ticket: Re-opening for
                # {re-opening type}: {comment}
                comment_vals = {
                    'tms_forge_ticket_id': forge_ticket.id,
                    'type': 'comment',
                    'comment': "Re-opening for " + reopening_type + ": " +
                    comment
                }
                ticket_comment_env.with_context(context).create(comment_vals)

                # Change state of forge_ticket_ids to assigned and create the
                # record "forge.ticket.reopening"
                vals = {
                    'state': 'assigned',
                    'owner_id': forge_ticket.last_completer_id and
                    forge_ticket.last_completer_id.id or False
                }
                forge_ticket.with_context(context).write(vals)

        return {
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window_close'
        }

    @api.multi
    def button_create_new_ticket(self):
        context = self._context and self._context.copy() or {}
        for reopen in self:
            if 'active_ids' in context and context.get('active_ids', False):
                reopening_dict = {
                    'defect': 'Defect',
                    'mis_analysis': 'Mis-analysis',
                    'new_requirement': 'New requirement',
                    'refactor': 'Refactoring Source Code'
                }
                tms_forge_ticket_env = self.env['tms.forge.ticket']
                ticket_comment_env = self.env['tms.ticket.comment']

                reopening_type = reopen.reopening_type or False
                comment = reopen.comment or False

                if reopening_type in reopening_dict.keys():
                    reopening_type = reopening_dict[reopening_type]

                for active_id in context.get('active_ids', False):
                    current_forge_ticket = tms_forge_ticket_env.browse(
                        active_id)
                    project_id = current_forge_ticket.project_id and \
                        current_forge_ticket.project_id.id or False
                    milestone_id = current_forge_ticket.milestone_id and \
                        current_forge_ticket.milestone_id.id or False
                    priority = current_forge_ticket.priority
                    sprint_date = reopen.reopen_sprint or\
                        current_forge_ticket.sprint\
                        and current_forge_ticket.sprint or False
                    tms_support_ticket_id = \
                        current_forge_ticket.tms_support_ticket_id \
                        and current_forge_ticket.tms_support_ticket_id.id \
                        or False
                    quotation = current_forge_ticket.quotation
                    tms_functional_block_id = \
                        current_forge_ticket.tms_functional_block_id and \
                        current_forge_ticket.tms_functional_block_id.id or \
                        False
                    yaml_test_status = current_forge_ticket.yaml_test_status
                    summary = current_forge_ticket.summary
                    owner_id = current_forge_ticket.last_completer_id \
                        and current_forge_ticket.last_completer_id.id or False
                    new_summary = "[Adjust ticket " + str(active_id) + "]" + \
                        summary
                    # Compute description for new requrement type
                    parent_forge = False
                    description = comment
                    if reopening_type == 'New requirement':
                        description_template = \
                            '#Initial requirement\n%s\n#New requirement\n%s'
                        parent_forge = self.env['tms.forge.ticket'].browse(
                            active_id)
                        parent_description = parent_forge and \
                            parent_forge.description or None
                        description = description_template % (
                            parent_description, comment)

                    parent_forge_ticket_id = parent_forge and\
                        parent_forge.get_parent_ticket_id() or active_id
                    new_forge_ticket_data = {
                        'summary': new_summary,
                        'description': description,
                        'project_id': project_id,
                        'milestone_id': milestone_id,
                        'priority': priority,
                        'sprint': sprint_date,
                        'tms_support_ticket_id': tms_support_ticket_id,
                        'quotation': quotation,
                        'yaml_test_status': yaml_test_status,
                        'parent_forge_ticket_id': parent_forge_ticket_id,
                        'reporter_id': self._uid,
                        'owner_id': owner_id,
                        'tms_functional_block_id': tms_functional_block_id
                    }

                    new_ticket_id = tms_forge_ticket_env.create(
                        new_forge_ticket_data)

                    comment_vals = {
                        'tms_forge_ticket_id': active_id,
                        'type': 'comment',
                        'comment': "Re-opening for " + reopening_type +
                                   " in new ticket " + str(new_ticket_id.id) +
                                   " : " + new_summary
                    }

                    ticket_comment_env.create(comment_vals)
        return True
