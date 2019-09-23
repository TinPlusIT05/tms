#!/usr/bin/env python
# -*- coding: utf-8 -*-

import calendar
import click
from datetime import *
from dateutil.relativedelta import *
import erppeek
import pprint
import sys

import report_writer
from trobz.log import init_logger, logger


init_logger(colored=True, formatter='simple')

HEADER = ['Employee',
          'Average',
          'Team Work',
          'Productivity & Quality',
          'Prioritization & Alignment',
          'Company Commitment',
          'Overall Esimtation',
          'Comments',
          ]


def prepare_rows(log, input_lines, questions):

    rows = []

    for l in input_lines:
        employee_name = l.input_id.appraisal_id.employee_id.name

        new = True
        for r in rows:
            if r['employee'] == employee_name:
                r[l.question_id.id] = l.qualification
                r['comment'] += '\n[%s]%s' % (
                    l.question_id.sequence,
                    l.explanation)
                new = False
        if new:
            rows.append({
                'employee': employee_name,
                l.question_id.id: l.qualification,
                'comment': '%s\n[%s]%s' % (
                    l.input_id.extra_comments,
                    l.question_id.sequence,
                    l.explanation)
            })

    rows.sort(key=lambda x: x['employee'])

    for r in rows:
        r['average'] = (float(sum([r[q.id] for q in questions])) /
                        len(questions))

    rows_log = []
    for r in rows:
        rows_log.append([r['employee'], str(r['average'])] +
                        [str(r[q.id]) for q in questions])
        # +  [r['comment']])

    log.table(rows_log, HEADER)

    return rows


def write_result(log, rows, questions):
    report_filename = 'Appraisal results (%s).xlsx' % (datetime.today())

    log.info('Preparing to writing report %s', report_filename)

    report = report_writer.ReportWriter(report_filename)

    cols = [30, 10, 10, 10, 10, 10, 10, 60]

    rows_report = []

    def get_style(val, low=3.5, high=4.5):
        if val <= low:
            return report.styleNumberLow
        elif val >= high:
            return report.styleNumberHigh
        else:
            return report.styleNumber

    for r in rows:

        rows_report.append([
            [r['employee'], report.styleText],
            [r['average'], get_style(r['average'])]
        ] + [
            [r[q.id], get_style(r[q.id])] for q in questions
        ] + [
            [r['comment'], report.styleText]
        ])

    worksheet = report_writer.WorkSheetWriter(
        report,
        'Results',
        column_widths=cols)

    worksheet.write(
        'Appraisal Results', HEADER, rows_report,
        first_col=0, first_row=0)
    report.close()

    log.info('Report %s complete! all done :)', report_filename)
    return True


@click.command()
@click.argument('client', default='tms-integration')
@click.option('--date-from',
              help="If date_from is not set, date_to - 15 days  will be used.")
@click.option('--date-to',
              help="If date_to is not set, today will be used.")
def run(client, date_from, date_to):
    '''
    Rerports for appraisal results for quarterly bonus based on create_date
    '''
    log = logger('Appraisal')

    APPRAISAL_TEMPLATE = 'Trobz - HR - Quarterly Bonus Appraisal'

    client = erppeek.Client.from_config(client)

    if date_from:
        date_from = datetime.strptime(date_from, '%Y-%m-%d')
    else:
        date_from = datetime.now() + relativedelta(days=-15)

    if date_to:
        date_to = datetime.strptime(date_to, '%Y-%m-%d')
    else:
        date_to = datetime.now()

    InputLines = client.model('hr.appraisal.input.line')
    # Employee = client.model('hr.employee')

    input_lines = InputLines.browse(
        [
            ('create_date', '>=', date_from.strftime('%Y-%m-%d')),
            ('create_date', '<=', date_to.strftime('%Y-%m-%d')),
            ('input_id.appraisal_id.template_evaluator_id.name',
                '=', APPRAISAL_TEMPLATE)],
        # order='input_id.appraisal_id.employee_id.name,question_id.sequence')
        order='input_id,question_id')

    log.info("Found %s input lines.", len(input_lines))

    questions = client.model('hr.appraisal.question').browse(
        [('template_id.name', '=', APPRAISAL_TEMPLATE)],
        order='sequence'
    )

    log.info("Questions:")
    for q in questions:
        log.info("- %s", q.name)

    write_result(log, prepare_rows(log, input_lines, questions), questions)


if __name__ == '__main__':
    run()
