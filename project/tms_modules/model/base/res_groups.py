# -*- encoding: UTF-8 -*-
from openerp import models, api, fields


class res_groups(models.Model):

    _inherit = "res.groups"

    # Columns
    wh_tickets_required = fields.Boolean(
        string="Working Hours Require Tickets", default=True)
    notif_pref_id = fields.Many2one(
        comodel_name='notification.preferences',
        string='Notification Preferences')
    is_sysadmin = fields.Boolean('Is Sysadmin', default=False)

    @api.multi
    def write(self, vals):
        for rg in self:
            if rg.is_profile and not rg.notif_pref_id \
                    and not vals.get('notif_pref_id'):
                raise Warning(
                    'Forbidden action!',
                    'Please, set a Notification Preference ' +
                    'on the profile!')
            if 'implied_ids' in vals and vals.get('implied_ids', False):
                rg_remove_ids = [
                    x for x in rg.implied_ids.ids
                    if x not in vals.get('implied_ids')[0][2]]
                if not rg_remove_ids or not rg.users:
                    continue
                # update access rights group for user
                sql = '''
                DELETE FROM res_groups_users_rel
                WHERE uid in (''' + ','.join(map(str, [u.id for u in rg.users])) + ''')
                and gid in (''' + ','.join(map(str, rg_remove_ids)) + ''')
                '''
                self._cr.execute(sql)
        return super(res_groups, self).write(vals)
