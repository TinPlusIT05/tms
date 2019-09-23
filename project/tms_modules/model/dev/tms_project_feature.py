# -*- encoding: UTF-8 -*-
from openerp.osv import osv, fields
from collections import defaultdict


class tms_project_feature(osv.Model):

    _name = "tms.project.feature"
    _description = "tms_project_feature"

    PROJECT_FEATURE_DEV_STATE = [
        ("development", "Development"),
        ("qa", "QA"),
        ("ready", "Ready")
    ]

    PROJECT_FEATURE_STATE = [
        ("development", "Development"),
        ("ready_for_validation", "Ready for Validation"),
        ("validated", "Validated"),
        ("cancelled", "Cancelled")
    ]

    def fnct_get_tags_comma_combination(
            self, cr, uid, ids, field, arg, context=None):
        """
            Return a string which is a combination of tags name
            separated by a comma, useful for contents tag search
        """
        if context is None:
            context = {}
        results, features = {}, self.browse(cr, uid, ids, context=context)
        for feature in features:
            tag_names = [tag.name for tag in feature.tag_ids]
            results[feature.id] = ", ".join(tag_names)
        return results

    def fnct_get_progress_char(self, cr, uid, ids, field, name, context=None):
        if context is None:
            context = {}
        results, features = {}, self.browse(cr, uid, ids, context=context)
        for feature in features:
            formatted = feature.progress and "{0} %".format(
                feature.progress) or "0 %"
            results[feature.id] = formatted
        return results

    def fnct_get_dev_status(self, cr, uid, ids, field, name, context=None):
        if context is None:
            context = {}
        results, features = {}, self.browse(cr, uid, ids, context=context)
        groups = defaultdict(list)
        for feature in features:

            # Group the state for tickets in each feature
            for ticket in feature.forge_ids:
                groups[ticket.state].append(ticket)

            # Classify and check
            ticket_statuses = groups.keys()

            if "assigned" in ticket_statuses or\
               "wip" in ticket_statuses:
                results[feature.id] = "development"

            elif "code_completed" in ticket_statuses or\
                 "ready_to_deploy" in ticket_statuses or\
                 "in_qa" in ticket_statuses:
                results[feature.id] = "qa"

            else:
                results[feature.id] = "ready"
        return results

    def store_fnct_get_changed_tag_ids_feature(
            self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return ids

    def store_fnct_get_changed_tag_name_project_tag(
            self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        feature_pool = self.pool.get("tms.project.feature")
        feature_ids = feature_pool.search(cr, uid, [], context=context)
        features = feature_pool.browse(cr, uid, feature_ids, context=context)
        result = []
        # For each changed tag that user made change
        for _tag_id in ids:
            for feature in features:
                # Check if the changed tag is in list of feature's tags
                feature_tag_ids = [tag.id for tag in feature.tag_ids]
                if _tag_id in feature_tag_ids:
                    result.append(feature.id)
        return result

    _columns = {
        "summary": fields.char(size=256, string="Summary", required=True),
        "comment": fields.text(string="Comment"),
        "link": fields.text(string="Link"),

        "project_id": fields.many2one(
            "tms.project", string="Project", required=True),

        "group_id": fields.many2one(
            "tms.project.feature.group", string="Feature Group",
            domain="[('project_id','=',project_id)]", required=True),

        "milestone_id": fields.many2one(
            "tms.milestone", string="Milestone",
            domain="[('project_id','=',project_id)]", required=True),

        "workload": fields.float(
            digits=(15, 3), string="Workload", required=True),

        "progress": fields.integer(
            string="Progress (%)"),

        "progress_char": fields.function(
            fnct_get_progress_char, type="char", string="Progress (%)"),

        "forge_ids": fields.many2many(
            "tms.forge.ticket", "tms_project_feature_forge_rel",
            "feature_id", "forge_id", string="Forge Tickets",
            groups="base.group_user",
            domain="[('project_id','=',project_id)]"),

        "tag_ids": fields.many2many(
            "tms.project.feature.tag", "tms_project_feature_tag_rel",
            "feature_id", "tag_id", string="Feature Tags",
            domain="[('project_id','=',project_id)]"),

        "tags_char": fields.function(
            fnct_get_tags_comma_combination, type="char", string="Tags",
            store={
                "tms.project.feature": (
                    store_fnct_get_changed_tag_ids_feature, ["tag_ids"], 10),
                "tms.project.feature.tag": (
                    store_fnct_get_changed_tag_name_project_tag, ["name"], 10),
            }
        ),

        "dev_status": fields.function(
            fnct_get_dev_status, type="selection",
            selection=PROJECT_FEATURE_DEV_STATE, string="Dev Status"),

        "state": fields.selection(
            selection=PROJECT_FEATURE_STATE, string="Status", required=True),
    }

    _defaults = {
        "workload": 0,
        "progress": 0,
        "state": "development",
    }

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}

        # If user updating the state of the feafure
        if vals.get("state"):

            # If state in > set progress as 100%
            states = ("ready_for_validation", "validated")
            if vals.get("state") in states:
                vals["progress"] = 100

        return super(tms_project_feature, self).write(
            cr, uid, ids, vals, context=context)

    def onchange_project_id(self, cr, uid, ids, project_id, context=None):
        if context is None:
            context = {}
        to_return_vals = {
            "group_id": False,
            "milestone_id": False,
            "forge_ids": [], "tag_ids": [],
        }
        return {"value": to_return_vals}

    def button_ready(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        update_vals = {"state": "ready_for_validation"}
        self.write(cr, uid, ids, update_vals, context=context)

    def button_validate(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        update_vals = {"state": "validated"}
        self.write(cr, uid, ids, update_vals, context=context)

    def button_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        update_vals = {"state": "cancelled"}
        self.write(cr, uid, ids, update_vals, context=context)
