# -*- encoding: utf-8 -*-

from openerp import api, models, fields, _, SUPERUSER_ID
from openerp.exceptions import Warning
from openerp.tools import config
import time
import requests
import json
import logging


class tms_host(models.Model):

    _name = "tms.host"
    _description = "Host"
    _order = 'operating_system_id'
    _inherit = ['mail.thread']

    @api.one
    @api.onchange('physical_host_id', 'container_id')
    def on_change_physical_host_container(self):
        """
        F#13948 - auto compute ssh port for host (virtual machine)
        """
        if self.virtual_machine:
            self.ip = self.env['ir.config_parameter'].get_param(
                'default_ip_host', False) + str(self.container_id)

        temp = self.config.copy()
        node_add = self.physical_host_id and \
            self.physical_host_id.host_address or False
        if node_add:
            if 'eu' in node_add:
                temp['timezone'] = 'Europe/Berlin'
                self.config = temp
            else:
                temp['timezone'] = 'Asia/Ho_Chi_Minh'
                self.config = temp

        if self.virtual_machine and \
                self.virtualization_id and \
                self.virtualization_id.name == 'Proxmox':
            suggest_ssh_port = '{AREA_CODE}{NODE_NUMBER}{CONTAINER_ID}'
            if self.physical_host_id and \
                    self.physical_host_id.name:
                host_name_prefix = self.physical_host_id.name[:2]
                host_name_suffix = self.physical_host_id.name[-2:]
                if host_name_prefix == 'eu':
                    suggest_ssh_port = suggest_ssh_port.replace(
                        '{AREA_CODE}', '1')
                elif host_name_prefix == 'vn':
                    suggest_ssh_port = suggest_ssh_port.replace(
                        '{AREA_CODE}', '2')
                if host_name_suffix.isnumeric():
                    suggest_ssh_port = suggest_ssh_port.replace(
                        '{NODE_NUMBER}',
                        str(int(host_name_suffix)))
            if self.container_id >= 0:
                suggest_ssh_port = suggest_ssh_port.replace(
                    '{CONTAINER_ID}', str(self.container_id))
            self.port = '{' not in suggest_ssh_port and \
                suggest_ssh_port or '22'

    @api.multi
    def _get_num_of_vm(self):
        for host in self:
            host.num_VM = len(host.virtual_host_ids)

    @api.multi
    @api.depends('name', 'virtual_machine', 'physical_host_id')
    def _get_physical_host(self):
        """
            get physical host for virtual machine
            if host is virtual machine then get Physical Host
            if host is not virtual machine then get name of this Host
        """
        # looking for all virtual host belong to this physical_host and
        # including it
        hosts = self.search(["|", ('physical_host_id', 'in', self._ids),
                             ('id', 'in', self._ids)])
        for host in hosts:
            if host.virtual_machine:
                host.physical_host = host.physical_host_id.name
            else:
                host.physical_host = host.name

    @api.model
    def get_grouped_host(self):
        """
        Retrieve host grouped by physical host
        """

        self._cr.execute('''
        SELECT ph.name, p.name, p.host_address, p.port, p.config
        FROM tms_host AS h
        JOIN tms_host AS ph ON h.physical_host_id = ph.id
        GROUP BY ph.name
        ''')

    @api.model
    def get_authorized_keys(self):
        """
        Retrieve all authorized keys for hosts
        Note: used by configuration manager tools (Ansible)

        Format:
        results = {
            'host-name': {
                'admin': [list of admin users' keys],
                'user': [list of host users' keys]
            }
        }
        """
        # Read private token from cofig file
        # Request to git lab with number users is 400
        results = {}
        private_token_key_config = config.get('private_token') or ''
        if private_token_key_config:
            # Get all user from gitlab
            payload = {
                'private_token': private_token_key_config,
                'per_page': 400
            }
            r = requests.get(
                "https://gitlab.trobz.com/api/v3/users",
                data=payload, verify=False
            )
            gitlab_users = json.loads(r.text) or []

            # First, get all ssh keys from Admin users
            # and Sysadmin users who have full access.
            self._cr.execute('''
                SELECT login
                FROM res_users
                WHERE is_sysadmin = TRUE
                    AND has_full_sysadmin_access = TRUE
                    AND active = TRUE
                    AND id != 1
                ORDER BY id;
            ''')
            admin_usernames = map(lambda r: r[0], self._cr.fetchall())

            host_users = []
            admin_keys = []
            for gitlab_user in gitlab_users:
                if gitlab_user['state'] == 'active':
                    req = requests.get(
                        "https://gitlab.trobz.com/api/v3/users/" +
                        str(gitlab_user['id']) + "/keys",
                        data=payload, verify=False
                    )
                    ssh_vals = json.loads(req.text) or []
                    ssh_keys = []
                    for val in ssh_vals:
                        if 'key' in val:
                            ssh_keys.append(val['key'])
                            if gitlab_user['username'] in admin_usernames:
                                admin_keys.append(val['key'])
                    host_users.append({
                        'login': gitlab_user['username'],
                        'ssh_key': ssh_keys
                    })

            self._cr.execute('''
                SELECT h.name, u.login, u.is_sysadmin
                FROM tms_host AS h
                LEFT JOIN host_users_rel AS hu ON hu.host_id = h.id
                LEFT JOIN res_users AS u ON u.id = hu.user_id
                WHERE (u.is_trobz_member = TRUE AND u.active = TRUE)
                OR u.login IS NULL
                AND h.state != 'deleted'
                ORDER BY h.name, u.id;
            ''')
            # result[0] => host name
            # result[1] => user login name
            # result[2] => is_sysadmin
            for result in self._cr.fetchall():
                if result[0] not in results:
                    # All sysadmin users
                    # who have full access are admins on this host.
                    results[result[0]] = {'admin': admin_keys, 'user': []}

                if result[1]:
                    for host_user in host_users:
                        # All users who are responsible to maintain
                        # odoo instances are users on this host.
                        if result[1] == host_user['login']:
                            results[result[0]]['user'] = list(
                                set(results[result[0]]['user'] +
                                    host_user['ssh_key']))
                            # All sysadmin users who don't have full access,
                            # but are responsible to maintain this host are
                            # admins on this host.
                            if result[2]:
                                results[result[0]]['admin'] = list(
                                    set(results[result[0]]['admin'] +
                                        host_user['ssh_key']))
        else:
            logging.info("You don't have a token key in the config file!")

        return results

    @api.constrains('container_id', 'virtual_machine', 'physical_host_id')
    def check_container_id(self):
        '''
        For Host (Virtual Machine) inside a Physical Host:
            - Container ID between 1 and 255
            - F#13552 - Unique container_id
                (only for Hosts that belong to the same Physical Host)
        '''
        for host in self:
            if host.virtual_machine and host.physical_host_id:
                if host.container_id < 1 or host.container_id > 255:
                    raise Warning(
                        _('You have to input Container ID between 1 and 255 !')
                    )
                # find existing Hosts in Physical Host
                # using the Container ID
                existed_hosts = self.search([
                    ('virtual_machine', '=', True),
                    ('physical_host_id', '=', host.physical_host_id.id),
                    ('container_id', '=', host.container_id),
                    ('id', '!=', host.id),
                    ('state', '!=', 'deleted')
                ])
                if existed_hosts:
                    raise Warning(
                        _('The Container ID should be unique for '
                          'Hosts that belong to the same Physical Host! '
                          'Container ID %s has been used for Host %s!' % (
                              host.container_id, existed_hosts[0].name))
                    )

    @api.multi
    def _get_groups(self):
        for item in self:
            if item.group_ids:
                item.groups = map(lambda group: {
                    'name': group.name,
                    'config': group.config}, item.group_ids)
            else:
                item.groups = []

    # Columns
    name = fields.Char('Host Name', size=256, required=True,
                       track_visibility='onchange')
    host_address = fields.Char('Host Address', size=256, required=True,
                               track_visibility='onchange')
    port = fields.Char('SSH Port', size=256, required=True,
                       track_visibility='onchange')
    ip = fields.Char(
        'IP', size=64, help='For nodes it is the IP address of the node, '
                            'for VM it is the Virtual IP of the VM',
        track_visibility='onchange')
    internal_ip = fields.Char('Internal IP', size=64)
    using_pgbouncer = fields.Boolean(
        string='Using PgBouncer', default=False)
    pgbouncer_port = fields.Char('PgBouncer Port')
    operating_system_id = fields.Many2one(
        'tms.operating.system', string='Operating System',
        track_visibility='onchange')
    # Adjustments of the Hosts
    service = fields.Char('Services', size=64)
    group_ids = fields.Many2many(
        "tms.host.group", "host_host_group_rel", "host_id", "group_id",
        string='Groups', help="Host group, used by ansible",
        track_visibility='onchange')
    groups = fields.Serialized(
        compute='_get_groups', string='Group list',
        readonly=True)
    user_ids = fields.Many2many(
        "res.users", "host_users_rel", "host_id", "user_id",
        string='Users', track_visibility='onchange',
        help="User with permissions to deploy on the host.",
        domain=[('is_trobz_member', '=', True)])
    instance_ids = fields.One2many(
        'tms.instance', 'host_id', string='Instances')
    config = fields.Serialized(
        string='Config', default={"timezone": "Asia/Ho_Chi_Minh"})
    type = fields.Selection([
        ('production', 'Production'), ('staging', 'Staging'),
        ('integration', 'Integration'), ('test', 'Test'),
        ('demo', 'Demo'), ('unknown', 'Unknown'), ('node', 'Node'),
        ('utils', 'Utils')
    ], string='Type', required=True, track_visibility='onchange')
    action_required = fields.Boolean('Action Required',
                                     track_visibility='onchange')
    backup_checking = fields.Date('Audit Date',
                                  track_visibility='onchange')
    update = fields.Datetime('Update', readonly=True)
    virtual_machine = fields.Boolean('Virtual Machine',
                                     track_visibility='onchange')
    virtualization_id = fields.Many2one('tms.host.virtualization',
                                        string='Virtualization',
                                        track_visibility='onchange')
    physical_host_id = fields.Many2one('tms.host', string='Physical Host',
                                       track_visibility='onchange')
    virtual_host_ids = fields.One2many('tms.host', 'physical_host_id',
                                       string='Virtual Machines')
    num_VM = fields.Integer(
        compute='_get_num_of_vm', string='Number of VM')
    # the temp for group by physical host
    physical_host = fields.Char(
        compute='_get_physical_host', string='Physical Host',
        store=True)
    state = fields.Selection(
        [
            ('active', 'Active'), ('exception', 'Exception'),
            ('asleep', 'Asleep'), ('deleted', 'Deleted')
        ], string='Status', track_visibility='onchange',
        help='For the field status:\n'
        '- Active: The host is active and in a normal state.\n'
        '- Exception: Something is wrong (ex: We lost the connection '
        'to host). This is set manually.\n'
        '- Asleep: This host is temporarily disabled.'
        ' -Deleted: We do not handle this host anymore, keeping record.')
    is_managed_by_trobz = fields.Boolean(
        string='Managed by Trobz', help='Instances managed by Trobz.',
        track_visibility='onchange')
    container_id = fields.Integer(
        string='Container ID', help='required for Virtual Machines')
    # Resources
    processors = fields.Integer(string='Processors',
                                track_visibility='onchange')
    ram = fields.Integer(string='Memory (RAM in MB)',
                         track_visibility='onchange')
    disk_size = fields.Integer(string='Disk Size (GB)',
                               track_visibility='onchange')
    swap = fields.Integer(string='Swap (MB)',
                          track_visibility='onchange')
    allow_edit_users = fields.Boolean(
        'Allow Edit Users', compute='_compute_allow_edit_users')
    awx_job_history_ids = fields.One2many(
        comodel_name='tms.awx.job.history',
        inverse_name='host_id', string='AWX Job History')

    _sql_constraints = [
        ('host_unique', 'unique(name)', 'This host already exists!'),
        ('host_add_unique', 'unique(host_address)',
         'This host address already exists!'),
    ]

    _defaults = {
        'port': '22',
        'state': 'active',
        'is_managed_by_trobz': True,
    }

    @api.multi
    def _compute_allow_edit_users(self):
        '''
        Users can only add users to hosts related to their projects
        '''
        user = self.env.user
        for host in self:
            allow = False
            if user.id == SUPERUSER_ID or user.has_full_sysadmin_access:
                allow = True
            else:
                # Apply for PM without has_full_sysadmin_access
                project_owners = host.instance_ids.\
                    mapped('project_id').\
                    mapped('owner_id')
                if user in project_owners:
                    allow = True
            host.allow_edit_users = allow

        return True

    @api.multi
    def write(self, vals):
        """
        when change virtual machine, clear value of field physical host
        or virtual host
        """
        if 'virtual_machine' in vals:
            if vals['virtual_machine']:
                virtual_machines = self.search(
                    [('physical_host_id', '=', self._ids)])
                virtual_machines.write({'physical_host_id': False})
            else:
                vals['physical_host_id'] = False
        # User of group TMS Add User To Host can edit users of host only
        current_user = self.env['res.users'].browse(self._uid)
        if not current_user.has_full_sysadmin_access and \
                current_user.has_groups('tms_modules.group_add_user_to_host'):
            if not 'bypass_security' in self._context and \
                    not ('user_ids' in vals and len(vals) == 1):
                raise Warning(
                    'Warning',
                    'You only allow modify users of host!')

        vals['update'] = time.strftime("%Y-%m-%d")
        return super(tms_host, self).write(vals)

    @api.multi
    def name_get(self):
        return [(host.id, u"{0} ({1})".format(
            host.name, host.physical_host_id.name)) if host.physical_host_id
            else (host.id, u"{0}".format(host.name)) for host in self]
