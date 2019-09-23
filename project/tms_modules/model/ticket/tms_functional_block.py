# -*- encoding: utf-8 -*-
from openerp import api, models, _, fields
from openerp.exceptions import Warning


class tms_functional_block(models.Model):

    _name = "tms.functional.block"
    _description = "Functional Block"
    _order = "name"

    name = fields.Char('Name', size=512, required=True)
    project_ids = fields.Many2many(
        'tms.project', 'tms_functional_block_project_rel',
        'tms_functional_block_id', 'project_id', 'Projects')
    description = fields.Text(string='Description')
    active = fields.Boolean('Active', default=True)

    @api.constrains('name', 'project_ids')
    def check_unique_name_project(self):
        """
        Check Functional Block name should be unique
        """
        sql = """
        SELECT id from tms_functional_block
        WHERE active = 't'
        AND id != %s
        AND LOWER(name) = '%s'
        """ % (self.id, self.name.lower())
        cr = self._cr
        cr.execute(sql)
        res_ids = [x[0] for x in cr.fetchall()]
        if res_ids:
            list_project_name = []
            functional_block_recs = self.browse(res_ids)
            for functional_block in functional_block_recs:
                if functional_block.project_ids:
                    list_project_name.extend(
                        [x.name for x in functional_block.project_ids])
            if not list_project_name:
                raise Warning(_(
                    "The Functional Block '{0}' is already existed".format(
                        self.name)))
            else:
                raise Warning(
                    _("The Functional Block '{0}' is already used by "
                      "a functional for the projects '{1}'".format(
                          self.name, ", ".join(set(list_project_name)))))

    @api.constrains('name', 'project_ids', 'description', 'active')
    def check_tpm_access(self):
        """
        Admin user: full access on functional block
        TPM user: full access on functional block of his project
        """
        user = self.env.user
        tpm_ids = [x.technical_project_manager_id.id for x in self.project_ids]
        if user.group_profile_id and \
                user.group_profile_id.name == \
                'Technical Project Manager Profile'\
                and user.id not in tpm_ids:
            # Current user is the TPM of one of the projects defined on FB
            # TPM cannot create FB without project or for other project
            raise Warning(
                _("Only user with Admin profile can update, "
                  "create or delete a Functional Block which is Global "
                  "(not associated to any project). "
                  "If you need to create a functional block "
                  "for your project, make sure to add a project "
                  "before saving."))

    @api.model
    def create(self, vals):
        """
        Auto update project for FB when it's created from ticket
        """
        context = self._context or {}
        project_id = context.get('project_id_from_ticket', False)
        if project_id:
            vals.update({
                'project_ids': [(4, project_id)]
            })
        return super(tms_functional_block, self).create(vals)
