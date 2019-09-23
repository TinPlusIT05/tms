# -*- encoding: UTF-8 -*-
from openerp import api, models, fields
from openerp.tools.translate import _


class res_partner(models.Model):
    _inherit = "res.partner"

    related_user_id = fields.Many2one('res.users', string='Related User')

    @api.model
    def default_get(self, field_list):
        res = super(res_partner, self).default_get(field_list)
        res.update({
            'user_id': self._uid,
        })
        return res

    @api.multi
    def write(self, vals):
        email = vals.get('email', '')
        if email:
            vals['email'] = email.lower()
        if 'is_employer' in self._context:
            is_employer = self._context.get('is_employer')
            user_id = self._context.get('user_id', False)
            if is_employer:
                partner_obj = self._context.get('old_related_partner_obj')
                if partner_obj:
                    partner_obj.write({'related_user_id': False})
                employer_obj = self._context.get('old_employer_obj')
                if employer_obj:
                    return self
            if user_id:
                vals.update({'related_user_id': user_id})
        return super(res_partner, self).write(vals)

    @api.model
    def create(self, vals):
        employer_id = self._context.get('no_create_partner', False)
        email = vals.get('email', '')
        if email:
            vals['email'] = email.lower()
        if employer_id:
            employer_obj = self.browse(employer_id)
            employer_obj.write({'email': vals.get('email', '')})
            return employer_obj
        return super(res_partner, self).create(vals)

    @api.constrains('email', 'website', 'is_company')
    def _check_primary_key_web_email(self):
        if self.is_company:
            duplicate = self.search_count(
                [('website', '=', self.website), ('is_company', '=', True),
                 ('id', '!=', self.id),
                 '|', ('active', '=', True), ('active', '=', False)])
            if duplicate:
                raise ValueError(
                    _('A company already exists with this website.'))
        else:
            duplicate = self.search_count(
                [('email', '=', self.email), ('is_company', '=', False),
                 ('id', '!=', self.id),
                 '|', ('active', '=', True), ('active', '=', False)])
            if duplicate:
                raise ValueError(
                    _('A contact already exists with this email.'))

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            code = record.country_id and record.country_id.code or ''
            # Display Country Code
            if code:
                name = "%s [%s]" % (record.name, code)

            # change the name display of the recipients to "{name} ({email})"
            if self._context.get('show_email') and record.email:
                name = "%s (%s)" % (name, record.email)

            res.append((record.id, name))
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
