# -*- coding: utf-8 -*-

from openerp.addons.test_runner.lib import case  # @UnresolvedImport
import logging
import time


class test_delivery_status(case.ModuleCase):

    def create_forge_ticket(self, n):
        forge_ticket_obj = self.env['tms.forge.ticket']
        project_obj = self.env['tms.project']
        milestone_obj = self.env['tms.milestone']
        activity_obj = self.env['tms.activity']
        name = "TestTmsCode_%d" % (n)
        projec_vals = {
            'name': name,
            'partner_id': 60,
            'state': 'active',
            'technical_project_manager_id': 5,
            'active': True,
            'invc_by_trobz_vn': True,
        }
        project = project_obj.create(projec_vals)

        milestone_vals = {
            'number': 1.0,
            'project_id': project.id,
            'state': 'planned'
        }
        milestone_vals1 = {
            'number': 1.1,
            'project_id': project.id,
            'state': 'planned'
        }
        milestone_vals2 = {
            'number': 1.2,
            'project_id': project.id,
            'state': 'planned'
        }
        milestone_obj.create(milestone_vals1)
        milestone_obj.create(milestone_vals2)
        milestone_1 = milestone_obj.create(milestone_vals)

        activity_vals = {
            'name': 'demo',
                    'project_id': project.id,
                    'priority': 'normal',
                    'state': 'planned',
                    'working_hours_requires_ticket': True,
                    'is_billable': True,
                    'active': True,
                    'analytic_secondaxis_id': 1,
                    'account_id': 1,
                    'owner_id': 1
        }

        activity = activity_obj.create(activity_vals)

        forge_ticket_vals = {
            'summary': 'Test1',
            'project_id': project.id,
            'priority': 'normal',
            'state': 'ready_to_deploy',
            'owner_id': 5,
            'tms_activity_id': activity.id,
            'milestone_id': milestone_1.id,
        }
        return forge_ticket_obj.create(
            forge_ticket_vals)

    def update_delivery_status(self, forge_ticket, instance):
        tms_instance_obj = self.env['tms.instance']
        instance_name = 'openerp-%s-%s' % (forge_ticket.project_id.name,
                                           instance)
        url = '%s.trobz.com' % (forge_ticket.project_id.name)
        instance_delivery_vals = {
            'project_id': forge_ticket.project_id.id,
            'server_type': instance,
            'name': instance_name,
            'milestone_id': forge_ticket.milestone_id.id,
            'host_id': 1,
            'url': url,
            'backend_port': '8069',
                            'state': 'active',
                            'active': True,
                            'psql_host': 'localhost',
                            'psql_port': '5432',
                            'psql_user': instance_name,
                            'psql_pass': instance_name,
        }
        instance = tms_instance_obj.create(instance_delivery_vals)

        tms_delivery_obj = self.env['tms.delivery']
        delivery_vals = {
            'name': time.strftime("%c"),
            'instance_id': instance.id,
            'state': 'done',
        }
        return tms_delivery_obj.create(delivery_vals)

    def test_deploy_staging(self):
        logging.info('''\n\n===== START test_deploy_staging =====''')

        forge_ticket = self.create_forge_ticket(1)
        self.update_delivery_status(forge_ticket, 'staging')

        logging.info(''' Expected Delivery Status: In Staging''')
        logging.info(''' The delivery status of ticket: (%s, %s)
            ''' % (forge_ticket.id, forge_ticket.delivery_status))

        logging.info('''===== END test_deploy_staging =====''')

    def test_deploy_production(self):
        logging.info('''\n\n===== START test_deploy_production =====''')

        forge_ticket = self.create_forge_ticket(2)
        self.update_delivery_status(forge_ticket, 'production')

        logging.info(''' Expected Delivery Status: In Production''')
        logging.info(''' The delivery status of ticket: (%s, %s)
            ''' % (forge_ticket.id, forge_ticket.delivery_status))

        logging.info('''===== END test_deploy_production =====''')

    def test_production_to_staging(self):
        logging.info('''\n\n===== START test_production_to_staging =====''')

        forge_ticket = self.create_forge_ticket(3)
        self.update_delivery_status(forge_ticket, 'production')
        logging.info(''' Deploy production success ''')

        self.update_delivery_status(forge_ticket, 'staging')
        logging.info(''' Deploy staging success ''')

        logging.info(''' Expected Delivery Status: In Production''')
        logging.info(''' The delivery status of ticket: (%s, %s)
            ''' % (forge_ticket.id, forge_ticket.delivery_status))

        logging.info('''===== END test_production_to_staging =====''')

    def test_staging_to_integration(self):
        logging.info('''\n\n===== START test_staging_to_integration =====''')

        forge_ticket = self.create_forge_ticket(4)
        self.update_delivery_status(forge_ticket, 'staging')
        logging.info(''' Deploy staging success ''')

        self.update_delivery_status(forge_ticket, 'integration')
        logging.info(''' Deploy integration success ''')

        logging.info(''' Expected Delivery Status: In Staging''')
        logging.info(''' The delivery status of ticket: (%s, %s)
            ''' % (forge_ticket.id, forge_ticket.delivery_status))

        logging.info('''===== END test_staging_to_integration =====''')

    def test_deploy_integration(self):
        """
        Run test delivery status:
        - Check delivery_status of support tickets.
        - Check delivery_status of forge tickets.
        """
        logging.info('''\n\n===== START test_deploy_integration =====''')

        forge_ticket = self.create_forge_ticket(5)
        if forge_ticket:
            logging.info('''The delivery status of ticket created: (%s, %s)
            ''' % (forge_ticket.id, forge_ticket.delivery_status))
        else:
            logging.info('No ticket created!')

        self.update_delivery_status(forge_ticket, 'integration')

        logging.info(''' Expected Delivery Status: In Integration''')
        logging.info('''The delivery status of ticket integration: (%s, %s)
            ''' % (forge_ticket.id, forge_ticket.delivery_status))

        logging.info('''===== END test_deploy_integration =====''')
