# -*- coding: utf-8 -*-

# Usage:
# $ python find_forge_ticket_invalid_delivery_status.py tms

import erppeek
import sys
from datetime import datetime


def check_delivery_to_staging_after_production(delivery_ids):
    # looking for delivery to staging and production after this staging
    deliver_to_production = False
    deliver_to_staging = False
    for delivery in delivery_ids:
        server_type = delivery.instance_id.server_type
        if server_type in ['test', 'demo']:
            continue
        elif server_type == 'production':
            deliver_to_production = delivery
        elif server_type == 'staging':
            deliver_to_staging = delivery
            break
    return deliver_to_production, deliver_to_staging


def is_reopening_after_delivery(delivery_ids, reopening_times_ids):
    # Check newest re-open after newest delivery
    latest_reopening_obj = reopening_times_ids[0]
    latest_delivery_obj = delivery_ids[0]
    if latest_reopening_obj.date > latest_delivery_obj.name:
        return True
    return False


def in_development_status(ticket_status, delivery_ids, reopening_times_ids):
    """
    'In Development':
        I. Ticket status is in ['assigned', 'wip',
                'code_completed', 'ready_to_deploy']:
            1) Deliveries list is Empty.
            2) Delivery and Reopening are already existed
                and latest Reopening time > latest Delivery time.
    """
    result = False
    if ticket_status in ['assigned', 'wip',
                         'code_completed', 'ready_to_deploy']:

        if not delivery_ids:
            result = True
        elif reopening_times_ids:
            reopening_after_delivery = is_reopening_after_delivery(
                delivery_ids, reopening_times_ids)
            if reopening_after_delivery:
                result = True
    return result


def in_integration_status(ticket_status, delivery_ids, reopen_times_ids):
    """
    'In Integration':
        I. Ticket status is in ['ready_to_deploy', 'in_qa']:
            1) Latest delivery 'Integration'.
                - Only 1 delivery.
                - More than 1 delivery and not yet deliver to production after
                    deliver to staging.
    """
    result = False
    if ticket_status in ['ready_to_deploy', 'in_qa']:
        if delivery_ids:
            latest_delivery_obj = delivery_ids[0]
            if latest_delivery_obj.instance_id.server_type == 'integration':
                if len(delivery_ids) > 1:
                    del_to_production, del_to_staging = \
                        check_delivery_to_staging_after_production(
                            delivery_ids)
                    if del_to_staging:
                        if reopen_times_ids:
                            latest_reopen_obj = reopen_times_ids[0]
                            if del_to_production:
                                deliver = del_to_production
                            else:
                                deliver = del_to_staging
                            if latest_reopen_obj.date > deliver.name:
                                result = True
                    else:
                        result = True
                else:
                    result = True
    return result


def ready_for_staging_status(ticket_status, delivery_ids):
    """
    'Ready for staging':
        I. Status of ticket is in ['closed']:
            1) latest Delivery is 'Integration'.
    """
    result = False
    if ticket_status in ['closed']:
        if delivery_ids:
            latest_delivery_obj = delivery_ids[0]
            if latest_delivery_obj.instance_id.server_type == 'integration':
                result = True
    return result


def in_staging_status(ticket_status, delivery_ids, reopen_times_ids):
    """
    'In Staging':
        I. Status of ticket is in ['ready_to_deploy', 'in_qa', 'closed']:
            1) latest Delivery is 'Staging'.
            2) Deliver to integration after delivery to staging (
                not yet deliver to production)
                a) without re-opening.
                b) with re-opening and time reopen < time deliver to staging.
    """
    result = False
    if ticket_status in ['ready_to_deploy', 'in_qa', 'closed']:
        if delivery_ids:
            latest_del_obj = delivery_ids[0]
            if latest_del_obj.instance_id.server_type == 'staging':
                result = True
            elif latest_del_obj.instance_id.server_type == 'integration':
                del_to_production, del_to_staging = \
                    check_delivery_to_staging_after_production(delivery_ids)
                if del_to_staging:
                    if reopen_times_ids:
                        latest_reopen_obj = reopen_times_ids[0]
                        if del_to_production:
                            deliver = del_to_production
                        else:
                            deliver = del_to_staging
                        if latest_reopen_obj.date > deliver.name:
                            result = True
                    else:
                        result = True
    return result


def production_status(ticket_status, delivery_ids):
    """
    'In Production':
        I. Status of ticket is in ['closed'].
            1) latest Delivery is 'Production'.
    """
    result = False
    if ticket_status in ['closed']:
        if delivery_ids:
            latest_delivery_obj = delivery_ids[0]
            if latest_delivery_obj.instance_id.server_type == 'production':
                result = True
    return result


def no_development_status(ticket_status, delivery_ids, reopening_times_ids):
    """
    'No Development':
        I. Status of ticket is in ['closed'].
            1) a) Don't have any Delivery
               b) Delivery and reopening
                    and latest reopening time > latest delivery time
    """
    result = False
    if ticket_status in ['closed']:
        if not delivery_ids:
            result = True
        elif reopening_times_ids:
            reopening_after_delivery = is_reopening_after_delivery(
                delivery_ids, reopening_times_ids)
            if reopening_after_delivery:
                result = True
    return result


def general_process(milestone):
    tmsmilestone = client.model('tms.milestone')
    mile_stone = tmsmilestone.browse([('name', '=', milestone)])
    if not mile_stone:
        print "Milestone % is not exist" % milestone
    else:
        ticket_ids = mile_stone.forge_ticket_ids[0]
        in_development = {'valid': [], 'unvalid': []}
        in_integration = {'valid': [], 'unvalid': []}
        ready_for_staging = {'valid': [], 'unvalid': []}
        in_staging = {'valid': [], 'unvalid': []}
        in_production = {'valid': [], 'unvalid': []}
        no_development = {'valid': [], 'unvalid': []}
        print "There are %s tickets in milestone %s" % (len(ticket_ids),
                                                        milestone)
        for ticket in ticket_ids:
            print "==**== ticket ==**==", ticket
            delivery_status = ticket.delivery_status
            ticket_status = ticket.state
            delivery_ids = ticket.delivery_id
            reopening_times_ids = ticket.forge_reopening_ids

            # 1.'In Development'
            if delivery_status == 'in_development':
                valid_ticket = in_development_status(
                    ticket_status, delivery_ids, reopening_times_ids)
                in_development['valid'].append(ticket.id)
                if not valid_ticket:
                    in_development['unvalid'].append(ticket.id)

            # 2. 'In Integration'
            elif delivery_status == 'in_integration':
                valid_ticket = in_integration_status(
                    ticket_status, delivery_ids, reopening_times_ids)
                in_integration['valid'].append(ticket.id)
                if not valid_ticket:
                    in_integration['unvalid'].append(ticket.id)

            # 3. 'Ready for staging'
            elif delivery_status == 'ready_for_staging':
                valid_ticket = ready_for_staging_status(
                    ticket_status, delivery_ids)
                ready_for_staging['valid'].append(ticket.id)
                if not valid_ticket:
                    ready_for_staging['unvalid'].append(ticket.id)

            # 4. 'In Staging'
            elif delivery_status == 'in_staging':
                valid_ticket = in_staging_status(ticket_status, delivery_ids,
                                                 reopening_times_ids)
                in_staging['valid'].append(ticket.id)
                if not valid_ticket:
                    in_staging['unvalid'].append(ticket.id)

            # 5. 'In Production'
            elif delivery_status == 'in_production':
                valid_ticket = production_status(ticket_status, delivery_ids)
                in_production['valid'].append(ticket.id)
                if not valid_ticket:
                    in_production['unvalid'].append(ticket.id)

            # 6. 'No Development'
            elif delivery_status == 'no_development':
                valid_ticket = no_development_status(
                    delivery_ids, ticket_status, reopening_times_ids)
                no_development['valid'].append(ticket.id)
                if not valid_ticket:
                    no_development['unvalid'].append(ticket.id)
            else:
                print "Can not found status %s" % delivery_status
        print "%s wrong tickets %s tickets In Development: %s" % (
            len(in_development['unvalid']), len(in_development['valid']),
            in_development['unvalid'])
        print "%s wrong tickets %s tickets In Integration: %s" % (
            len(in_integration['unvalid']), len(in_integration['valid']),
            in_integration['unvalid'])
        print "%s wrong tickets %s tickets Ready For Stagin: %s" % (
            len(ready_for_staging['unvalid']), len(ready_for_staging['valid']),
            ready_for_staging['unvalid'])
        print "%s wrong tickets %s tickets In Staging: %s" % (
            len(in_staging['unvalid']), len(in_staging['valid']),
            in_staging['unvalid'])
        print "%s wrong tickets %s tickets In Production: %s" % (
            len(in_production['unvalid']), len(in_production['valid']),
            in_production['unvalid'])
        print "%s wrong tickets %s tickets No Development: %s" % (
            len(no_development['unvalid']), len(no_development['valid']),
            no_development['unvalid'])

if len(sys.argv) == 4:
    client = erppeek.Client.from_config(sys.argv[1])
    project = sys.argv[2]
    milestone = sys.argv[3]
    general_process('%s %s' % (project, milestone))
else:
    print "Make sure you run this script: " \
          "python find_forge_ticket_invalid_delivery_status.py" \
          " tms *milestone_name*"
