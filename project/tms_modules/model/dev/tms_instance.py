# -*- encoding: utf-8 -*-
from datetime import datetime
import logging
import time
from xml.sax.saxutils import escape
import xmlrpclib

from openerp import SUPERUSER_ID
from openerp import api, fields
from openerp.addons.field_secure import models  # @UnresolvedImport
from openerp.tools.safe_eval import safe_eval
from openerp.exceptions import Warning

# order of server_type is important to set delivery_status on forge
server_type_array = [
    ('production', 'Production'),
    ('staging', 'Staging'),
    ('integration', 'Integration'),
    ('test', 'Test'),
    ('demo', 'Demo'),
    ('hotfix', 'Hotfix'),
]

instance_state_array = [
    ('active', 'Active'),
    ('sleep', 'Sleep'),
    ('exception', 'Exception'),
    ('inactive', 'Inactive'),
    ('deleted', 'Deleted')
]

test_instance_array = [
    ('access', 'Access only'),
    ('access_login', 'Access and login'),
    ('none', 'None')
]


class TmsInstance(models.SecureModel):
    _name = "tms.instance"
    _inherit = ['mail.thread']
    _order = "name"

    _sql_constraints = [
        ('instance_unique', 'unique (name)', 'This instance already exists!'),
        ('host_xmlrpc_unique', 'unique (host_id,xmlrpc_port)',
         'This xmlrpc port already exists on that host!')
    ]

    # ========================================================================
    # FIELD DEFINITIONS
    # ========================================================================

    https_password = fields.Secure(  # @UndefinedVariable
        string="HTTP Authen Test Password",
        security="_security_https_password")

    name = fields.Char('Instance Name', size=256, required=True,
                       track_visibility='onchange')
    mail_instance = fields.Char(compute='_get_mail', string='Mail')
    project_id = fields.Many2one('tms.project', 'Project name',
                                 required=True, track_visibility='onchange')

    milestone_id = fields.Many2one(
        'tms.milestone', 'Milestone',
        track_visibility='onchange',
        required=True)

    host_id = fields.Many2one('tms.host', 'Host',
                              required=True, track_visibility='onchange')

    physical_host_id = fields.Many2one('tms.host',
                                       related='host_id.physical_host_id',
                                       string="Node", store=True)

    parent_bzr_repository_suffix = fields.Char(
        'Parent bzr Repository Suffix',
        size=64,
        help='A possible value is "-stable" '
        'if we want to use the repositories '
        'in {project_name}-stable instead of '
        'the one in {project_name}.')

    server_type = fields.Selection(
        server_type_array, 'Server Type', required=True,
        track_visibility='onchange')

    url = fields.Char('URL', size=256, required=True,
                      track_visibility='onchange')

    xmlrpc_port = fields.Char('xmlrpc port', size=256,
                              track_visibility='onchange')

    psql_host = fields.Char('PostgreSQL Host', size=120, required=True,
                            track_visibility='onchange', default='localhost')

    psql_port = fields.Char('PostgreSQL Port', size=120, required=True,
                            track_visibility='onchange', default='5432')

    psql_user = fields.Char('PostgreSQL User', size=120, required=True,
                            track_visibility='onchange')

    psql_pass = fields.Char('PostgreSQL Pass', size=120, required=True,
                            track_visibility='onchange')

    is_set_up_domain = fields.Boolean(
        'Domain',
        help='Create the instance for: {projectname}.tms.com')

    is_set_up_http_authentication = fields.Boolean(
        'Http Authentication',
        help='Set http authentication to '
        '{projectname}.tms.com to (denis, jc, '
        'tam, TPM,{projectname})')

    is_set_up_https = fields.Boolean('https')

    is_set_up_xmlrpc = fields.Boolean('xmlrpc')

    is_set_up_ssh_access = fields.Boolean('ssh access',
                                          help='Set ssh access & '
                                          'passwordless to '
                                          '{projectname}.tms.com to '
                                          '(denis, jc,  TPM,{projectname})')

    is_project_manager = fields.Boolean(
        compute='compute_is_project_manager',
        string='Is Project Manager')

    state = fields.Selection(
        instance_state_array,
        string='Status', required=True,
        default='active',
        help='Sleep: the instance is active but is facing temporary '
        'issues not under our control. Inactive: This instance will '
        'not be used anymore. Deleted: This instance has been removed '
        'from our servers.',
        track_visibility='onchange'
    )

    datetime_test = fields.Datetime('Last Test', readonly=True)

    note = fields.Text('Note')

    last_error = fields.Text('Last Error')

    operating_system = fields.Char(compute='compute_operating_system',
                                   method=True, string="Operating System",
                                   store=True)

    ssh_port = fields.Char(compute='compute_ssh_port', string="SSH Port",
                           store=True)

    custom_parameter = fields.Serialized('Custom parameter',
                                         track_visibility='onchange')

    instance_database_ids = fields.One2many('instance.database',
                                            'tms_instance_id',
                                            string='Instance Database')

    active = fields.Boolean('Active', default=True,
                            help="When unchecked, the instance will not "
                            "be visible in the user interface unless the "
                            "search filters specify that you want to "
                            "display non-active records (this a native "
                            "behavior of Odoo)")

    test_instance = fields.Selection(
        test_instance_array,
        default='access_login',
        required=True, string='Test instance',
        help="- Access only: Test if instance is up by connecting xmlrpc "
        "and test database names\n"
        "- Access and login: Test if instance is up by connecting xmlrpc "
        "and can be login into admin account and test database names\n"
        "- None: Don't test status of the instance, "
        "don't check the database names.",
        track_visibility='onchange'
    )

    xmlrpc_url = fields.Char(compute='compute_xmlrpc_url',
                             string="XML-RPC URL")

    https_login = fields.Char('HTTP Authen Test Login', size=64)

    proj_owner_id = fields.Many2one('res.users',
                                    related='project_id.owner_id',
                                    string="Project's Owner",
                                    store=True)
    team_id = fields.Many2one(string='Team', related='project_id.team_id',
                              store=True)
    team_manager_id = fields.Many2one(
        string="Team Manager", related='project_id.team_id.team_manager',
        store=True)

    backend_ip = fields.Char('Backend IP')

    backend_port = fields.Char('Backend Port', default='8069')

    ssl = fields.Boolean(
        'SSL',
        default=True,
        help="SSL termination is handled by nginx"
    )

    http_auth = fields.Boolean('HTTP Auth', default=True)

    htpasswd_file = fields.Char('htpasswd file')

    instance_user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='tms_instance_user_rel',
        column1='instance_id',
        column2='user_id',
        string="Users of Instance",
        help="list users who can access to this instance "
        "( to generate htpasswd file)")

    multi_host = fields.Boolean(string="is Multi-host?",
                                track_visibility='onchange')

    haproxy_host_id = fields.Many2one('tms.host', string="HA Proxy Host",
                                      track_visibility='onchange')

    front_end_ids = fields.Many2many(
        comodel_name='tms.host',
        relation="tms_instance_host_front_end_rel",
        column1="instance_id",
        column2="host_id",
        string="Front End",
        track_visibility='onchange')

    back_end_ids = fields.Many2many(
        comodel_name='tms.host',
        relation="tms_instance_host_back_end_rel",
        column1="instance_id",
        column2="host_id",
        string="Back Office",
        track_visibility='onchange')

    database_ids = fields.One2many(
        'multi.host.database', 'instance_id', string="Databases",
        track_visibility='onchange')

    nfs_host_id = fields.Many2one(
        'tms.host', string="NFS Host",
        track_visibility='onchange')

    awx_job_history_ids = fields.One2many(
        comodel_name='tms.awx.job.history',
        inverse_name='instance_id', string='AWX Job History')

    @api.multi
    def write(self, vals):
        res = super(TmsInstance, self).write(vals)
        if vals.get('database_ids', False):
            for instance in self:
                databases = instance.database_ids
                master_no = len(databases.filtered('master'))
                if master_no > 1:
                    raise Warning('ONLY ONE DATABASE CAN BE SET AS MASTER')
        return res

    # ========================================================================
    # COMPUTE FUNCTION DEFINITIONS
    # ========================================================================

    @api.multi
    def _get_mail(self):
        mail_content = ''
        numb = 1

        # Only check on active instances with databases defined
        domain_build = [
            ('state', 'in', ['active']),
            ('instance_database_ids', '!=', False),
            ('test_instance', '=', 'access_login')
        ]
        instances = self.search(domain_build)
        logging.info('{0} instance(s) have databases need '
                     'to be compared'.format(len(instances)))

        for instance in instances:
            list_db_in_instance, list_db_in_tms_instances = \
                self.get_lst_db_instance(instance)
            if not list_db_in_instance and not list_db_in_tms_instances:
                continue

            mail_content += '<div><b>' + str(numb) + '.'
            mail_content += instance.name + '</b>:</div>'
            if list_db_in_instance and list_db_in_tms_instances:
                mail_content += '<ul>'
                mail_content += '<li>Database(s) in instance:' + \
                    ','.join(list_db_in_instance) + '</li>'
                mail_content += '<li>Database(s) in TMS:' + \
                    ','.join(list_db_in_tms_instances) + '</li>'
                mail_content += '</ul>'
            else:
                mail_content += '<ul>'
                mail_content += "<li><font color=red>Cannot access" +\
                    " the instance!</font></li>"
                mail_content += '</ul>'
            numb += 1

        for user in self:
            user.mail_instance = mail_content

    @api.model
    def get_lst_db_instance(self, instance):
        # Get instance address to test - including port
        # Get the https login and password
        https_login = instance.https_login or 'guest'
        https_password = instance.read_secure(
            fields=['https_password'])[0].get('https_password', 'n0-@pplY')
        inject_idx = instance.xmlrpc_url.find('://')
        uri_base = '%s://%s:%s@%s' % (instance.xmlrpc_url[:inject_idx],
                                      https_login, https_password,
                                      instance.xmlrpc_url[inject_idx + 3:])

        # List to store database for each instances and in TMS
        instance_databases_list = []

        # Databases configured for instance in TMS
        tms_instances_databases_list = [
            db_info.name for db_info in instance.instance_database_ids]
        # log in uri
        message = ''
        error_stack = []
        try:
            # Link to instance's db service, should be:
            # http://<user>:<pass>@<host-name>:<port>/xmlrpc/db
            # can be changed by later versions (odoo)
            conn = xmlrpclib.ServerProxy(uri_base + '/xmlrpc/db')
            instance_databases_list = conn.list()

        except Exception as e:
            logging.warning('Failed at sock common')
            message += 'Warning: Failed at sock common\n'
            error_stack.append(e)
            return [], []

        # Compare 2 database list before calling check_database to improve the
        # performance
        tms_instances_databases_list = sorted(tms_instances_databases_list)
        instance_databases_list = sorted(instance_databases_list)
        compare_list = set(tms_instances_databases_list).symmetric_difference(
            instance_databases_list)
        if not compare_list:
            return [], []

        list_db_in_tms_instances = self.check_database(
            tms_instances_databases_list, instance_databases_list
        )
        list_db_in_instance = self.check_database(
            instance_databases_list, tms_instances_databases_list
        )
        return list_db_in_instance, list_db_in_tms_instances

    @api.multi
    def compute_is_project_manager(self):
        user = self.env["res.users"].browse(self._uid)
        user_group_ids = [group.id for group in user.groups_id]
        pm_group_ids = self.env["res.groups"].search(
            [('name', '=', 'TMS Activity Viewer')])
        if pm_group_ids and user_group_ids:
            for record in self:
                record.is_project_manager = pm_group_ids[0].id in \
                    user_group_ids

    @api.multi
    @api.depends(
        "host_id",
        "host_id.operating_system_id",
        "host_id.operating_system_id.name")
    def compute_operating_system(self):
        for instance in self:
            instance.operating_system = \
                instance.host_id \
                and instance.host_id.operating_system_id \
                and instance.host_id.operating_system_id.name \
                or False

    @api.multi
    @api.depends(
        "host_id",
        "host_id.port")
    def compute_ssh_port(self):
        for instance in self:
            ssh_port = instance.host_id and instance.host_id.port or False
            instance.ssh_port = ssh_port

    @api.multi
    def compute_xmlrpc_url(self):

        for instance in self:

            # Normal authentication, use custom xmlrpc port
            if instance.xmlrpc_port:
                uri_base = '%s:%s' % (instance.url, instance.xmlrpc_port)

                if uri_base[:4] != 'http':
                    uri_base = 'http://%s' % uri_base

            # 8113: Special uri for the instances which require https
            # authentication
            else:
                uri_base = '%s:443' % instance.url
                if uri_base[:5] != 'https':
                    uri_base = 'https://' + uri_base

            instance.xmlrpc_url = uri_base

    # ========================================================================
    # ONCHANGE FUNCTION DEFINITIONS
    # ========================================================================

    @api.onchange('server_type')
    def on_change_server_type(self):
        for instance in self:
            project = instance.project_id
            server_type = instance.server_type
            if not project or not server_type:
                return {}
            name = 'openerp-%s-%s' % (project.name, server_type)
            if server_type == 'production':
                url = '%s.trobz.com' % (project.name)
            else:
                url = '%s-%s.trobz.com' % (project.name, server_type)
            instance.name = name
            instance.url = url
            instance.psql_user = name
            instance.psql_pass = name
            # F#13799 - htpasswd_file field on instance should be editable
            if project and server_type:
                htpasswd_file = '/usr/local/var/auth/htpasswd_%s_%s' %\
                    (project.name, server_type)
                instance.htpasswd_file = htpasswd_file

    @api.onchange('state')
    def on_change_state(self):
        for instance in self:
            if instance.state in ('inactive', 'deleted'):
                instance.active = False
            else:
                instance.active = True

    @api.onchange('project_id')
    def on_change_project_id(self):
        for instance in self:
            project = instance.project_id
            server_type = instance.server_type
            # F#13799 - htpasswd_file field on instance should be editable
            if project and server_type:
                htpasswd_file = '/usr/local/var/auth/htpasswd_%s_%s' %\
                    (project.name, server_type)
                instance.htpasswd_file = htpasswd_file

    @api.onchange('host_id')
    def on_change_host(self):
        for instance in self:
            host = instance.host_id
            if host:
                instance.backend_ip = '10.26.%d.y' % host.container_id
                instance.ssh_port = host.port
            else:
                instance.backend_ip = False
                instance.ssh_port = False

    # ========================================================================
    # FORM BUTTON FUNCTION DEFINITIONS
    # ========================================================================

    @api.multi
    def button_request_in_ticket(self):
        # FIXME: should we consider to remove this function, this is not used
        ticket_pool = self.env['tms.ticket']
        for instance in self:
            ticket_pool.create({
                'summary': u'Configure the instance {0}'.format(instance.name)
            })

    # ========================================================================
    # Daily Check List Instance Databases scheduler (email: Test List DB)
    # ========================================================================

    @api.model
    def check_database(self, list_check, list_to_check):
        RENDER_COLOR = '<font color=red>%s</font>'
        list_new = []
        for i in list_check:
            if i not in list_to_check:
                i = RENDER_COLOR % i
            list_new.append(i)
        return list_new

    @api.model
    def run_scheduler_compare_instance_in_tms_and_database(self):
        logging.info('[Scheduler] [Start] Compare list of databases in TMS '
                     'and in instances')

        domain_build = [
            ('state', 'in', ['active']),
            ('instance_database_ids', '!=', False),
            ('test_instance', '!=', 'none')
        ]
        instances = self.search(domain_build)

        for instance in instances:
            list_db_in_instance, list_db_in_tms_instances = \
                self.get_lst_db_instance(instance)
            if not list_db_in_instance and not list_db_in_tms_instances:
                continue

            # send notification email
            template = self.env.ref(
                'tms_modules.daily_instances_db_template'
            )
            template._send_mail_asynchronous(instance.id)
            logging.info('[Scheduler] [End] Compare list of databases '
                         'in TMS and in instances')
            return True

    # ========================================================================
    # Test Instances Scheduler (email: Instance Down Mail)
    # ========================================================================

    @api.model
    def run_test_instance_scheduler(self):
        logging.info("run_test_instance_scheduler: start")
        try:
            self.button_test_all_instances()
        except Exception as e:
            logging.error("Error in run_test_instance_scheduler: %s" % str(e))
        logging.info("run_test_instance_scheduler: end")
        return True

    @api.multi
    def button_test(self):
        """
        Test instance.
        """
        logging.info('Entered button_test of tms_instance '
                     '(to test availability of instances)...')

        # Number of attempts and Sleep time between each attempt
        NB_ATTEMPS = 2
        TIME_SLEEP = 3
        error_stack = []

        # message for test instance log
        message = ''

        for instance in self:
            message = ''
            vals = {}

            # get the db_login, db_password and db_name
            # from instance database field
            db_login = 'admin'

            if instance.test_instance == 'access_login':
                # check if a database is created for this instance
                if not (instance.instance_database_ids and
                        instance.instance_database_ids.ids or False):
                    logging.warning(
                        'No database defined for the instance %s.'
                        % instance.name
                    )
                    continue

                # only check the first database in the list
                instance_db = instance.instance_database_ids and \
                    instance.instance_database_ids[0] or False

                if instance_db:
                    # extract db name and password from first line
                    db_name = instance_db.name
                    db_password = instance_db\
                        .read_secure(fields=['password'])[0]\
                        .get('password', 'n0-@pplY')
            else:
                db_name = 'unnamed'
                db_password = 'n0-@pplY'

            # Get the https login and password (from instance)
            https_login = instance.https_login or 'guest'
            https_password = instance\
                .read_secure(fields=['https_password'])[0]\
                .get('https_password', 'n0-@pplY')

            inject_idx = instance.xmlrpc_url.find('://')
            uri_base = '%s://%s:%s@%s' % (instance.xmlrpc_url[:inject_idx],
                                          https_login, https_password,
                                          instance.xmlrpc_url[inject_idx + 3:])

            # To remove the https_login_pass from the instance down message
            https_real_pass = ':%s@' % https_password
            https_replace_pass = ':****@'
            logging.info('Checking ' + instance.xmlrpc_url)

            for i in range(NB_ATTEMPS):
                instance_exc = None
                state = 'active'

                # Try to reach the instance
                try:
                    sock_common = xmlrpclib.ServerProxy(
                        '%s/xmlrpc/common' % uri_base)
                except Exception as e:
                    logging.warning('Failed at sock common')
                    message += 'Warning: Failed at sock common\n'
                    state = 'exception'
                    instance_exc = str(e).replace(
                        https_real_pass, https_replace_pass
                    )

                # Try to login at the instance
                try:
                    if instance.test_instance == 'access_login':
                        logging.info(
                            'Trying to login as Admin into instance %s...' %
                            instance.name)
                        message += 'Info: Trying to login as Admin into '\
                            'instance %s...\n' % instance.name
                        connection = sock_common.login(
                            db_name, db_login, db_password)
                        if not connection:
                            raise Exception(
                                'Could not login to the instance %s' %
                                instance.name)
                        else:
                            # reset state and message then break, no more try
                            # after successful check
                            state, message = 'active', ''
                            break
                    elif instance.test_instance == 'access':
                        try:
                            connection = sock_common.login(
                                'test_access_only', 'test', 'test')
                        except Exception as e:
                            if 'FATAL:  database "test_access_only" ' +\
                                    'does not exist' in str(e):
                                state, message = 'active', ''
                                break
                            else:
                                raise Exception(
                                    'Could not connect to the instance %s' %
                                    instance.name)
                except Exception as e:
                    # TODO: to remove the password from the exception
                    exc_str = str(e).replace(https_real_pass,
                                             https_replace_pass)
                    logging.warning('ATTEMPT FAILED: Could not connect '
                                    'to the instance %s: %s' %
                                    (instance.name, exc_str))
                    message += 'Warning: ATTEMPT FAILED: Could not connect '\
                               'to the instance %s: %s' % (instance.name,
                                                           exc_str)
                    state = 'exception'
                    instance_exc = exc_str
                finally:
                    sock_common = None

                if state == 'exception':
                    logging.warning('ATTEMPT FAILED: Tried %s time(s), '
                                    'trying again ...' % (i + 1,))
                    if i < NB_ATTEMPS - 1:
                        time.sleep(TIME_SLEEP)
                    elif i == NB_ATTEMPS - 1:
                        error_stack.append(instance_exc)

            # after N times to check on the instance ==> if instance down
            if state == 'exception':
                logging.error('The instance %s is down !!!' % instance.name)
                message += 'Error: The instance %s is down !!!\n'\
                    % instance.name
                logging.error('Could not connect to the instance %s after %s '
                              'attempts!!' % (instance.name, NB_ATTEMPS))
                message += 'Error: Could not connect to the instance %s '\
                    'after %s attempts!!\n' % (instance.name, NB_ATTEMPS)
                logging.error('uri_base: %s, db_name: %s, db_login: %s, '
                              'db_password: ****' % (instance.xmlrpc_url,
                                                     db_name, db_login))
                message += 'Error: uri_base: %s, db_name: %s, '\
                    'db_login: %s, db_password: ****\n' % (instance.xmlrpc_url,
                                                           db_name, db_login)
                logging.error(error_stack)
                vals['last_error'] = message
                state = 'exception'
            else:
                logging.info(
                    'Connect to the instance %s successful!' % instance.name)
                state = 'active'
                vals['last_error'] = False

            vals.update({
                'state': state, 'datetime_test': datetime.now()
            })
            logging.info('Writing new data to current instance: %s' % vals)

            instance.write(vals)  # write test data to instance

    @api.model
    def button_test_all_instances(self):
        """
        Test instance.
        """

        logging.info('Entered button_test of tms_instance '
                     '(to test availability of instances)...')

        instances = self.search(
            [('state', 'in', ('active', 'exception')),
             ('test_instance', '!=', 'none')]
        )
        for instance in instances:
            instance.button_test()
            # commit the write transaction (before sending email)
            self.env.cr.commit()

        down_instances = self.search([
            ('state', '=', 'exception'),
            ('test_instance', '!=', 'none')
        ])
        if down_instances and down_instances.ids:
            # context should be passed in email process
            context = {'instances_down_ids': down_instances.ids}

            # send email to inform number of down instances
            email_template = self.env.ref(
                'tms_modules.tms_instance_down_mail_template'
            )
            email_template.with_context(context).send_mail(
                down_instances[0].id)

        logging.info('Leaving button_test of tms_instance '
                     '(to test availability of instances)...')

    @api.multi
    def get_mail_down_instances_subject(self):
        """
            this function will be called by email template
            to prepare the subject of the email
        """
        context = self._context and self._context.copy() or {}

        # build domain to get only down instances
        domain = [
            ('state', '=', 'exception'), ('test_instance', '!=', 'none')
        ]
        if context.get('instances_down_ids'):
            domain.append(('id', 'in', context.get('instances_down_ids')))

        # get down instances
        down_instances = self.search(domain)

        if not down_instances.ids:
            return 'No instance down'

        nb_production_instance_down = 0
        nb_instance_down = 0

        for down_instance in down_instances:
            nb_instance_down += 1
            if down_instance.name[-11:] == '-production':
                nb_production_instance_down += 1

        if nb_production_instance_down == 0:
            return '%s Instance(s) down, none from production' %\
                str(nb_instance_down)

        return '%s Instance(s) down, including %s from production' %\
            (str(nb_instance_down), str(nb_production_instance_down))

    @api.multi
    def get_mail_down_instances(self):
        """
        # Ticket #1075 Send list of down instances.
        """
        context = self._context and self._context.copy() or {}
        domain = [('state', '=', 'exception'), ('test_instance', '!=', 'none')]
        if context.get('instances_down_ids'):
            domain.append(('id', 'in', context.get('instances_down_ids')))

        down_instances = self.search(domain)
        if not down_instances:
            return 'No instance down'

        config_pool = self.env['ir.config_parameter']
        base_url = config_pool.get_param(
            'web.base.url',
            default='https://tms.trobz.com')
        base_url = u'{0}#model=tms.instance&id='.format(base_url)

        # 3051
        list_instances_production, list_instances_down = [], []

        # Get name of down instances - classified through instance type
        for instance in down_instances:
            if "production" in instance.name:
                list_instances_production.append(instance.name)
            else:
                list_instances_down.append(instance.name)

        # predefined mail templates and mail contents
        mail_content = u''
        list_template = u"<ol>{0}</ol>"
        details_template = u"<li>{0}: {1}</li>"
        instance_down_contents, instance_down_details = u"", u""

        # compose list of down production instance names
        for instance in list_instances_production:
            instance_down_contents += u'<li>{0} down</li>'.format(instance)

        # compose list of down staging/integration instances name
        for instance in list_instances_down:
            instance_down_contents += u'<li>{0} down</li>'.format(instance)

        # compose list of down instance names
        mail_content += list_template.format(instance_down_contents)

        # detailed information section for down instances
        mail_content += u'More details:<br />'

        # information to be displayed in details, read from database
        for instance in down_instances:
            # name of the down instance first - followed by the details
            instance_down_details += u'<li style="margin-bottom: 15px;">'
            instance_down_details += u'<span>{0} down</span>'.format(
                instance.name)
            # begin detailed information
            instance_down_details += u'<ul style="padding-left: 20px;">'
            instance_down_details += details_template.format(
                "URL", instance.url)
            instance_db_list = [
                db_info.name for db_info in instance.instance_database_ids]
            instance_down_details += details_template.format(
                "Database info", str(instance_db_list))
            instance_down_details += details_template.format(
                "XML-RPC port", instance.xmlrpc_port)
            instance_down_details += details_template.format(
                "Last error", escape(instance.last_error))
            instance_down_details += details_template.format(
                "Link to TMS", base_url + str(instance.id))
            instance_down_details += u'</ul>'
            # end detailed information
            instance_down_details += u'</li>'

        # compose list of down instance details
        mail_content += list_template.format(instance_down_details)

        return mail_content

    @api.multi
    def get_sysadmin_tpm_email_list(self):
        """
        Get list of users who are active Trobz members and
        have jobs in (Manager, Technical Project Manager)
        and have departments in (Management, OpenErp).
        """

        departments = self.env['hr.department'].search(
            [('name', 'in', ('Management', 'OpenErp', 'Sysadmin'))])
        if not departments:
            return 'jcdrubay@trobz.com,sysadmin@lists.trobz.com'
        jobs = self.env['hr.job'].search([
            ('name', 'in', ('Manager', 'Technical Project Manager',
                            'System Admin'))])
        if not jobs:
            return 'jcdrubay@trobz.com,sysadmin@lists.trobz.com'
        employee_obj = self.env['hr.employee']
        employees = employee_obj.search(
            [('job_id', 'in', jobs.ids),
             ('department_id', 'in', departments.ids)])
        if not employees:
            return 'jcdrubay@trobz.com,sysadmin@lists.trobz.com'
        mail_list = ['sysadmin@lists.trobz.com']
        for employee in employees:
            if employee and employee.user_id\
                    and employee.user_id.active\
                    and employee.user_id.is_trobz_member\
                    and employee.user_id.email:
                mail_list.append(employee.user_id.email)
        if mail_list:
            all_mail = ",".join(mail_list) + ",jcdrubay@trobz.com"
        else:
            all_mail = 'jcdrubay@trobz.com,sysadmin@lists.trobz.com'
        return all_mail

    @api.multi
    def get_admin_tpm_sysadmin_email(self):
        result = ""
        res_users_obj = self.env['res.users']
        res_groups_obj = self.env['res.groups']
        admin_tpm_profs = res_groups_obj.search(
            [('name', 'in', ('Admin Profile',
                             'Sysadmin Profile',
                             'Technical Project Manager Profile')),
             ('is_profile', '=', True)])
        res_users = res_users_obj.search(
            [('group_profile_id', 'in', admin_tpm_profs.ids)])
        mail_list = []
        for user in res_users:
            if user.email:
                mail_list.append(user.email)
        if mail_list:
            result = ",".join(mail_list)
        else:
            result = 'sysadmin@lists.trobz.com'
        return result

    # ========================================================================
    # OTHER FUNCTIONS
    # ========================================================================

    @api.model
    def _check_password_security(self, instance):
        """
        @param instance: recordset tms.instance
        @return:
            - Admin profile, return True
            - TPM/FC profiles and in the supporters, return True
            - The rest, return False
        """
        if self._uid == SUPERUSER_ID:
            return True
        config_pool = self.env['ir.config_parameter']
        user_profile = self.env.user.group_profile_id
        # If this user is a Sysadmin and has full access
        if user_profile.is_sysadmin and self.env.user.has_full_sysadmin_access:
            return True
        # If this user is a Sysadmin but don't have full access
        # check if he is in the list of users of the host of this instance
        if user_profile.is_sysadmin\
                and self.env.user.id in instance.host_id.user_ids.ids:
            return True
        # If this user is not a sysadmin, he must be in the list of supporters
        db_instance_profiles = config_pool.get_param(
            'db_instance_profiles')
        db_instance_profiles = safe_eval(db_instance_profiles)

        if user_profile.name not in db_instance_profiles:
            return False
        project_supporters = instance and\
            instance.project_id.project_supporter_rel_ids.ids\
            or []
        if self.env.user.id not in project_supporters:
            return False
        return True

    @api.multi
    def _security_https_password(self):
        """
        Only allow Admin/TPM or FC update read/update password field.
        """
        is_allow = False
        for rec in self:
            if self._check_password_security(rec):
                is_allow = True
            else:
                is_allow = False
                break
        return is_allow

    @api.model
    def run_get_module_quality_check_scheduler(self):
        instance_ids = self.search([
            ('state', '=', 'active')]
        )
        self.button_module_quality_check(instance_ids)
        self.env['email.template']._send_mail_asynchronous(
            self._uid, 'Module Quality Check Result')
        return True

    def _build_result_detail(self, result, result_details):
        detail_dict = {}
        for detail in result_details:
            module_name = result[detail['quality_check_id'][0]]['name']
            module_score = result[detail['quality_check_id'][0]]['final_score']
            if module_name not in detail_dict:
                detail_dict[module_name] = [
                    u'<li> Module {0}: {1}</li>'.format(
                        module_name, module_score)
                ]

        result_detail = u'Last update: {0}<br/>'.format(datetime.now())\
            + u'<li>Modules: </li><ul>'
        for detail in detail_dict.values():
            detail_str = u'<br />  '.join(tuple(detail))
            result_detail = str(result_detail) + detail_str

        return result_detail

    @api.model
    def migrate_database_instance(self):
        logging.info('==== START migrate database instance ====')
        tms_instance_datas = self.search([])
        instance_db_env = self.env['instance.database']
        for data in tms_instance_datas:
            if data.databases:
                databases = data.databases.split(",")
                for database in databases:
                    dict_data = database.split(":")
                    vals = {'name': dict_data[0],
                            'tms_instance_id': data.id}
                    new_data = instance_db_env.create(vals)
                    if len(dict_data) > 1:
                        vals.update({'password': dict_data[1]})
                        new_data.secure_write(vals)
        logging.info('==== END migrate database instance  ====')
        return True

    @api.multi
    def get_databases_list(self):
        """
        Get a list of databases for each given instance.
        """
        databases_lst = {}  # {instance: list of databases}
        for instance in self:
            db_names = [db_info.name
                        for db_info in instance.instance_database_ids]
            databases_lst.update({
                instance.name: db_names
            })
        return databases_lst

    @api.multi
    def get_instance_info(self, context=None):
        """
        Get cleartext password of a database.
        """
        databases_lst = {}
        for instance in self:
            instance_db = instance.instance_database_ids and \
                instance.instance_database_ids[0] or False
            if instance_db:
                db_name = instance_db.name
                db_password = instance_db.read_secure(fields=['password'])
                databases_lst.update({
                    instance.name: [
                        instance.state, instance.server_type,
                        db_name, db_password[0]['password']]
                })
        return databases_lst
