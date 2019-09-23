from openerp import models, fields, api


class calendar_event(models.Model):
    _inherit = 'calendar.event'

    @api.model
    def _models_get(self):
        models = self.env['ir.model'].search([])
        real_models = []
        for m in models:
            model = m.model
            try:
                # try to get env of object
                model_env = self.env[model]
                # if has attribute _auto => Model Object
                auto = getattr(model_env, '_auto')
                transient = getattr(model_env, '_transient')
                # it should be auto and not transient
                if auto and not transient:
                    real_models.append(m)
            except:
                pass
        return [(model.model, model.name)
                for model in real_models]

    description = fields.Html('Description')
    resource_id = fields.Reference(string='Resource', selection='_models_get')

calendar_event()
