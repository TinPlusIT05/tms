from openerp import models, fields


class tms_ticket_task_type(models.Model):

    _name = "tms.ticket.task.type"
    _description = "TMS Ticket Task Type"

    family = fields.Many2one('tms.ticket.task.type.family', 'Family',
                             required=True)
    name = fields.Char('Name')
    formula = fields.Char('Formula',
                          help="use _a, _b or _c as variable names")
    formula_description = fields.Text('Formula Description')
    formula_parameter = fields.Char('Formula Parameter',
                                    default="{'_a': 0,'_b': 0,'_c': 0}")
    risk = fields.Integer("Risk (%)")
