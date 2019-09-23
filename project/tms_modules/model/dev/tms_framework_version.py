# -*- encoding: utf-8 -*-
from openerp import api, models, fields


class tms_framework_version(models.Model):

    _name = "tms.framework.version"
    _description = "Framework Version"
    _order = "name"

    # Comlumns
    name = fields.Char("Name", required=True)
    project_type_id = fields.Many2one('tms.project.type', 'Project Type')

    _sql_constraints = [
        ('tms_project_framework_name_unique',
         'unique(name)',
         "The name must be unique!")
    ]

    @api.multi
    def name_get(self):
        result = []
        for version in self:
            if version.project_type_id:
                result.append(
                    (version.id, u"{0} {1}".format(
                        version.project_type_id.name, version.name))
                )
            else:
                result.append(
                    (version.id, u"{0}".format(version.name))
                )
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Override function:
        Allow to search by framework version and project type
        """
        if not args:
            args = []
        recs = self.search(args)
        ids = recs.ids
        if name:
            sql = """
            SELECT a.id
            FROM tms_framework_version a
            JOIN tms_project_type p
            ON a.project_type_id = p.id
            WHERE p.name || ' - ' || a.name %s '%%%s%%'
            """ % (operator, name.replace("'", ""))
            self._cr.execute(sql)
            framework_ids = [framework_id[0]
                             for framework_id in self._cr.fetchall()]
            ids = list(set(ids).intersection(framework_ids))
            recs = self.browse(ids)

        return recs.name_get()
