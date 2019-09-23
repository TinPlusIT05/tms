#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Usage:
# $ python check_booking_resource.py tms

import erppeek
import sys
from datetime import datetime

client = erppeek.Client.from_config(sys.argv[1])

BookingChart = client.model('booking.chart')
BookingResource = client.model('booking.resource')

booking_ra_id = BookingChart.browse([
    ('name', '=', 'Booking Resource Allocation')]).id[0]
booking_resources = BookingResource.browse([('name', 'ilike',
                                             '%Days Off (%')])
nb = []
for booking_resource in booking_resources:
    sprint = booking_resource.origin_ref.sprint
    name = booking_resource.name
    date_start = name[-25:-15]
    date_end = name[-11: -1]
    date_start = datetime.strptime(date_start, "%Y-%m-%d").date()
    date_end = datetime.strptime(date_end, "%Y-%m-%d").date()
    booking_start = datetime.strptime(booking_resource.date_start,
                                      "%Y-%m-%d %H:%M:%S").date()
    booking_end = datetime.strptime(booking_resource.date_end,
                                    "%Y-%m-%d %H:%M:%S").date()
    if sprint:
        if not (date_start >= booking_start and date_end <= booking_end):
            nb.append(booking_resource.id)
print "List Booking Resource need to CHECK: %s" % nb
