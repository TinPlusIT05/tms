# -*- encoding: UTF-8 -*-
##############################################################################

from openerp import fields, api
from openerp.addons.field_secure import models  # @UnresolvedImport
import logging
_logger = logging.getLogger(__name__)


AVAILABLE_PRIORITIES = [
    ('0', 'Bad'),
    ('1', 'Below Average'),
    ('2', 'Average'),
    ('3', 'Good'),
    ('4', 'Excellent')
]


class hr_applicant(models.SecureModel):
    _inherit = "hr.applicant"

    salary_expected_secure = fields.Secure(
        string='Expected Salary',
        security="_password_security",
        help="Salary Expected by Applicant")
    salary_proposed_secure = fields.Secure(
        string='Proposed Salary',
        security="_password_security",
        help="Salary Proposed by the Organization")
    partner_name = fields.Char("Applicant's Name", track_visibility="onchange")
    email_from = fields.Char('Email', size=128,
                             help="These people will receive email.",
                             track_visibility="onchange")
    partner_mobile = fields.Char('Mobile', size=32,
                                 track_visibility="onchange")
    type_id = fields.Many2one('hr.recruitment.degree', 'Degree',
                              track_visibility="onchange")
    date_action = fields.Date('Next Action Date', track_visibility="onchange")
    title_action = fields.Char('Next Action', size=64,
                               track_visibility="onchange")
    priority = fields.Selection(AVAILABLE_PRIORITIES, 'Appreciation',
                                track_visibility="onchange")
    source_id = fields.Many2one('hr.recruitment.source', 'Source',
                                track_visibility="onchange")
    reference = fields.Char('Referred By', track_visibility="onchange")
    job_id = fields.Many2one('hr.job', 'Applied Job',
                             track_visibility="onchange")
    availability = fields.Integer(
        'Availability', help="The number of days in which the applicant will "
        "be available to start working", track_visibility="onchange")
    categ_ids = fields.Many2many('hr.applicant_category', string='Tags',
                                 track_visibility="onchange")
    description = fields.Text('Description', track_visibility="onchange")

    @api.model
    def create(self, vals):
        """
        Override function
        Calculate Subject = {Applied Job} - {Applicants name}
        """
        job_obj = self.env['hr.job']
        job_name = ''
        if vals.get('job_id'):
            job_name = job_obj.browse(vals['job_id']).name
        vals['name'] = job_name and job_name + ' - ' + vals['partner_name'] \
            or vals['partner_name']
        return super(hr_applicant, self).create(vals)

    @api.multi
    def write(self, vals):
        """
        Override function
        Calculate Subject = {Applied Job} - {Applicants name}
        """
        if 'job_id' not in vals and 'partner_name' not in vals:
            # Nothing change
            return super(hr_applicant, self).write(vals)

        job_obj = self.env['hr.job']
        if 'job_id' in vals and 'partner_name' in vals:
            # change job and applicant name
            # update all applicant at the same time
            job_name = ''
            if vals.get('job_id'):
                job_name = job_obj.browse(vals['job_id']).name
            vals['name'] = job_name and job_name + ' - ' \
                + vals['partner_name'] \
                or vals['partner_name']
            return super(hr_applicant, self).write(vals)
        else:
            # change job or partner_name
            if 'job_id' in vals:
                # Only change job name
                job_name = ''
                if vals['job_id']:
                    job_name = job_obj.browse(vals['job_id']).name
                for app in self:
                    pos = app.name.find('-')
                    vals['name'] = job_name and job_name + ' - ' + \
                        (pos > -1 and app.name[pos + 2:] or app.name) \
                        or app.name[pos + 2:]
                    super(hr_applicant, app).write(vals)
            elif 'partner_name' in vals:
                # On change the application name
                for app in self:
                    pos = app.name.find('-')
                    vals['name'] = (pos > -1 and app.name[: pos + 2] or '') + \
                        vals['partner_name']
                    super(hr_applicant, app).write(vals)
        return True

    @api.multi
    def _password_security(self):
        """
            Only the followers of the application can read/update/delete the
            Propose Salary/Suggested Salary.
        """
        is_allow = False
        for rec in self:
            if self.env.user.partner_id.id in rec.message_follower_ids.ids:
                is_allow = True
            else:
                is_allow = False
                break
        return is_allow

    @api.model
    def _get_applicants_of_followers(self, user_id):
        filter_ids = []
        current_user = self.env["res.partner"].search(
            [('user_id', '=', user_id)])
        self._cr.execute(""" SELECT id FROM hr_applicant """)
        datas = [data[0] for data in self._cr.fetchall()]
        for rec in self.browse(datas):
            if current_user in rec.message_follower_ids:
                filter_ids.append(rec.id)
        if filter_ids:
            return [('id', 'in', filter_ids)]
        else:
            return [('id', 'in', [])]

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        uid = self._context.get('uid', self._uid)
        if self.message_follower_ids and \
                uid in self.message_follower_ids.ids:
            args.extend(self._get_applicants_of_followers(uid))
        return super(hr_applicant, self).search(
            args, offset=offset, limit=limit, order=order, count=count)

    @api.cr_uid_ids_context
    def message_track(self, cr, uid, ids, tracked_fields,
                      initial_values, context=None):
        def convert_for_display(value, col_info):
            if not value and col_info['type'] == 'boolean':
                return 'False'
            if not value:
                return ''
            if col_info['type'] == 'many2one':
                return value.name_get()[0][1]
            if col_info['type'] == 'selection':
                return dict(col_info['selection'])[value]
            if col_info['type'] == 'many2many':
                str1 = ', '.join([v.name_get()[0][1] for v in value])
                return str1
            return value

        def format_message(message_description, tracked_values):
            message = ''
            if message_description:
                message = '<span>%s</span>' % message_description
            for name, change in tracked_values.items():
                old_values = change.get('old_value')
                if isinstance(old_values, int):
                    old_values = str(old_values)
                list_old_values = \
                    [item.strip().encode('utf-8')
                     for item in old_values.strip('[]').split(',')]

                new_values = change.get('new_value')
                if isinstance(new_values, int):
                    new_values = str(new_values)
                list_new_values = \
                    [item.strip().encode('utf-8')
                     for item in new_values.strip('[]').split(',')]

                vals = []
                for x in list_old_values:
                    if x not in list_new_values:
                        vals.append(x.decode('utf-8'))
                if vals:
                    message +=\
                        '<div> &nbsp; &nbsp; &bull; <b>Removed %s</b>: ' %\
                        change.get('col_info')
                    message += '%s</div>' % ', '.join(vals)

                vals = []
                for x in list_new_values:
                    if x not in list_old_values:
                        vals.append(x.decode('utf-8'))
                if vals:
                    message +=\
                        '<div> &nbsp; &nbsp; &bull; <b>Added %s</b>: ' %\
                        change.get('col_info')
                    message += '%s</div>' % ', '.join(vals)
            return message

        if not tracked_fields:
            return True

        for browse_record in self.browse(cr, uid, ids, context=context):
            initial = initial_values[browse_record.id]
            changes = set()
            tracked_values = {}

            # generate tracked_values data structure: {'col_name': {col_info,
            # new_value, old_value}}
            for col_name, col_info in tracked_fields.items():
                field = self._fields[col_name]
                initial_value = initial[col_name]
                record_value = getattr(browse_record, col_name)

                if record_value == initial_value and\
                        getattr(field, 'track_visibility', None) == 'always':
                    tracked_values[col_name] = dict(
                        col_info=col_info['string'],
                        new_value=convert_for_display(record_value, col_info),
                    )
                # because browse null != False
                elif record_value != initial_value and\
                        (record_value or initial_value):
                    if getattr(field, 'track_visibility', None) in\
                            ['always', 'onchange']:
                        tracked_values[col_name] = dict(
                            col_info=col_info['string'],
                            old_value=convert_for_display(
                                initial_value, col_info),
                            new_value=convert_for_display(
                                record_value, col_info),
                        )
                    if col_name in tracked_fields:
                        changes.add(col_name)
            if not changes:
                continue

            # find subtypes and post messages or log if no subtype found
            subtypes = []
            # By passing this key, that allows to let the subtype empty and so
            # don't sent email because partners_to_notify from
            # mail_message._notify will be empty
            if not context.get('mail_track_log_only'):
                for field, track_info in self._track.items():
                    if field not in changes:
                        continue
                    for subtype, method in track_info.items():
                        if method(self, cr, uid, browse_record, context):
                            subtypes.append(subtype)

            posted = False
            for subtype in subtypes:
                subtype_rec = self.pool.get('ir.model.data').xmlid_to_object(
                    cr, uid, subtype, context=context)
                if not (subtype_rec and subtype_rec.exists()):
                    _logger.debug('subtype %s not found' % subtype)
                    continue
                message = format_message(
                    subtype_rec.description if subtype_rec.description else
                    subtype_rec.name, tracked_values)
                self.message_post(
                    cr, uid, browse_record.id, body=message,
                    subtype=subtype, context=context)
                posted = True
            if not posted:
                message = format_message('', tracked_values)
                self.message_post(
                    cr, uid, browse_record.id,
                    body=message, context=context)
        return True
