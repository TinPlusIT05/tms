#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Usage:
# $ python select_forge_ticket_invalid_subcribers.py tms

import erppeek
import pprint
import sys


client = erppeek.Client.from_config(sys.argv[1])

TmsSupportTicket = client.model('tms.support.ticket')
TmsSubscriber = client.model('tms.subscriber')
TmsProject = client.model('tms.project')
ResUsers = client.model('res.users')
ResPartner = client.model('res.partner')

tms_projects = TmsProject.browse([('active', 'in', (True, False))])

tms_subscriber_ids = TmsSubscriber.browse(
    [("support_id", "!=", None), ("support_id.state", "!=", 'closed')])


supporter_ids_dict = {}

for project in tms_projects:
    supporter_ids_dict[project.id] = \
        project.project_supporter_rel_ids.id

print "Supporter user ids per project id:"
pprint.pprint(supporter_ids_dict)


print "Checking the **%s** support subscribers of opened support tickets." % (
    len(tms_subscriber_ids))

i = 0
if tms_subscriber_ids:
    print 'Support tickets with subcribers which are not project supporters: '
    if len(tms_subscriber_ids) == 1:
        tms_subscriber_ids = [tms_subscriber_ids]
    for item in tms_subscriber_ids:
        if not item.support_id.project_id.active:
            print ("Project %s is not active, Support "
                   "ticket %s should be closed.") % (
                item.support_id.project_id.name,
                item.support_id.id)
            continue

        if item.name.id in supporter_ids_dict[item.support_id.project_id.id]:
            # Subscribe is a supporter
            continue

        print ("Ticket: %s | User: %s | Project: %s,") % (
            item.support_id.id, item.name.name,
            item.support_id.project_id.name)
        i += 1
print "There are still %s support tickets with subscribers not supporters." % i
