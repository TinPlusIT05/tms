# Objective
Compare what we consume with what we sell within the same time range.

# Data requirements: what you need to do in TMS
Everything we sell must be recorded in TMS following this rules:
- Dedicated Resource Contract
  - Menu: HR > Resource Bookings > Dedicated Resource Contracts
- Support Contract: an activity of the type "*Support (Defect, Functional Support and Evolution Analysis)*"
- Support tickets with type Initial Project for:
  - Initial Project billable tasks (additionally, you should use the type Initial Project and create Activities that matches the Payment Terms)
- Support tickets with the field `Quotation Approved` checked for:
  - Evolution
  - Consulting: for a business analysis or training
  - ... any service that we sell that don't fit in other categories


Note:
With previous design, the consumed time was mostly not in the same range as the time we sell (based on invoicing date)

# Usage

`$ python generate_performance_report.py tms-integration 2016-01-01 2016-01-30 cc`

Possible team filters: rogue-one, expendables, nils, cc, tung

Note:
 - It is prefered to execute this in a trobz-odoo docker container, see installation info [here](https://sites.google.com/a/trobz.com/dev/tools/docker/set-up-docker)

# Requirements
Dependencies:  
```
sudo pip install erppeek
sudo pip install xlsxwriter
```
Get TMS Source code, Use the current production branch:  
`git clone git@gitlab.trobz.com:project/tms.git`

Create a erppeek config file `erppeek.ini` by copying the template
`erppeek.ini.template` in `tms/erppeek`.

#Report
## Profitability
Columns of the report:
 - Team
 - Project
 - Ticket Workload Produced
 - Ticket Time Spent
 - Support Budget
 - Dedicated Resource
 - Total Budget Man days
 - Project Time spent
 - Project Profitability
 - Team Time Spent
 - Team Profitability
 - Trobz Time Spent
 - Trobz Profitability


# Calculation details
## Ticket Workload Produced
Workload on support ticket with
 - Quotation Approved or Initial Project
 - Invoiceable by Trobz Vietnam
 - the date range including
   - the delivery date
   - or the closing date if no delivery date

## Ticket Time Spent
Based on Working Hours linked to the support ticket or the related forge ticket.

## Support Budget
Based on the `Time Sold for dev (in days)` of the **active** activities having
the support type "*Support (Defect, Functional Support and Evolution Analysis)*".

`sum("Time Sold for dev (in days)" / 30 * report_period_range_days)`

## Total Budget Man days
- 1.4 * (Ticket Workload Produced + Dedicated Resource) + Support Budget

## Total Time spent
- Sum of time spent on the project

## Missing Working Hours
- Excludes trainees
- Per employee:  
  days(wizard.date_to - wizard.date_from) * 8 * 251 / 365
  - working hours input during the period
  - We must take into account the hiring date
- Where:
  - 8: hours in a day
  - 251: number of working days in a year (=(365*5/7-10))
    - 5/7: 5 working days per week of 7 days
    - 10: public holidays]


# Improvements to do
- A team might not be in charge of any project (ex: Tu's team should have no projects), yet it must be possible
 to allocate Team/Trobz time.
- Activities in TMS should have a Starting and Ending Date to handle the case of
 completed support contracts (useful for Arena or a Support contract terminated)


# Possible improvements
- Improve the calculation of missing working hours, currently it takes into account all active employees
  - instead it is should take into account all employees and take into account the contracts not trial and not trainee). see TMS > res_users.check_wh_n_day_past
  - it should ignore public holidays
- Add a delivery team to the project which should be used instead of the DTM (Done muanually in report_data, need to change in TMS)
- Factor 1.4 should be defined per (billed) activity, S#9587
- Invoicing Flow: we should handle the Initial Projects in the same way as Evolution (to be agreed by Denis, then update the tools).
  This will allow to handle all the invoicing in the same way (Evolutions or Initial Project) ???? (special case of downpayment)


# Simplifications / limitations
- Only one DTM per project
- Ignore people changing teams; only the current team is taken into account (this impacts only for the re-allocation of missing working hours and Trobz allocation)
- About Trainee and employees in probation, we expect the 2 below factors to balance each other:
  - Expected productivity is low in first weeks
  - Will consume time from other team members
- Missing working hours of DTM are only allocated to their main team


# Development notes
## erppeek manual commands
import erppeek
client = 'tms-production'
client = erppeek.Client.from_config(client)
date_from='2016-01-01'
date_to='2016-05-11'
SupportTicket = client.model('tms.support.ticket')
ticket_fields = ["id", "project_id", "workload", "state", "time_spent"]
PROJECT_ID = 132  # ospreypacks

domain_produced_1 = [
    "|", ('quotation_approved', '=', True),
    ('ticket_type', '=', 'initial_project'),
    ('staging_delivery_date', '>=', date_from),
    ('staging_delivery_date', '<=', date_to),
    ('project_id','=',PROJECT_ID)]
tickets_1 = SupportTicket.read(domain_produced_1, fields=ticket_fields)
len(tickets_1)
