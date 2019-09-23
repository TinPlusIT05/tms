# -*- coding: utf-8 -*-

import logging

from openerp.addons.test_runner.lib import case  # @UnresolvedImport
from openerp.tools import mute_logger


class TestMailNoticationPreference(case.ModuleCase):

    '''
    This tests are focused on testing the function:
     - get_subscriber_email_list_by_ticket
    '''

    TMS_SUPPORT_TICKET = 'tms.support.ticket'
    TMS_FORGE_TICKET = 'tms.forge.ticket'
    SUPPORT_TICKET_ID = 6883
    SUPPORT_SUBSCRIBER_FIELD = 'support_ticket_subscriber_ids'

    '''
        Production data
    '''
    CUSTOMER_AMPFIELD_ID = 2  # Ampfield
    PROJECT_AMPFIELD_ID = 1  # Ampfield
    UID_JC = 3
    UID_TU = 5
    UID_DB = 7
    EMAIL_JC = 'jcdrubay@trobz.com'
    EMAIL_TU = 'tu@trobz.com'
    EMAIL_DB = 'dbarbot@trobz.com'
    NOTIF_ALL_ID = 1
    NOTIF_MOST_ID = 2
    NOTIF_MIN_ID = 3
    NOTIF_MOST_FIELDS_EX = ['priority']
    NOTIF_ALL_ONLY_FIELDS_EX = ['milestone_id']

    def setUp(self):
        super(TestMailNoticationPreference, self).setUp()

        self.UserObj = self.env['res.users']
        JC_obj = self.UserObj.browse(self.UID_JC)
        self.SupportTicketObj = self.env['tms.support.ticket'].sudo(JC_obj)
        self.ProjectAmpfield = self.env['tms.project'].browse(
            self.PROJECT_AMPFIELD_ID)

    def _dict_to_key_val_str(self, _dict):
        return ", ".join(["[%s] %s" % (k, v) for (k, v) in _dict.items()])

    def _check_subscribers(self, ticket_obj, expected_subscribers):

        count_expected_subsriber = len(expected_subscribers)
        expected_subscribers_str = self._dict_to_key_val_str(
            expected_subscribers)
        subscribers = ticket_obj.support_ticket_subscriber_ids
        subscribers_str = u', '.join(
            subscribers.mapped(lambda r: "[%s] %s" % (r.name.id,
                                                      r.name.name)))

        msg = '%s subscribers expected (%s). Found %s' % (
            count_expected_subsriber,
            expected_subscribers_str,
            subscribers_str)

        self.assertEquals(len(subscribers), count_expected_subsriber, msg)

        count_in = 0

        for subscriber in subscribers:
            for es in expected_subscribers:
                if es == subscriber.name.id:
                    count_in += 1
                    continue

        msg = 'The subscribers (%s) are not the one expected (%s).' % (
            subscribers_str, expected_subscribers_str)

        self.assertEquals(count_in, count_expected_subsriber, msg)

    @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def test_create_ticket_adds_assignee_reporter_as_subscribers(self):
        global SUPPORT_TICKET_ID
        vals = {
            'summary': 'Test',
            'project_id': self.PROJECT_AMPFIELD_ID,
            'customer_id': self.CUSTOMER_AMPFIELD_ID,
            'owner_id': self.UID_TU,
            'reporter_id': self.UID_JC,
        }
        ticket_obj = self.SupportTicketObj.create(vals)
        SUPPORT_TICKET_ID = ticket_obj.id

        expected_subscribers = {
            self.UID_TU: 'Assignee',
            self.UID_JC: 'Reporter'}

        self._check_subscribers(ticket_obj, expected_subscribers)

    def _get_mail_to(self, author_notif_id, assignee_notif_id, normal_notif_id,
                     fields_change):
        ticket_obj = self.SupportTicketObj.browse(SUPPORT_TICKET_ID)
        context = {}
        subscriber_ids = [[0, False, {'name': self.UID_JC,
                                      'tk_notif_pref_id': author_notif_id}],
                          [0, False, {'name': self.UID_TU,
                                      'tk_notif_pref_id': assignee_notif_id}],
                          [0, False, {'name': self.UID_DB,
                                      'tk_notif_pref_id': normal_notif_id}],
                          ]

        ticket_obj.support_ticket_subscriber_ids.unlink()
        ticket_obj.write({self.SUPPORT_SUBSCRIBER_FIELD: subscriber_ids,
                          'owner_id': self.UID_TU})

        return self.SupportTicketObj.get_subscriber_email_list_by_ticket(
            self.TMS_SUPPORT_TICKET,
            ticket_obj,
            self.SUPPORT_SUBSCRIBER_FIELD,
            fields_change,
            context)

    '''
        I found a list of list being the most suitable  to store those cases
        as it allows to compare easily all the cases. Otherwise, I would
        have preferred a dictionary for a more explicit declaration.

        Here are the "keys" of those list of test cases:
        [Test Case ID, Notif of Author, Notif of Assignee, Notif of Normal,
            Kind of field changed, expected emails]


        JC is the author
        Tu is the assignee
        DB is a normal user
    '''

    TEST_CASES = [
        ['C1', NOTIF_ALL_ID, NOTIF_ALL_ID, NOTIF_ALL_ID,
            NOTIF_ALL_ONLY_FIELDS_EX, [EMAIL_JC, EMAIL_TU, EMAIL_DB]],
        ['C2', NOTIF_MOST_ID, NOTIF_MOST_ID, NOTIF_MOST_ID,
            NOTIF_ALL_ONLY_FIELDS_EX, [EMAIL_TU]],
        ['C3', NOTIF_MIN_ID, NOTIF_MIN_ID, NOTIF_MIN_ID,
            NOTIF_ALL_ONLY_FIELDS_EX, [EMAIL_TU]],
        ['C4', NOTIF_ALL_ID, NOTIF_ALL_ID, NOTIF_ALL_ID,
            NOTIF_MOST_FIELDS_EX, [EMAIL_JC, EMAIL_TU, EMAIL_DB]],
        ['C5', NOTIF_MOST_ID, NOTIF_MOST_ID, NOTIF_MOST_ID,
            NOTIF_MOST_FIELDS_EX, [EMAIL_TU, EMAIL_DB]],
        ['C6', NOTIF_MIN_ID, NOTIF_MIN_ID, NOTIF_MIN_ID,
            NOTIF_MOST_FIELDS_EX, [EMAIL_TU]],
    ]

    '''
        Notes about some cases:

    '''

    def _assert_mail_to_equal(self, tc_id, mails, expected_mails):
        if len(mails) == 0 and len(expected_mails) == 0:
            return
        try:
            self.assertSetEqual(set(mails.split(',')), set(expected_mails))
        except AssertionError as e:
            logging.info('FAIL: %s', tc_id)
            raise e

    @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def test_get_subscriber_email_list_by_ticket(self):
        for tc in self.TEST_CASES:
            mails = self._get_mail_to(tc[1], tc[2], tc[3], tc[4])
            self._assert_mail_to_equal(tc[0], mails, tc[5])
