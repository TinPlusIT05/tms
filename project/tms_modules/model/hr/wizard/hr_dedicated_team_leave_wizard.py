from openerp import fields, models, api
from datetime import date, datetime


MONTH_LIST = [
    ("1-1", "Jan-period 1"),
    ("1-2", "Jan-period 2"),
    ("2-1", "Feb-period 1"),
    ("2-2", "Feb-period 2"),
    ("3-1", "Mar-period 1"),
    ("3-2", "Mar-period 2"),
    ("4-1", "Apr-period 1"),
    ("4-2", "Apr-period 2"),
    ("5-1", "May-period 1"),
    ("5-2", "May-period 2"),
    ("6-1", "Jun-period 1"),
    ("6-2", "Jun-period 2"),
    ("7-1", "Jul-period 1"),
    ("7-2", "Jul-period 2"),
    ("8-1", "Aug-period 1"),
    ("8-2", "Aug-period 2"),
    ("9-1", "Sep-period 1"),
    ("9-2", "Sep-period 2"),
    ("10-1", "Oct-period 1"),
    ("10-2", "Oct-period 2"),
    ("11-1", "Nov-period 1"),
    ("11-2", "Nov-period 2"),
    ("12-1", "Dec-period 1"),
    ("12-2", "Dec-period 2"),
]

CONDITION_LIST = [
    ("AND", "AND"),
    ("OR", "OR")
]


class HrDedicatedTeamLeaveWizard(models.TransientModel):
    _name = 'hr.dedicated.team.leave.wizard'

    year = fields.Selection(
        string="Year",
        selection=[(y, '%s' % y) for y in range(2010, 2051)],
        default=lambda self: date.today().year,
        required=True,
    )
    month = fields.Selection(
        string="Month-Period",
        selection=MONTH_LIST,
        default=MONTH_LIST[0][0],
        required=True,
    )
    team_ids = fields.Many2many(
        "hr.team",
        string="Team",
        rel="team_dedicated_rel",
        id1="dedicated_id",
        id2="team_id"
    )
    team_leader_ids = fields.Many2many(
        "hr.employee",
        rel="team_leader_dedicated_rel",
        string="Team Leader",
        id1="dedicated_id",
        id2="parent_id"
    )
    leave_manager_ids = fields.Many2many(
        "hr.employee",
        rel="leave_manager_dedicated_rel",
        string="Leave Manager",
        id1="dedicated_id",
        id2="leave_manager_id"
    )

    condition_1 = fields.Selection(
        string="Condition 1",
        selection=CONDITION_LIST,
    )
    condition_2 = fields.Selection(
        string="Condition 2",
        selection=CONDITION_LIST,
    )

    @api.multi
    def button_print_em_leave_report(self):
        self.ensure_one()

        wizard_input_data = {
            "team_ids": self.team_ids.ids,
            "team_leader_ids": self.team_leader_ids.ids,
            "leave_manager_ids": self.leave_manager_ids.ids,
            "condition_1": self.condition_1,
            "condition_2": self.condition_2,
            "year": self.year,
            "update_to": self.month,
            "model": "hr.dedicated.team.leave.wizard",
        }
        return {
            "datas": wizard_input_data,
            "type": "ir.actions.report.xml",
            "report_name": "report.dedicated.team.leave.xlsx",
            "name":
                u"Dedicated-Team-Leave-{0}-{1}".format(self.year, self.month)
        }
