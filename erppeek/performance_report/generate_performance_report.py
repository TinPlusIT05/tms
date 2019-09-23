#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import sys

import click
import erppeek
import report_data
import report_writer
from trobz.log import init_logger, logger


init_logger(colored=True, formatter='simple')


@click.command()
@click.option('-c', '--client',
              help='Name of the client in erppeek.ini')
@click.option('-s', '--server')
@click.option('-db', '--database')
@click.option('-u', '--username')
@click.option('-p', '--password')
@click.argument('date_from')
@click.argument('date_to')
def run(client, server, database, username, password, date_from, date_to):
    '''
    Geneates the performance reports, date must use the format yyyy-mm-dd.
    '''

    log = logger('run')

    log.info('client: %s', client)
    log.info('server: %s', server)
    log.info('database: %s', database)
    log.info('username: %s', username)
    log.info('password: %s', password)
    log.info('date_from: %s', date_from)
    log.info('date_to: %s', date_to)

    my_data = report_data.ReportData(
        client, server, database, username, password, date_from, date_to)

    report_filename = ('performance_report (%s to %s).xlsx' %
                       (date_from, date_to))

    report = report_writer.ReportWriter(report_filename)
    cols = [20, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15]

    def add_sheet(ws='Trobz'):
        worksheet = report_writer.WorkSheetWriter(report, ws,
                                                  column_widths=cols)

        my_data.profitability_data.write_project_profitability(worksheet)
        my_data.profitability_data.write_team_profitability(worksheet)
        my_data.profitability_data.write_trobz_profitability(worksheet)
        my_data.wh_data.write_missing_working_hours(worksheet)

    add_sheet()
    for team_id, team in my_data.team_dict.iteritems():
        my_data.team_filter = team_id
        add_sheet(team.name)

    report.close()
    log.success('Report "%s" generated!', report_filename)

if __name__ == '__main__':
    run()
