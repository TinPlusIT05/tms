from openerp import models, fields
from openerp.tools.translate import _
from openerp.addons.base.ir.ir_actions import VIEW_TYPES

# add new view type to action system
VIEW_TYPE = ['tms_audit_board_list', _('TMS Audit Board List')]
VIEW_TYPES.append(VIEW_TYPE)


class IrUiView(models.Model):

    _inherit = "ir.ui.view"

    type = fields.Selection(selection_add=[VIEW_TYPE])
