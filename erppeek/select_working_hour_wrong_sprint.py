#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Usage:
# $ python select_working_hour_wrong_sprint.py tms

import erppeek
import sys

client = erppeek.Client.from_config(sys.argv[1])

TmsWorkingHour = client.model('tms.working.hour')

working_hours = TmsWorkingHour.browse([("date", ">=", "2016-01-01")])
i = 0

if working_hours:
    print 'Totals Working Hour: %s' % len(working_hours)
    for working in working_hours:
        date = working.date
        current_sprint = working.sprint and working.sprint
        sprint = client.execute(
            'daily.mail.notification',
            'get_sprint_by_date', [date])
        if sprint and current_sprint:
            if sprint == current_sprint:
                continue
            else:
                i += 1
                print "User Name: %s | Working Hour: Id: %s | : %s | Wrong Sprint: %s" % (working.user_id.name, working.id, date, working.sprint)
        elif not current_sprint:
            print "User Name: %s | Working Hour: Id: %s Doesn't Set Sprint" % (working.user_id.name, working.id,)
        elif not sprint:
            print "Not Found Sprint" % (working.id,)
print "Total: %s" % (i,)
