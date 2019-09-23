#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Description: Analyze the reopening type of a user since the beginning of his
# work to now.
# Usage:
# $ python analyze_reopening_reason.py tms-production {user login}

import erppeek
from operator import itemgetter
from collections import OrderedDict
import os
import re
import sys

from trobz.log import init_logger, logger

init_logger()
log = logger('analyze.reopening.reason')

if len(sys.argv) < 3:
    log.error('Missing argument. Usage '
              '`python analyze_reopening_reason.py {env} {user login}`')
    exit(os.EX_USAGE)

client = erppeek.Client.from_config(sys.argv[1])

User = client.model('res.users')
user_login = sys.argv[2]
target_user = User.browse([('login', '=', user_login)])
if not target_user:
    log.error('Cannot find user with login %s' % user_login)
    exit(os.EX_NOTFOUND)
user_id = target_user.id[0]

ForgeTicket = client.model('tms.forge.ticket')
ForgeReopening = client.model('forge.ticket.reopening')
WorkingHour = client.model('tms.working.hour')

# Analyze reopening by types
reopen_types = {}
TYPE_HEADER = ['Reopening Type', 'No. of Tickets']
# Categories to analyze
REOPEN_CATEG_DESCRIPTION = {
    '1-missing_req': 'Missing some requirements',
    '2-misunderstand_req': 'Misunderstanding the requirements',
    '3-not_test_before_commit': 'Not testing before code commit',
    '4-defect_code_completed': 'Defect at status code completed',
    '5-others': 'Other reasons'
}
CATEG_KEYWORDS = {
    '1-missing_req': '(miss|lack|(all (requirements|points).*not done))',
    '2-misunderstand_req': '(mis[ -]*under(stand|stood)|' +
    '((get|got|under(stand|stood)).*(wrong|(not |in|un)correct)))',
    '3-not_test_before_commit': '(error|error when upgrad|' +
    '(still (not|in|un)correct))'
}
reopen_categs = {
    '1-missing_req': [],
    '2-misunderstand_req': [],
    '3-not_test_before_commit': [],
    '4-defect_code_completed': [],
    '5-others': []
}
CATEG_HEADER = ['Reopening ID', 'Type', 'Previous Status',
                'TS for Fix before reopening (h)',
                'Ticket', 'Ticket Estimation (h)', 'Time Spent (h)',
                'Time Over Consumed (h)']
# affected tickets
reopened_ticket_ids = []
# Analyze all reopenings (except the invalid ones)
reopenings = ForgeReopening.browse(
    [('last_completer_id', '=', user_id),
     ('reopening_type', '!=', 'invalid')])
reopening_total = len(reopenings)
reopening_count = 0
for reopening in reopenings:
    reopening_count += 1
    sys.stdout.write("Analyzing %5d/%5d reopenings \r" % (reopening_count,
                                                          reopening_total))
    sys.stdout.flush()
    ticket = reopening.name
    # Analyze the reopening by types
    if reopening.reopening_type not in reopen_types:
        reopen_types[reopening.reopening_type] = 0
    reopen_types[reopening.reopening_type] += 1
    # Info of reopened tickets
    if ticket.id not in reopened_ticket_ids:
        reopened_ticket_ids.append(ticket.id)
    # Classify the reopening into predefined categories by
    # looking for some keywords
    categorized = False
    reopening_data = (
        str(reopening.id), reopening.reopening_type, reopening.pre_state,
        str(reopening.fixing_time_spent), str(ticket.name),
        str(ticket.development_time), str(ticket.time_spent),
        ticket.time_spent - ticket.development_time)
    for categ, pattern in CATEG_KEYWORDS.iteritems():
        if not re.search(pattern, reopening.comment, re.M|re.I):
            continue
        reopen_categs[categ].append(reopening_data)
        categorized = True
        break
    # If none of the categories matches, add it to category Others.
    if not categorized:
        if reopening.reopening_type == 'defect' and\
                reopening.pre_state == 'code_completed':
            reopen_categs['4-defect_code_completed'].append(reopening_data)
        else:
            reopen_categs['5-others'].append(reopening_data)

log.info("========== ANALYSIS ==========")
for categ in sorted(reopen_categs.keys()):
    data = reopen_categs[categ]
    log.info('\n%s (%s times)' % (REOPEN_CATEG_DESCRIPTION[categ], len(data)))
    pattern = CATEG_KEYWORDS.get(categ, '')
    if pattern:
        log.info('\t(search with pattern: %s' % pattern)
    if not data:
        log.info('Clean...')
        continue
    # Sort by over time consumed, ticket id desc, reopening id
    data = sorted(
        sorted(sorted(data, key=itemgetter(0)),
               key=itemgetter(4),
               reverse=True),
        key=itemgetter(7),
        reverse=True)
    log.table(data, CATEG_HEADER)

# Count all tickets which was developed by this user
developed_tickets = ForgeTicket.browse([('developer_id', '=', user_id)])
total_estimate = 0
total_user_spent = 0
total_all_spent = 0
ticket_total = len(developed_tickets)
ticket_count = 0
for ticket in developed_tickets:
    ticket_count += 1
    sys.stdout.write("Analyzing %5d/%5d tickets        \r" % (ticket_count,
                                                              ticket_total))
    sys.stdout.flush()
    total_estimate += ticket.development_time
    total_all_spent += ticket.time_spent
    for wh in WorkingHour.browse(
            [('user_id', '=', user_id),
             ('tms_forge_ticket_id', '=', ticket.id)]):
        total_user_spent += wh.duration_hour

log.info("========== GRAND SUMMARY ==========")
log.table([(reopen_type, str(count))
           for reopen_type, count in reopen_types.iteritems()],
          TYPE_HEADER)
reopened_tickets_count = len(reopened_ticket_ids)
summary_reopen_header = [
    'No. of tickets', 'Reopened tickets', 'Reopening times',
    'Reopening rate (%)', 'Reopening times/ticket']
summary_reopen_content = [(
    str(ticket_total),
    str(reopened_tickets_count),
    str(reopening_total),
    '%.2f' % (1.0 * reopened_tickets_count / ticket_total * 100),
    '%.2f' % (1.0 * reopening_total / reopened_tickets_count))]
log.table(summary_reopen_content, summary_reopen_header)
summary_time_header = [
    'Total estimate (h)', 'Total TS - user (h)', 'Total TS - team (h)',
    'User Efficiency (%)', 'Team Efficiency (%)']
summary_time_content = [(
    str(total_estimate), str(total_user_spent), str(total_all_spent),
    '%.2f' % (1.0 * total_estimate / total_user_spent * 100),
    '%.2f' % (1.0 * total_estimate / total_all_spent * 100))]
log.table(summary_time_content, summary_time_header)
