#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Usage:
# $ python restore_quotation_approved_date.py localhost

import erppeek
import sys


client = erppeek.Client.from_config(sys.argv[1])
SupportTicket = client.model('tms.support.ticket')

support_tickets = SupportTicket.browse(
    [('quotation_approved', '=', True),
     ('quotation_approved_date', '=', False)])
total = len(support_tickets)
count = 0
error = []
for support_ticket in support_tickets:
    count += 1
    print count
    for comment in support_ticket.tms_support_ticket_comment_ids:
        if comment.type == 'changelog' and \
                "Quotation Approved: Empty => True" in comment.comment:
            support_ticket.write({'quotation_approved_date': comment.name})
            break
    if support_ticket.quotation_approved_date:
        print "====  Restore successfully support ticket ", support_ticket.id
    if not support_ticket.quotation_approved_date:
        error.append(support_ticket.id)
        print "====  Unable to restore support ticket ", support_ticket.id
print "Restore successfully", count, "from ", total
print "Error: ", error
 