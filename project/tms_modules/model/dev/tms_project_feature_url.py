# -*- encoding: utf-8 -*-
from openerp.osv import osv, fields


class tms_project_feature_url(osv.Model):

    _name = "tms.project.feature.url"
    _description = "tms_project_feature_url"

    _columns = {
        "customer_id": fields.many2one("res.users", string="Customer"),
        "name": fields.char(size=256, string="Name", required=True),
        "url": fields.text(string="URL", required=True),
        "description": fields.text(string="Description")
    }
