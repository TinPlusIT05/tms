# -*- coding: utf-8 -*-

from openerp.addons.test_runner.lib import case  # @UnresolvedImport


class TestCreateUser(case.ModuleCase):

    load = [
        'data/res.partner.csv',
        'data/res.users.csv'
    ]

    def test_create_users(self):
        """
        #TODO: Must have the profiles before user creation
        Create Trobz users using SUPERUSER rights.
        """
        # Admin
        user = self.browse_by_ref('demo_user_manager')
        self.assertEquals(user.name, 'Admin')
        # HR Manager
        user = self.browse_by_ref('demo_user_hr')
        self.assertEquals(user.name, 'HR Manager')
        # Technical Project Manager
        user = self.browse_by_ref('demo_user_tpm')
        self.assertEquals(user.name, 'Technical Project Manager')
        # Functional Consultant
        user = self.browse_by_ref('demo_user_fc')
        self.assertEquals(user.name, 'Functional Consultant')
        # Technical Consultant
        user = self.browse_by_ref('demo_user_tc')
        self.assertEquals(user.name, 'Technical Consultant')
        # Quality Control
        user = self.browse_by_ref('demo_user_qc')
        self.assertEquals(user.name, 'Quality Control')
        # Sysadmin
        user = self.browse_by_ref('demo_user_sysadmin')
        self.assertEquals(user.name, 'Sysadmin')
        # Sales
        user = self.browse_by_ref('demo_user_sales')
        self.assertEquals(user.name, 'Sales')
