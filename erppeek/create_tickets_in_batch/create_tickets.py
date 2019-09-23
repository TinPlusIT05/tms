#!/usr/bin/env python
# -*- coding: utf-8 -*-
import click
import csv
import erppeek
from trobz.log import init_logger, logger
import sys


log = logger('run')
init_logger(colored=True, formatter='simple')


class Ticket:

    def __init__(self, client, line):
        self.client = client
        self.line = line

        self.functional_block_id = None
        self.summary = None
        self.workload_char = None
        self.milestone_id = None
        self.description = None
        self.owner_id = None
        self.reporter_id = None
        self.project_id = None
        self.activity_id = None
        self.customer_id = None

        # Only case when we should use this script
        self.ticket_type = 'initial_project'
        self.quotation_approved = False

    def to_vals(self):
        vals = {
            'tms_functional_block_id': self.functional_block_id,
            'summary': self.summary,
            'workload_char': self.workload_char,
            'milestone_id': self.milestone_id,
            'description': self.description,
            'owner_id': self.owner_id,
            'reporter_id': self.reporter_id,
            'project_id': self.project_id,
            'tms_activity_id': self.activity_id,
            'customer_id': self.customer_id,
            'ticket_type': self.ticket_type,
            'quotation_approved': self.quotation_approved
        }

        for k, v in vals.iteritems():
            if v is None:
                log.warning('Tickets in line %s has no value for field %s',
                            self.line,
                            self.k)
        return vals

    def create(self, confirm=True):
        SupportTicket = self.client.model('tms.support.ticket')
        s = SupportTicket.create(self.to_vals())
        log.info('Ticket for line %s created with id %s', self.line, s.id)

        if s.button_create_forge_ticket():
            log.info("Forge ticket created")
            dev_workload = round(s.workload * 8 / 1.2)
            s.tms_forge_ticket_id.development_time = dev_workload
        if confirm:
            click.confirm('Please check the support and forge ticket '
                          'before continuing. All good?', abort=True)
        return s


def read_tickets_data(client, ticket_file):
    client = erppeek.Client.from_config(client)

    log.info('client: %s', client)

    SupportTicket = client.model('tms.support.ticket')
    ForgeTicket = client.model('tms.forge.ticket')
    User = client.model('res.users')
    Project = client.model('tms.project')
    Milestone = client.model('tms.milestone')
    FuncionalBlock = client.model('tms.functional.block')
    Activity = client.model('tms.activity')
    Partner = client.model('res.partner')

    r = csv.reader(open(ticket_file, 'r'))
    r.next()  # header

    tickets = []
    i = 2
    for l in r:
        t = Ticket(client, i)
        try:
            fb_name = l[0]
            milestone_number = l[3]
            project_name = l[7]

            fb_id = FuncionalBlock.get([('name', '=', fb_name)]).id
            project_id = Project.get([('name', '=', project_name)]).id

            milestone_id = Milestone.get([('number', '=', milestone_number),
                                          ('project_id', '=', project_id)]).id
            customer_id = Partner.get([('name', '=', l[9])])

            t.functional_block_id = fb_id
            t.summary = l[1]
            t.workload_char = l[2] and float(l[2]) or 0
            t.milestone_id = milestone_id
            t.description = l[4]
            t.owner_id = User.get([('login', '=', l[5])]).id
            t.reporter_id = User.get([('login', '=', l[6])]).id
            t.project_id = project_id
            t.activity_id = Activity.get([('name', '=', l[8])]).id
            t.customer_id = customer_id
        except Exception as e:
            log.error("Error when reading data in line %s.", i)
            log.error("A related record is probably missing in TMS")
            log.error(e)
            raise

        tickets.append(t)
        i += 1
    return tickets


def create_tickets(support_tickets):
    confirm = True
    for t in support_tickets:
        t.create(confirm=confirm)
        confirm = False
    log.info("SUCCESS: all support tickets created.")
    return True


@click.command()
@click.option('-c', '--client', default='tms-integration',
              help='Name of the client in erppeek.ini')
@click.argument('filename', default='tickets_data.csv')
def run(client, filename):

    support_tickets = read_tickets_data(client, filename)
    create_tickets(support_tickets)

if __name__ == '__main__':
    run()
