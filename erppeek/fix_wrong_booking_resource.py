#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Usage:
# $ python select_wrong_booking_resource.py tms

import erppeek
import sys
from datetime import datetime

client = erppeek.Client.from_config(sys.argv[1])

BookingResource = client.model('booking.resource')
BookingChart = client.model('booking.chart')
HrResourceAllocation = client.model('hr.resource.allocation')
HrHolidays = client.model('hr.holidays')
HrHolidaysLine = client.model('hr.holidays.line')
HrDedicated = client.model('hr.dedicated.resource.contract')

booking_resources = BookingResource.browse([])
booking_ra_id = BookingChart.browse([
    ('name', '=', 'Booking Resource Allocation')]).id[0]
booking_drc_id = BookingChart.browse([
    ('name', '=', 'Chart of Dedicated Resources Contracts')]).id[0]
wrong_booking_resource = 0
mapping_error = 0
missing_date = 0
br_holidays = {}
if booking_resources:
    print 'Totals Booking Resources: %s' % len(booking_resources)
    for booking_resource in booking_resources:
        booking_resource_id = booking_resource.read("id")
        origin = booking_resource.origin_ref or False
        target = booking_resource.target_ref or False
        chart_id = booking_resource.chart_id.id
        booking_start = datetime.strptime(booking_resource.date_start,
                                          "%Y-%m-%d %H:%M:%S").date()
        booking_end = datetime.strptime(booking_resource.date_end,
                                        "%Y-%m-%d %H:%M:%S").date()
        if chart_id == booking_ra_id:
            ra_obj = origin
            current_sprint_obj = ra_obj.sprint or False

            # In case old records, current sprint does not exist
            if not current_sprint_obj:
                print 'Resource Allocation Missing Sprint : %s' % ra_obj.id
            else:
                start_sprint = current_sprint_obj.date_start
                end_sprint = current_sprint_obj.date_end
        elif chart_id == booking_drc_id:
            # in case chart = 'Chart of Dedicated Resources Contracts'
            if not target:
                # In case missing target and origin is hr.holidays
                holiday_obj = origin
                holiday_line_obj = holiday_obj.holiday_line
                if len(holiday_line_obj) > 1:
                    is_br = False
                    for line_obj in holiday_line_obj:
                        start_sprint = datetime.strptime(line_obj.first_date,
                                                         '%Y-%m-%d').date()
                        end_sprint = datetime.strptime(line_obj.last_date,
                                                       '%Y-%m-%d').date()
                        if booking_start == start_sprint and\
                                booking_end == end_sprint:
                            is_br = True
                            if line_obj.id in br_holidays:
                                print "1 holiday line maps to 2 booking" +\
                                      " resources: %s, %s" % (
                                          booking_resource_id,
                                          br_holidays[line_obj.id])
                                mapping_error += 1
                            else:
                                br_holidays.update(
                                    {line_obj.id: booking_resource_id})
                    if not is_br:
                        # CHECK AND REMOVE
                        print "DRC-Wrong Booking Resource: %s" %\
                              booking_resource_id
                        wrong_booking_resource += 1
                        continue

                start_sprint = holiday_line_obj.first_date[0]
                end_sprint = holiday_line_obj.last_date[0]
            else:
                # In case existing target and
                # origin is hr.dedicated.resource.contract
                dedicated_resource_obj = origin
                start_sprint = dedicated_resource_obj.start_date
                end_sprint = dedicated_resource_obj.end_date
        else:
            # in case chart = 'HR holidays chart'
            holidays_line_obj = origin
            start_sprint = holidays_line_obj.first_date
            end_sprint = holidays_line_obj.last_date

        if not start_sprint or not end_sprint:
            print "Booking Resource without " +\
                  "start date or end date: %s" % booking_resource_id
            missing_date += 1
            continue
        start_sprint = datetime.strptime(start_sprint, '%Y-%m-%d').date()
        end_sprint = datetime.strptime(end_sprint, '%Y-%m-%d').date()
        if booking_start != start_sprint or booking_end != end_sprint:
            # CHECK AND REMOVE
            print "Wrong Booking Resource: %s" % booking_resource_id
            wrong_booking_resource += 1

            booking_resource.write(
                {'date_start': start_sprint.strftime("%Y-%m-%d 00:00:00"),
                 'date_end': end_sprint.strftime("%Y-%m-%d 00:00:00")})
print "===============***==============="
print "Total Wrong BR: %s" % wrong_booking_resource
print "Total BR missing date: %s" % missing_date
print "Total duplicate mapping: %s" % mapping_error
