# Objective
Script to create support tickets and related forge tickets in batch from a csv file.


# Usage

Steps:
 - Prepare a csv file with data for the tickets to create
   - see detail below
 - Prepare all the related records
   - see detail below
 - Consider disabling mail notifications
   - (remove default subscribers of the projects)
 - Execute in integration to test the creation in TMS integration or your local
 - Execute in production
 - Add default subscribers back to the project

## Prepare a csv file with data for the tickets to create
Place a csv file in this folder (ex `tickets_data.csv`) with the columns:
- functional block
- summary
- workload
- milestone: the Milestone Number in TMS
- description
- assignee: the tms login of the user to be set as assignee
- reporter: the tms login of the user to be set as reporter
- project: the project name
- activity: the activity name
- customer: the customer name


## Prepare all the related records
In TMS, creates the related records:
- functional blocks
- milestone
- assignee
- reporter
- project
- activity
- customer


## Test the creation in TMS integration or your local
If you don't have the rights, ask sysadmin team to backup / restore a database
from production to integration for you

Migrate a copy of the production to integration
  - `remoteoi db openerp-tms80-production migrate tms80 tms80_tmp openerp-tms80-integration`

Backup a copy of the production to local
  - `remoteoi db openerp-tms80-production backup tms80 --restore --admin-pwd songonight`


## Execute the command
 `python create_support_tickets.py tms-integration tickets_data.csv`

# Requirements
Dependencies:  
```
sudo pip install erppeek
```

Get TMS Source code, Use the current production branch:  
`git clone git@gitlab.trobz.com:project/tms.git`

Create a erppeek config file `erppeek.ini` by copying the template
`erppeek.ini.template` in `tms/erppeek`.

# Improvements ideas
- Show the url of the ticket after creation
