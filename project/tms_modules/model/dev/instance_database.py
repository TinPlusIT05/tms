# -*- encoding: utf-8 -*-

from openerp import fields, api, _
from openerp.addons.field_secure import models  # @UnresolvedImport
from openerp.exceptions import Warning


class instance_database(models.SecureModel):

    _name = "instance.database"
    _description = "Instance Database"

    name = fields.Char("Database Name", size=256, required=1)
    password = fields.Secure(string="Password", security="_password_security")
    login = fields.Char("Login", default="admin")
    tms_instance_id = fields.Many2one(
        'tms.instance', string='TMS Instance', select=1, required=1)

    @api.model
    def create(self, vals):
        """
        Override function
        Raise warning in case the current user is not
             Admin or TPM/FC profiles and in the supporters
        """
        instance_env = self.env['tms.instance']
        instance_id = vals.get('tms_instance_id')
        instance = instance_env.browse(instance_id)
        read_update_password = instance_env._check_password_security(instance)
        if not read_update_password:
            raise Warning(_(
                'Only user with Admin profile or user with TPM/FC profiles'
                ' who exists in the supporters'
                ' of the project linked to this instance'
                ' can add/remove/update database recored'))
        return super(instance_database, self).create(vals)

    @api.multi
    def unlink(self):
        """
        Override function
        Raise warning in case the current user is not
             Admin or TPM/FC profiles and in the supporters
        """
        instance_env = self.env['tms.instance']
        for line in self:
            read_update_password = instance_env._check_password_security(
                line.tms_instance_id)
            if not read_update_password:
                raise Warning(_(
                    'Only user with Admin profile or user with TPM/FC profiles'
                    ' who exists in the supporters'
                    ' of the project linked to this instance'
                    ' can add/remove/update database recored'))
        return super(instance_database, self).unlink()

    @api.multi
    def _password_security(self):
        """
        Only allow Admin/TPM or FC update read/update password field.
        """
        instance_env = self.env['tms.instance']
        is_allow = False
        for rec in self:
            if instance_env._check_password_security(rec.tms_instance_id):
                is_allow = True
            else:
                is_allow = False
                break
        return is_allow
