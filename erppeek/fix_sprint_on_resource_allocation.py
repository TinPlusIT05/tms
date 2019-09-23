#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Usage:
# $ python fix_sprint_resource_allocation.py tms

import erppeek
import sys
from datetime import datetime

client = erppeek.Client.from_config(sys.argv[1])

HrResourceAllocation = client.model('hr.resource.allocation')

resource_allocations = HrResourceAllocation.browse([])
old_records = 0
if resource_allocations:
    print 'Total Resource Allocations: %s' % len(resource_allocations)
    for resource_allocation in resource_allocations:
        if not resource_allocation.sprint:
            sprint = client.execute(
                'daily.mail.notification', 'get_sprint_by_date',
                [resource_allocation.date_to])
            resource_allocation.write({'sprint': sprint})
            old_records += 1

print 'Total resource allocation without sprint : %s' % old_records
