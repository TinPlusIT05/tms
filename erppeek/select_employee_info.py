#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
import calendar
from datetime import *
from dateutil.relativedelta import *
import erppeek
import sys
import pprint
from trobz.log import init_logger, logger

init_logger(colored=True, formatter='simple')


def _add_capacity_info(my_key, my_dict, capacity, productivity):
    if my_key in my_dict:
        my_dict[my_key]['capacity'] += capacity.production_rate/100
        my_dict[my_key]['productivity'] += productivity
        my_dict[my_key]['count'] += 1
    else:
        my_dict[my_key] = {
            'capacity': capacity.production_rate/100,
            'productivity': productivity,
            'count': 1
        }
    return


def str_ratio(productivity, capacity):
    color = 'green'
    if capacity == 0:
        ratio = "na"
        color = 'white'
    else:
        ratio = productivity / capacity
        if ratio < 0.6:
            color = 'red'
        elif ratio < 0.9:
            color = 'yellow'
        ratio = "%s%%" % round(ratio * 100)
    return "{%s|B}%s{/}" % (
        color, ratio
    )


@click.command()
@click.argument('client', default='tms-integration')
@click.option('--date-to',
              help="If date_to is not set, past Saturday will be used.")
@click.option('--date-from',
              help="If date_from is not set, date_to - 7 days  will be used.")
@click.option('--order-by', type=click.Choice(['job', 'team', 'name']),
              default="team")
def run(client, date_to, date_from, order_by):
    '''
    Analyze capacity vs productivity, dates in format yyyy-mm-dd.
    '''

    log = logger('Employee Info')

    client = erppeek.Client.from_config(client)

    if date_to:
        date_to = datetime.strptime(date_to, '%Y-%m-%d')
    else:
        date_to = (datetime.now() +
                   relativedelta(weekday=calendar.SATURDAY) +
                   relativedelta(days=-7))

    if date_from:
        date_from = datetime.strptime(date_from, '%Y-%m-%d')
    else:
        date_from = date_to + relativedelta(days=-7)

    duration = (date_to - date_from).days
    work_hours = 8 * duration * 20 / 30
    duration_str = "From %s to %s" % (
        date_from.strftime('%Y-%m-%d'),
        date_to.strftime('%Y-%m-%d'))

    log.info("Analysis: " + duration_str)

    Project = client.model('tms.project')
    Users = client.model('res.users')
    Employee = client.model('hr.employee')
    Capacity = client.model('hr.employee.capacity')
    Ticket = client.model('tms.forge.ticket')

    Partner = client.model('res.partner')

    projects = Project.browse([('active', 'in', (True, False))])

    employees = Employee.browse([])

    capacities = Capacity.browse([('employee_id.active', '=', True)])

    capacity_dict = {}

    for c in capacities:
        employee_id = c.employee_id.name
        if employee_id in capacity_dict:
            if c.starting_date < capacity_dict[employee_id].starting_date:
                continue
        capacity_dict[employee_id] = c

    log.info("%s active Employee Capacities.", len(capacity_dict))

    tickets = Ticket.browse([
        ('completion_date', '>=', date_from.strftime('%Y-%m-%d')),
        ('completion_date', '<=', date_to.strftime('%Y-%m-%d'))])

    productivity_dict = {}
    for t in tickets:
        employee_id = t.developer_id.employee_id.name
        if employee_id in productivity_dict:
            productivity_dict[employee_id] += t.development_time
        else:
            productivity_dict[employee_id] = t.development_time

    # Check missing capacities
    for employee in employees:
        if 'Technical' in employee.job_id.name:
            if employee.name not in capacity_dict:
                log.warning("%s does not have a capacity set.", employee.name)

    # Measure total, team capacities, job capacities
    total_capacity = 0
    total_productivity = 0
    team_capacity = {}
    job_capacity = {}

    capacity_employee_lines = []

    for k, c in capacity_dict.iteritems():
        job = c.employee_id.job_id.name
        team = c.employee_id.team_id.name
        capa = c.production_rate / 100 * work_hours
        productivity = productivity_dict.get(k, 0)

        capacity_employee_lines.append([
            team,
            k,
            job,
            str(round(c.production_rate * 8 / 100, 1)),
            str(capa),
            str(productivity),
            str_ratio(productivity, capa)
        ])

        total_capacity += c.production_rate/100
        total_productivity += productivity
        _add_capacity_info(job, job_capacity, c, productivity)
        _add_capacity_info(team, team_capacity, c, productivity)

    log.separator("Analysis per employee %s" % duration_str)
    capacity_employee_header = [
        "Team", "Employee", "Job", "Daily Capacity",
        'Capacity', 'Productivity',
        "Ratio"]

    def getKey(item):
        if order_by == 'team':
            return (item[0], item[1])
        elif order_by == 'name':
            return (item[1], item[2], item[0])
        elif order_by == 'job':
            return (item[2], item[0], item[1])
        else:
            raise "Order by not recognized"

    log.table(sorted(capacity_employee_lines, key=getKey),
              capacity_employee_header, )

    def getOrderGroup(item):
        return item[0]

    def _log_result(name, results):

        header = [name, 'Daily Capacity', 'Technical Members',
                  'Average Capacity',
                  'Capacity', 'Productivity',
                  "Ratio"]

        result_list = []
        for k, v in results.iteritems():
            capa = v['capacity'] * work_hours
            result_list.append([
                k,
                str(v['capacity']),
                str(v['count']),
                str(round(capa / v['count'], 1)),
                str(capa),
                str(v['productivity']),
                str_ratio(v['productivity'], capa)])

        log.separator("Analysis per %s %s " % (name, duration_str))
        log.table(sorted(result_list, key=getOrderGroup), header)

    _log_result("Job", job_capacity)
    _log_result("Team", team_capacity)

    log.separator("Overall " + duration_str)
    header = [
        "Daily Capacity",
        "Technical Members",
        "Average Capacity in Technical positions",
        "Capacity",
        "Productivity",
        "Ratio"]
    results = [[
        str(total_capacity * 8),
        str(len(capacity_dict)),
        str(round(total_capacity * 8 / len(capacity_dict), 2)),
        str(total_capacity * work_hours),
        str(total_productivity),
        str_ratio(total_productivity, total_capacity * work_hours)
    ]]

    log.table(results, header)

    log.info("Daily Capacity reflects a ratio to working days. "
             "For instance a capacity of 12 represents 12 days of workload "
             "can be produced within 1 working day.")
    log.info("The columns 'Capaciy', 'Productivity' and 'Ratio' are calculated"
             " for the period of analysis: %s" % duration_str)

if __name__ == '__main__':
    run()
