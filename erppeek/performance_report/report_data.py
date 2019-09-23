#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Usage:
# $ python generate_performance_report.py tms-integration 2016-01-01 2016-01-30

from datetime import datetime
import sys

import erppeek
import profitability_data
from trobz.log import logger
import working_hours_data


TRAINEE_JOB_IDS = [
    6,  # Technical Consultant (Trainee)
    11,   # Functional Consultant (Trainee)
    14,  # System Admin (Trainee)
    26,  # Technical Expert (Trainee)
]


def to_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")


class Project:

    def __init__(self, vals, team_dict, owner_id):
        self.log = logger('Project')
        self.id = vals['id']
        self.name = vals['name']
        self.owner_id = owner_id
        if not vals['team_id']:
            self.log.warning('Team not defined for project %s.', self.name)
        TEAM_JC_ODOO = 10
        self.team_id = team_dict[
            vals['team_id'] and vals['team_id'][0] or TEAM_JC_ODOO]


class ReportData:

    def get_employee(self, employee_id):
        return self.employee_dict[employee_id]

    def get_project(self, project_id):
        return self.project_dict[project_id]

    def get_user(self, user_id):
        return self.user_dict[user_id]

    def get_activity(self, activity_id):
        return self.activity_dict[activity_id]

    def _init_contract_dict(self):
        contract_dict = {}
        for c in self.contracts:
            employee_id = c.employee_id.id
            if contract_dict.get(employee_id, False):
                c_list = contract_dict[employee_id]
                contract_dict[employee_id].append(c)
            else:
                contract_dict[employee_id] = [c]
        return contract_dict

    def team_name(self, team_id):
        team = self.team_dict.get(team_id, False)
        if team:
            team_name = team.name
        else:
            self.log.warning("Unknown team with id %s", team_id)
            team_name = str(team_id)
        return team_name

    def get_contract(self, employee_id, current_date):
        contracts = self.contract_dict[employee_id]
        for c in contracts:
            if (to_date(c.date_start) <= to_date(current_date) and
                (not c.date_end or
                 to_date(c.date_end) >= to_date(current_date))):
                return c
        self.log.warning("Employee ID %s has no contract at date  %s",
                         employee_id, current_date)

        # Order by project time spent
        contracts.sort(key=lambda element: element.date_start)
        return contracts[-1]

    def is_trainee_trial(self, employee_id, current_date):
        current_contract = self.get_contract(employee_id, current_date)
        return (current_contract.job_id.id in TRAINEE_JOB_IDS or
                current_contract.is_trial)

    def __init__(self, client, server, database, username, password,
                 date_from, date_to):
        self.log = logger('ReportData')
        self.date_from = date_from
        self.date_to = date_to
        self.dt_from = datetime.strptime(date_from, '%Y-%m-%d')
        self.dt_to = datetime.strptime(date_to, '%Y-%m-%d')
        self.duration = (self.dt_to - self.dt_from).days

        if client != None:
            self.client = erppeek.Client.from_config(client)
        else:
            self.client = erppeek.Client(
                server, database, username, password)

        all = ['|', ('active', '=', True), ('active', '=', False)]

        self.log.info("Load teams")
        self.teams = self.client.model('hr.team').browse([])
        self.team_dict = {t.id: t for t in self.teams}

        self.log.info("Load employees")
        self.employees = self.client.model('hr.employee').browse(all)
        self.employee_dict = {e.id: e for e in self.employees}
        self.team_filter = None

        self.log.info("Load contracts")
        self.contracts = self.client.model('hr.contract').browse([])
        self.contract_dict = self._init_contract_dict()
        self.log.debug(self.contract_dict)

        self.log.info("Load users")
        self.users = self.client.model('res.users').browse(all)
        self.user_dict = {u.id: u for u in self.users}

        self.log.info("Load projects")
        project_fields = ["id", "name", "owner_id", 'team_id']
        projects = self.client.model('tms.project').read(all,
                                                         fields=project_fields)
        self.projects = {
            Project(p, self.team_dict,
                    self.get_user(p['owner_id'][0])) for p in projects
            if p['owner_id']}
        # self.projects = self.fix_projects(projects)
        self.project_dict = {p.id: p for p in self.projects}

        self.log.info("Load activities")
        self.activities = self.client.model('tms.activity').browse(all)
        self.activity_dict = {a.id: a for a in self.activities}

        self.log.info("Load Dedicated Resources")
        DedicatedResource = self.client.model('hr.dedicated.resource.contract')
        self.dedicated_resources = DedicatedResource.browse([])

        self.log.info("Prepare Working Hours Data")
        self.wh_data = working_hours_data.WorkingHoursData(self)

        self.log.info("Prepare Profitability Data")
        self.profitability_data = profitability_data.ProfitabilityData(self)
