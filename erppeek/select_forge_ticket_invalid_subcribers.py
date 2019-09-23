#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Usage:
# $ python select_forge_ticket_invalid_subcribers.py tms

import erppeek
import sys

client = erppeek.Client.from_config(sys.argv[1])

TmsForgeTicket = client.model('tms.forge.ticket')
TmsSubscriber = client.model('tms.subscriber')
TmsProject = client.model('tms.project')
ResUsers = client.model('res.users')
ResPartner = client.model('res.partner')

res_partner_ids = ResPartner.browse([("name","!=","Trobz Co., Ltd.")]).read("id")
res_user_ids = ResUsers.browse([("employer_id","in",res_partner_ids)]).read("id")
tms_subscriber_ids = TmsSubscriber.browse([("name","in",res_user_ids)])

i = 0
if tms_subscriber_ids:
    print 'The forge ticket have subscribers is not Trobz employee: '
    for item in tms_subscriber_ids.forge_id:
        if item != False:
            project_id = item.project_id.read("id")
            tms_project_name = TmsProject.browse([("id","=",project_id)]).read("name")
            print "Ticket: %s -- Project:%s"%(item, tms_project_name)
            i += 1
print "There are still %s tickets with subscribers not trobz employees." % i

