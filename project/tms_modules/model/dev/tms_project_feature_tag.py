# -*- encoding: utf-8 -*-
from openerp.osv import osv, fields


class tms_project_feature_tag(osv.Model):

    _name = "tms.project.feature.tag"
    _description = "tms_project_feature_tag"

    def fnct_get_progress_remaining_workload(
            self, cr, uid, ids, field, name, context=None):
        if context is None:
            context = {}
        result = {}

        # Get all non-cancelled features
        # the reason why get feature here because the relation
        # between Tag and Feature are many2many
        feature_pool = self.pool.get("tms.project.feature")
        feature_domain = [('state', '!=', 'cancelled')]
        feature_ids = feature_pool.search(
            cr,
            uid,
            feature_domain,
            context=context)
        features = feature_ids and feature_pool.browse(
            cr,
            uid,
            feature_ids,
            context=context)

        for _tag_id in ids:

            # Initial value (reset for each iteration)
            workload = progress = 0

            # Make sure this tag is not empty
            if features:

                # Get a list of feature associated with this tag (many2many)
                tag_features_list = [
                    feature for feature in features if _tag_id in [
                        tag.id for tag in feature.tag_ids]]

                # Get sum of all features workload
                feature_workloads = sum(
                    [feature.workload for feature in tag_features_list])

                # Calculate workload (for this tag)
                workload = sum(
                    [feature_workloads * (1 - feature.progress)
                     for feature in tag_features_list])

                # Calculate Progress (for this tag)
                numerator = sum(
                    [feature_workloads * feature.progress
                     for feature in tag_features_list])
                progress = feature_workloads and numerator / \
                    feature_workloads or 0

            result.update({_tag_id: {
                "progress": progress,
                "remaining_workload": workload
            }})

        return result

    _columns = {
        "project_id": fields.many2one("tms.project", string="Project",
                                      required=True),
        "name": fields.char(size=256, string="Name", required=True),

        "progress": fields.function(fnct_get_progress_remaining_workload,
                                    type="float", digits=(15, 0),
                                    string="Feature Progress", multi=True),

        "remaining_workload": fields.function(
            fnct_get_progress_remaining_workload, type="float",
            digits=(15, 3), string="Remaining Workload", multi=True)
    }
