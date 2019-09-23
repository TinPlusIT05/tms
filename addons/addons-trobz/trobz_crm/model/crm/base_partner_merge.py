# -*- coding: utf-8 -*-
from openerp import models, fields, api


def is_integer_list(ids):
    return all(isinstance(i, (int, long)) for i in ids)


class MergePartnerAutomatic(models.TransientModel):
    """
        The idea behind this wizard is to create a list of potential partners
        to merge. We use two objects, the first one is the wizard for the
        end-user.
        And the second will contain the partner list to merge.
    """
    _inherit = 'base.partner.merge.automatic.wizard'

    exclude_is_company = fields.Boolean('Is Company')

    def _generate_query(self, fields, this, maximum_group=100):
        sql_fields = []
        for field in fields:
            if field in ['email', 'name']:
                sql_fields.append('lower(%s)' % field)
            elif field in ['vat']:
                sql_fields.append("replace(%s, ' ', '')" % field)
            else:
                sql_fields.append(field)

        group_fields = ', '.join(sql_fields)

        filters = []
        if this.exclude_is_company:
            filters.append(('is_company', '<>', 'True'))
        for field in fields:
            if field in ['email', 'name', 'vat']:
                filters.append((field, 'IS NOT', 'NULL'))

        criteria = ' AND '.join('%s %s %s' % (field, operator, value)
                                for field, operator, value in filters)

        text = [
            "SELECT min(id), array_agg(id)",
            "FROM res_partner",
        ]

        if criteria:
            text.append('WHERE %s' % criteria)

        text.extend([
            "GROUP BY %s" % group_fields,
            "HAVING COUNT(*) >= 2",
            "ORDER BY min(id)",
        ])

        if maximum_group:
            text.extend([
                "LIMIT %s" % maximum_group,
            ])
        return ' '.join(text)

    @api.multi
    def start_process_cb(self):
        """
        Start the process.
        *Compute the selected groups (with duplication)
        *If the user has selected the 'exclude_XXX' fields, avoid the partners.
        """
        assert is_integer_list(self.ids)

        context = dict(self._context or {}, active_test=False)
        this = self and self[0]
        groups = self.with_context(context)._compute_selected_groupby(this)
        query = self.with_context(context)._generate_query(
            groups, this, this.maximum_group)
        self.with_context(context)._process_query(query)

        return this.with_context(context)._next_screen()
