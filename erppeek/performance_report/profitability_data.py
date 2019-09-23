from datetime import datetime
from trobz.log import logger
from pudb import set_trace


SUPPORT_ACTIVITY_TYPE = 3

TROBZ_ACTIVITY_TYPES = [7,  # Prospection and Demo
                        9,  # R&D
                        15,  # Internal tools
                        20,  # Days off
                        22,  # Compensation
                        26,  # Trobz Allocation
                        ]
TEAM_ACTIVITY_TYPES = [29,  # Team Allocation
                       ]


class Profitability:

    def __init__(self, vals):
        self.log = logger('Profitability')

        project = vals.get('project', None)
        if project:
            self.team_id = project.team_id
            self.project_name = project.name
        else:
            self.team_id = vals.get('team_id', None)
            self.project_name = vals.get('project_name', None)

        self.ticket_workload = vals.get('ticket_workload', 0)
        self.ticket_time_spent = vals.get('ticket_time_spent', 0)
        self.support_budget = vals.get('support_budget', 0)
        self.dedicated_resource = vals.get('dedicated_resource', 0)
        self.project_time_spent = vals.get('project_time_spent', 0)
        self.team_time_spent = vals.get('team_time_spent', 0)
        self.trobz_time_spent = vals.get('trobz_time_spent', 0)
        self.project_weight = vals.get('project_weight', 0)

    @classmethod
    def group(cls, profitability):
        ''' Second constructor
        '''
        vals = {
            'team_id': profitability.team_id,
            'project_name': profitability.project_name,
            'ticket_workload': profitability.ticket_workload,
            'ticket_time_spent': profitability.ticket_time_spent,
            'support_budget': profitability.support_budget,
            'dedicated_resource': profitability.dedicated_resource,
            'project_time_spent': profitability.project_time_spent,
            'team_time_spent': profitability.team_time_spent,
            'trobz_time_spent': profitability.trobz_time_spent,
            'project_weight': profitability.project_weight,
        }
        return cls(vals)

    def group_add(self, profitability):
        self.ticket_workload += profitability.ticket_workload
        self.ticket_time_spent += profitability.ticket_time_spent
        self.support_budget += profitability.support_budget
        self.dedicated_resource += profitability.dedicated_resource
        self.project_time_spent += profitability.project_time_spent
        self.team_time_spent += profitability.team_time_spent
        self.trobz_time_spent += profitability.trobz_time_spent
        self.project_weight += profitability.project_weight

    def total_budget_man_day(self):
        return (1.4 * (self.ticket_workload +
                       self.dedicated_resource) +
                self.support_budget)

    def project_profitability(self):
        budget = self.total_budget_man_day()
        return budget and (budget - self.project_time_spent) / budget or 0

    def team_profitability(self):
        budget = self.total_budget_man_day()
        project_team_time_spent = (self.project_time_spent +
                                   self.team_time_spent)
        return budget and (budget - project_team_time_spent) / budget or 0

    def trobz_profitability(self):
        budget = self.total_budget_man_day()
        project_team_trobz_time_spent = (self.project_time_spent +
                                         self.team_time_spent +
                                         self.trobz_time_spent)
        return (budget and
                (budget - project_team_trobz_time_spent) / budget or 0)


class Ticket:

    def __init__(self, ticket_val):
        self.id = ticket_val["id"]
        self.project_id = ticket_val["project_id"][0]
        self.project_name = ticket_val["project_id"][1]
        self.workload = ticket_val["workload"]
        self.state = ticket_val["state"]
        self.time_spent = ticket_val["time_spent"]


class ProfitabilityData:

    def _init_profitability_dict(self):
        profitability_dict = {}
        for project in self.report_data.projects:
            profitability_dict[project.id] = Profitability(
                {'project': project})
        return profitability_dict

    def _set_ticket_workload_produced_time_spent(self):
        for ticket in self.tickets:
            self.profitability_dict[ticket.project_id].ticket_workload = \
                self.profitability_dict[ticket.project_id].ticket_workload \
                + ticket.workload
            self.profitability_dict[ticket.project_id].ticket_time_spent = \
                self.profitability_dict[ticket.project_id].ticket_time_spent \
                + ticket.time_spent / 8
        return True

    def _set_support_budget(self):
        date_from = str(self.report_data.dt_from.date())
        date_to = str(self.report_data.dt_to.date())

        for activity in self.report_data.activities:
            activity_date_start = activity.date_start
            activity_date_end = activity.date_end

            if (activity_date_start or activity_date_start > date_to or
                activity_date_end < date_from or
                    activity.analytic_secondaxis_id.id != SUPPORT_ACTIVITY_TYPE):
                continue

            date_1 = max(activity_date_start, date_from)
            date_2 = min(activity_date_end, date_to)
            duration = max(0, (date_2 - date_1).days) * 20 / 30

            if duration == 0:
                continue
            self.profitability_dict[activity.project_id.id].support_budget \
                += activity.day_sold_dev / 30 * duration
        return True

    def _set_time_spent(self):
        trobz_time_spent = {}
        team_time_spent = {}
        project_time_spent = {}
        for wh in self.report_data.wh_data.whs:
            activity = self.report_data.get_activity(wh.activity_id)
            if not wh.employee_id:
                self.log.warning("Skipping working hours (missing employee)"
                                 ": %s", wh.id)
                continue
            employee = self.report_data.get_employee(wh.employee_id)

            if not employee.team_id:
                raise Exception("DATA ERROR: Employee %s missing a team" %
                                employee.name)

            if self.report_data.is_trainee_trial(wh.employee_id, wh.date):
                continue

            employee_team = employee.team_id.id

            if activity.analytic_secondaxis_id.id in TROBZ_ACTIVITY_TYPES:
                trobz_time_spent[employee_team] = (
                    trobz_time_spent.get(employee_team, 0) +
                    (wh.duration_hour / 8))

            elif activity.analytic_secondaxis_id.id in TEAM_ACTIVITY_TYPES:
                team_time_spent[employee_team] = (
                    team_time_spent.get(employee_team, 0) +
                    (wh.duration_hour / 8))
            else:
                try:

                    project = self.report_data.get_project(wh.project_id)
                    project_team_id = project.team_id.id
                    self.profitability_dict[wh.project_id].project_time_spent \
                        += (wh.duration_hour / 8)
                    project_time_spent[project_team_id] = (
                        project_time_spent.get(project_team_id, 0) +
                        (wh.duration_hour / 8))
                except Exception as e:
                    set_trace()
                    raise

        missing_whs = self.report_data.wh_data.missing_whs
        for mwh in missing_whs:
            employee = self.report_data.get_employee(mwh)

            date_to = self.report_data.date_to
            if self.report_data.is_trainee_trial(mwh, date_to):
                # FIXME: This won't be necessary once the missing working
                # hours ignore the trainees and trials
                # Then, we won't need anymore the approximation of trainee
                # trial only on the last day
                continue

            if not employee.team_id:
                raise Exception("DATA ERROR: Employee %s missing a team" %
                                employee.name)
            employee_team = employee.team_id.id
            missing_duration = (missing_whs[mwh] / 8)
            if employee_team in team_time_spent:
                team_time_spent[employee_team] += missing_duration
            else:
                team_time_spent[employee_team] = missing_duration

        for project in self.profitability_dict:
            p = self.profitability_dict[project]
            try:
                team = p.team_id.id
                project_weight = (
                    project_time_spent.get(team, False) and
                    p.project_time_spent / project_time_spent[team] or 0)
                p.project_weight = project_weight
                p.trobz_time_spent = trobz_time_spent.get(
                    team, 0) * project_weight
                p.team_time_spent = team_time_spent.get(
                    team, 0) * project_weight
            except Exception as e:
                set_trace()
                raise

    def _set_dedicated_resource(self):
        date_from = self.report_data.dt_from
        date_to = self.report_data.dt_to

        dr_team = {}
        for r in self.report_data.dedicated_resources:

            r_start_date = datetime.strptime(r.start_date, "%Y-%m-%d")
            r_end_date = (
                r.end_date and datetime.strptime(r.end_date, "%Y-%m-%d") or
                date_to)

            date_1 = max(r_start_date, date_from)
            date_2 = min(r_end_date, date_to)
            duration = max(0, (date_2 - date_1).days) * 20 / 30

            if duration == 0:
                continue

            employee = self.report_data.get_employee(r.employee_id.id)
            if not employee.team_id:
                raise Exception("DATA ERROR: Employee %s missing a team" %
                                employee.name)
            employee_team = employee.team_id.id

            if employee_team in dr_team:
                dr_team[employee_team] += duration
            else:
                dr_team[employee_team] = duration

        for project in self.profitability_dict:
            p = self.profitability_dict[project]
            team_id = p.team_id.id
            p.dedicated_resource = dr_team.get(team_id, 0) * p.project_weight

    def write_trobz_profitability(self, worksheet_writer):

        header = ['Ticket Workload Produced',
                  'Ticket Time Spent',
                  'Support Budget',
                  'Dedicated Resource',
                  'Total Budget Man days',
                  'Project Time spent',
                  'Project Profitability',
                  'Team Time Spent',
                  'Team Profitability',
                  'Trobz Time Spent',
                  'Trobz Profitability',
                  ]

        trobz = None
        for project in self.profitability_dict:
            p = self.profitability_dict[project]
            if trobz:
                trobz.group_add(p)
            else:
                trobz = Profitability.group(p)

        report = worksheet_writer.report

        rows = [[
                [trobz.ticket_workload, report.styleNumber],
                [trobz.ticket_time_spent, report.styleNumber],
                [trobz.support_budget, report.styleNumber],
                [trobz.dedicated_resource, report.styleNumber],
                [trobz.total_budget_man_day(), report.styleNumber],
                [trobz.project_time_spent, report.styleNumber],
                [trobz.project_profitability(), report.stylePercentage],
                [trobz.team_time_spent, report.styleNumber],
                [trobz.team_profitability(), report.styleBoldPercentage],
                [trobz.trobz_time_spent, report.styleNumber],
                [trobz.trobz_profitability(), report.stylePercentage],
                ]
                ]

        worksheet_writer.write("Trobz Profitability",
                               header, rows, first_col=2)

        return True

    def write_team_profitability(self, worksheet_writer):
        # TODO: Today, it is by DTM due to missing Team at project level

        header = ['Team',
                  'Ticket Workload Produced',
                  'Ticket Time Spent',
                  'Support Budget',
                  'Dedicated Resource',
                  'Total Budget Man days',
                  'Project Time spent',
                  'Project Profitability',
                  'Team Time Spent',
                  'Team Profitability',
                  'Trobz Time Spent',
                  'Trobz Profitability',
                  ]

        team_dict = {}
        for project in self.profitability_dict:
            p = self.profitability_dict[project]
            if p.team_id in team_dict:
                team_dict[p.team_id].group_add(p)
            else:
                team_dict[p.team_id] = Profitability.group(p)

        rows = []

        report = worksheet_writer.report

        for team in team_dict:
            p = team_dict[team]

            if (self.report_data.team_filter and
                    p.team_id.id != self.report_data.team_filter):
                continue

            row = [
                [self.report_data.team_name(p.team_id.id), report.styleText],
                [p.ticket_workload, report.styleNumber],
                [p.ticket_time_spent, report.styleNumber],
                [p.support_budget, report.styleNumber],
                [p.dedicated_resource, report.styleNumber],
                [p.total_budget_man_day(), report.styleNumber],
                [p.project_time_spent, report.styleNumber],
                [p.project_profitability(), report.stylePercentage],
                [p.team_time_spent, report.styleNumber],
                [p.team_profitability(), report.styleBoldPercentage],
                [p.trobz_time_spent, report.styleNumber],
                [p.trobz_profitability(), report.stylePercentage],
            ]
            rows.append(row)

        # Order by project time spent
        rows.sort(key=lambda element: element[6][0])
        worksheet_writer.write("Team Profitability", header, rows, first_col=1)

        return True

    def write_project_profitability(self, worksheet_writer):

        header = ['Team',
                  'Project',
                  'Ticket Workload Produced',
                  'Ticket Time Spent',
                  'Support Budget',
                  'Dedicated Resource',
                  'Total Budget Man days',
                  'Project Time spent',
                  'Project Profitability',
                  'Team Time Spent',
                  'Team Profitability',
                  'Trobz Time Spent',
                  'Trobz Profitability',
                  ]

        rows = []

        report = worksheet_writer.report

        for project in self.profitability_dict:
            p = self.profitability_dict[project]

            if p.total_budget_man_day() == 0 and p.project_time_spent == 0:

                self.log.debug("Skipping project %s (no ticket produced, no "
                               "time spent)", p.project_name)
                continue

            if (self.report_data.team_filter and
                    p.team_id.id != self.report_data.team_filter):
                continue

            row = [
                [self.report_data.team_name(p.team_id.id), report.styleText],
                [p.project_name, report.styleText],
                [p.ticket_workload, report.styleNumber],
                [p.ticket_time_spent, report.styleNumber],
                [p.support_budget, report.styleNumber],
                [p.dedicated_resource, report.styleNumber],
                [p.total_budget_man_day(), report.styleNumber],
                [p.project_time_spent, report.styleNumber],
                [p.project_profitability(), report.stylePercentage],
                [p.team_time_spent, report.styleNumber],
                [p.team_profitability(), report.styleBoldPercentage],
                [p.trobz_time_spent, report.styleNumber],
                [p.trobz_profitability(), report.stylePercentage],
            ]
            rows.append(row)

        # Order by project time spent
        rows.sort(key=lambda element: element[7][0])
        worksheet_writer.write("Project Profitability",
                               header, rows, first_row=0)

        return True

    def _init_ticket(self):
        SupportTicket = self.report_data.client.model('tms.support.ticket')
        ticket_fields = ["id", "project_id", "workload", "state", "time_spent"]

        # Test Data:
        # 7381 => Staging Delivery Date empty + closing date 24/02/2016
        # 8727: Staging Delivery Date:  06/04/2016 + closing date 13/04
        # test_ticket = 7381

        domain_produced_1 = [
            "|", ('quotation_approved', '=', True),
            ('ticket_type', '=', 'initial_project'),
            ('invc_by_trobz_vn', '=', True),
            ('staging_delivery_date', '>=', self.report_data.date_from),
            ('staging_delivery_date', '<=', self.report_data.date_to),
            # ('id','=',test_ticket)
        ]

        domain_produced_2 = [
            "|", ('quotation_approved', '=', True),
            ('ticket_type', '=', 'initial_project'),
            ('invc_by_trobz_vn', '=', True),
            ('staging_delivery_date', '=', None),
            ('closing_datetime', '>=', self.report_data.date_from),
            ('closing_datetime', '<=', self.report_data.date_to),
            # ('id','=',test_ticket)
        ]

        tickets_1 = SupportTicket.read(domain_produced_1, fields=ticket_fields)
        tickets_2 = SupportTicket.read(domain_produced_2, fields=ticket_fields)

        return [Ticket(t) for t in (tickets_1 + tickets_2)]

    def __init__(self, report_data):
        self.log = logger('ProfitabilityData')
        self.report_data = report_data
        self.profitability_dict = self._init_profitability_dict()

        self.tickets = self._init_ticket()

        self._set_ticket_workload_produced_time_spent()
        self._set_support_budget()
        self._set_time_spent()
        self._set_dedicated_resource()
