# Project

Base projects are used as a template to create project specific repositories, they have pre-installed Odoo source code + some default Trobz addons added as subtree.

## Subtrees

- Odoo 8.0, from git@gitlab.trobz.com:odoo/odoo.git, branch `8.0-master`
- Addons Trobz, from git@gitlab.trobz.com:odoo/addons-trobz.git, branch `8.0-master`
- Web Addons, from git@gitlab.trobz.com:odoo/web-addons.git, branch `8.0-master`
- Web Unleashed, from git@gitlab.trobz.com:odoo/web-unleashed.git, branch `8.0-master`
- Server Tools, from git@gitlab.trobz.com:odoo/server-tools.git, branch `8.0-master`

You can update them with a `git subtree pull`.

## Command

### start.sh

`./bin/start.sh` start Odoo server will a pre-configured `--addons-path` and `--config` options. 

You can add more addons specific to your project by editing the `ADDONS` variable in `start.sh` script.

Usage: 
```
./bin/start.sh [optional openerp-server arguments]
```

### update.sh

`/bin/update.sh` will update ```trobz_base``` module on the configured database.

You can add more modules to update by passing them in argument to `update.sh` command.

You can update the default module updated and the target database specific to your project by editing `UPDATE` and `DATABASE` variable in `update.sh` script.

Usage:
```
./bin/update.sh [module1] [module2] [moduleN]
```

### git-subtree.sh

This script will handle the compilation/installation of git 2.1.2 + subtree contrib plugin. 

Required on ubuntu 12.04, optional in 14.04 (the official git package already include subtree plugin).

## Config file

By default, `start.sh` script use `./config/dev.conf` as the default `openerp-server.conf` file, you can customize it according to your project.

