# -*- coding: utf-8 -*-

from openerp.tests import common


class test_mailman(common.TransactionCase):

    def setUp(self):

        super(test_mailman, self).setUp()
        self.list = self.registry('mailman.list')

    def test_00_get_sync_actions(self):
        old_subscribers = {'1': 'test1@mail.com',
                           '2': 'test2@mail.com',
                           '3': 'test3@mail.com',
                           '6': 'test6@mail.com',
                           }
        new_subscribers = {'1': ('test1@mail.com', 'Name 1'),
                           '2': ('test2@mail.com', 'Name 2'),
                           '4': ('test4@mail.com', 'Name 4'),
                           }
        members = ['test1@mail.com', 'test3@mail.com', 'test5@mail.com']

        sync_actions = self.list._get_sync_actions(old_subscribers,
                                                   new_subscribers,
                                                   members)

        self.assertEqual(sync_actions['odoo']['add'], ['test5@mail.com'])
        self.assertEqual(sync_actions['mailman']['add'],
                         [('test2@mail.com', 'Name 2'),
                          ('test4@mail.com', 'Name 4')],)
        self.assertEqual(sync_actions['mailman']['del'], ['test3@mail.com'])

    '''
    # Run this test only if you have a mailman server running.
    def test_01_create(self):

        cr, uid = self.cr, self.uid
        vals = {'name':'list_test_01_create_1'}
        list_1 = self.list.create(cr, uid, vals, context=None)
        self.assertIsNotNone(list_1)
        self.assertRaises(IntegrityError, self.list.create, cr, uid,vals,
                                                      context=None)
    '''
