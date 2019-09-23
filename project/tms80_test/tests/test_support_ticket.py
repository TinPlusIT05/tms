# -*- coding: utf-8 -*-

from openerp.addons.test_runner.lib import case  # @UnresolvedImport
from datetime import datetime
import logging


class TestSupportTicket(case.ModuleCase):

    def _create_support_ticket(self, admin_uid, project_name, customer_name,
                               tmp_name, supporter_name,
                               customer_profile='TMS Customer Profile'):
        """
        A customer create a support ticket of a project
        - use admin user to create users: TPM, supporter, customer
        - use admin user to create project
        - use customer to create support ticket
        @return: customer_uid, support_ticket_id
        """
        support_ticket_obj = self.registry('tms.support.ticket')
        partner_obj = self.registry('res.partner')
        project_obj = self.registry('tms.project')
        user_obj = self.registry('res.users')
        group_obj = self.registry('res.groups')
        cr = self.cr
        # Find the existed profiles
        customer_profile_id = group_obj.search(
            cr, admin_uid, [('name', '=', customer_profile)]
        )[0]
        tpm_profile_id = group_obj.search(
            cr, admin_uid, [('name', '=', 'Technical Project Manager Profile')]
        )[0]
        fc_profile_id = group_obj.search(
            cr, admin_uid, [('name', '=', 'Functional Consultant Profile')]
        )[0]
        # create TPM user
        tpm_user_vals = {
            'name': tmp_name,
            'login': tmp_name,
            'password': 'tpm',
            'email': '%s@trobz.com' % tmp_name,
            'group_profile_id': tpm_profile_id,
            'is_trobz_member': True,
        }
        tpm_uid = user_obj.create(cr, admin_uid, tpm_user_vals)

        # Create support user
        fc_user_vals = {
            'name': supporter_name,
            'login': supporter_name,
            'password': 'supporter',
            'email': '%s@trobz.com' % supporter_name,
            'group_profile_id': fc_profile_id,
            'is_trobz_member': True,
        }
        fc_uid = user_obj.create(cr, admin_uid, fc_user_vals)

        # Create a Partner, it is:
        # - Customer on Project form
        # - Employer on User form
        # - Customer on Support ticket form
        customer_vals = {
            'name': customer_name,
            'is_company': True,
            'website': '%s-fake.com' % customer_name
        }
        customer_id = partner_obj.create(cr, admin_uid, customer_vals)

        # TPM creates a project
        # required for creating support ticket
        project_vals = {
            'name': project_name,
            'partner_id': customer_id,
            'technical_project_manager_id': tpm_uid,
            'state': 'active',
            'default_supporter_id': fc_uid,
            'project_supporter_rel_ids': [(4, fc_uid), (4, tpm_uid)]
        }
        # Computing the supporters here avoids the access control
        # related to `res.partner`.
        project_id = project_obj.create(
            cr, admin_uid, project_vals
        )
        # Create customer user
        customer_user_vals = {
            'name': customer_name,
            'login': customer_name,
            'password': 'customer',
            'email': '%s@test.com' % customer_name,
            'group_profile_id': customer_profile_id,
            'is_trobz_member': False,
            'supporter_of_project_ids': [(6, 0, [project_id])],
            'employer_id': customer_id,
        }
        customer_uid = user_obj.create(cr, admin_uid, customer_user_vals)
        # Customer create a support ticket
        support_ticket_vals = {
            'reporter_id': customer_uid,
            'summary': 'Support ticket test',
            'description': 'Support Ticket Test',
            'state': 'assigned',
            'ticket_type': 'unclassified',
            'priority': 'normal',
            'project_id': project_id,
            'customer_id': customer_id,
        }
        support_ticket_id = support_ticket_obj.create(
            cr, customer_uid, support_ticket_vals,
            {'test_support_ticket': True}
        )
        return customer_uid, support_ticket_id

    def test_support_ticket(self):
        """
        Run test support ticket:
        - Customer must be able to create a support ticket
        - Customer must be able to update a support ticket
        - Customer should not be able to see support tickets
            from other customers
        """
        user_obj = self.registry('res.users')
        group_obj = self.registry('res.groups')
        support_ticket_obj = self.registry('tms.support.ticket')
        ticket_comment_obj = self.registry('tms.ticket.comment')
        cr, uid = self.cr, self.uid
        # Find the existed profiles
        admin_profile_id = group_obj.search(
            cr, uid, [('name', '=', 'Admin Profile')]
        )[0]
        # Create a manager user, then use it to create other users and project
        admin_user_vals = {
            'name': 'Manager',
            'login': 'manager',
            'password': 'manager',
            'email': 'manager@trobz.com',
            'group_profile_id': admin_profile_id,
            'is_trobz_member': True,
            'has_full_sysadmin_access': True,
        }
        admin_uid = user_obj.create(cr, uid, admin_user_vals)

        # Customer creates a support ticket
        cus1_uid, ticket1_id = self._create_support_ticket(
            admin_uid, 'Project test 1', 'customer_1', 'tmp_1',
            'supporter_1')
        _, ticket2_id = self._create_support_ticket(
            admin_uid, 'Project test 2', 'customer_2', 'tmp_2',
            'supporter_2')
        logging.info('[OK] Customer can create a support ticket.')
        # Customer must be able to update a support ticket
        # Customer changes name, description, priority, Owner, Status
        update_vals = {
            'summary': 'Update support ticket test',
            'description': 'Update support Ticket Test',
            'state': 'ok_for_production',
            'priority': 'major',
        }
        support_ticket_obj.write(
            cr, cus1_uid, ticket1_id, update_vals,
            {'test_support_ticket': True}
        )
        logging.info('[OK] Customer can update a support ticket.')
        # Customer should be able to read tickets he created himself.
        support_ticket_obj.read(cr, cus1_uid, ticket1_id)
        logging.info('[OK] Customer can read the support ticket '
                     'he created himself.')
        # Customer should not be able to
        # see support tickets from other customers
        try:
            support_ticket_obj.read(
                cr, cus1_uid, ticket2_id
            )
        except Exception:
            logging.info('[OK] Customer cannot read the support ticket ' +
                         'of other customer.')
            pass
        # Add comments on support ticket
        comment_vals = {
            'name': datetime.now(),
            'author_id': cus1_uid,
            'comment': 'Test comment',
            'tms_support_ticket_id': ticket1_id,
        }
        ticket_comment_obj.create(cr, cus1_uid, comment_vals)
        logging.info('[OK] Customer can create a comment')
