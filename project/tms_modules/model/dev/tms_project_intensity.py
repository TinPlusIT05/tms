from openerp import api, models, fields


class TmsProjectIntensity(models.Model):

    _name = 'tms.project.intensity'
    _description = 'TMS Project Intensity'

    name = fields.Char('Name')
    min_tk = fields.Integer('Min')
    max_tk = fields.Integer('Max')

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = "%s: %s-%s tickets (Support or Forge) in 2 months" % \
                (record.name, record.min_tk, record.max_tk)
            res.append((record.id, name))
        return res
