# -*- encoding: utf-8 -*-

from openerp import models, api
import logging


class post_object(models.TransientModel):
    _name = 'post.object'
    _description = 'Trobz CRM post object'

    @api.model
    def start(self):
        return True

    @api.model
    def create_crm_event_tags(self):
        logging.info("===== START: CREATE CRM-EVENT TAGS =====")
        calendar_event_type = self.env['calendar.event.type']
        calendar_event_type.create({'name': 'CRM-Event'})
        logging.info("===== END: CREATE CRM-EVENT TAGS =====")
        return True

    @api.model
    def update_open_status_for_stage(self):
        logging.info("===== START: update_open_status_for_stage =====")
        crm_case_stage = self.env['crm.case.stage']
        crm_case_stage_objs = crm_case_stage.search(
            ['|', '|', '|', '|', ('name', '=', 'New'),
             ('name', '=', 'Qualification'), ('name', '=', 'Opportunity'),
             ('name', '=', 'Proposition'), ('name', '=', 'Negotiation')])
        for crm_case_stage_obj in crm_case_stage_objs:
            crm_case_stage_obj.write({'open_status': True})
        logging.info("===== END: update_open_status_for_stage =====")
        return True

    @api.model
    def update_reminder_cron_interval(self):
        logging.info("===== START: UPDATE REMINDER JOB =====")
        cron = self.env['ir.model.data'].get_object(
            'calendar', 'ir_cron_scheduler_alarm')
        cron.write({'interval_number': 5})
        logging.info("===== END: REMINDER JOB updated =====")
        return True

    @api.model
    def update_date_trobz_crm_event(self):
        logging.info("====== START: UPDATE DATE FOR TROBZ_CRM_EVENT =======")
        sql = """
            UPDATE trobz_crm_event
            SET date = (
                SELECT start_datetime::date
                FROM calendar_event
                WHERE trobz_crm_event.calendar_event_id = calendar_event.id
            )
            WHERE calendar_event_id in (
                SELECT id from calendar_event
                WHERE allday is False or allday is NULL
            );
            UPDATE trobz_crm_event
            SET date = (
                SELECT start_date
                FROM calendar_event
                WHERE trobz_crm_event.calendar_event_id = calendar_event.id
            )
            WHERE calendar_event_id in (
                SELECT id from calendar_event
                WHERE allday is True
            );
        """
        self._cr.execute(sql)
        logging.info("====== END: UPDATE DATE FOR TROBZ_CRM_EVENT =======")
        return True

    @api.model
    def update_lead_mass_update(self):
        logging.info("===== START: update_lead_mass_update =====")
        sql = '''
            update mass_object set name = 'Opportunity mass update'
            where name = 'Lead mass update';
            update ir_actions set name = 'Mass Editing (Opportunity mass update)'
            where name = 'Mass Editing (Lead mass update)';
            update ir_model set name = 'Opportunity'
            where model = 'crm.lead';
        '''
        self._cr.execute(sql)
        logging.info("===== END: update_lead_mass_update =====")
        return True
    @api.model
    def update_probability_id(self):
        '''
        # F#13348 set the value of the field probability_id
        '''
        logging.info(
            "====== START: UPDATE probability_id FOR crm_lead =======")

#         sql = '''
#             UPDATE crm_lead SET probability_id = probability_moved2;
#             UPDATE crm_lead SET probability_id = 3
#             where probability_id is Null;
#         '''
#         self._cr.execute(sql)

        logging.info("====== END: UPDATE probability_id FOR crm_lead =======")
        return True

    @api.model
    def update_priority(self):
        '''
        # F#12553
        '''
        logging.info(
            "====== START: UPDATE update_priority FOR trobz_crm_event =======")

        sql = '''
            update trobz_crm_event
                set priority = '1' where priority = 'low';
            update trobz_crm_event
                set priority = '2' where priority = 'normal';
            update trobz_crm_event
                set priority = '3' where priority = 'high';
            update trobz_crm_event
                set priority = '4' where priority = 'very_high';
        '''
        self._cr.execute(sql)

        logging.info(
            "====== END: UPDATE update_priority FOR trobz_crm_event =======")
        return True
