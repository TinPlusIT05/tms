# -*- encoding: utf-8 -*-
from openerp.osv import osv, fields


class tms_project_feature_group(osv.Model):

    _name = "tms.project.feature.group"
    _description = "tms_project_feature_group"

    def fnct_get_progress_remaining_workload(
            self, cr, uid, ids, field, name, context=None):
        if context is None:
            context = {}
        result = {}

        for _group_id in ids:

            # Get feature belong to this group
            feature_pool = self.pool.get("tms.project.feature")
            feature_domain = [
                ('group_id', '=', _group_id), ('state', '!=', 'cancelled')]
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

            # Initial value (reset for each iteration)
            workload = progress = 0

            # make sure this group is not empty
            if features:

                # Get sum of all features workload
                feature_workloads = sum(
                    [feature.workload for feature in features])

                # Calculate workload (for this group)
                workload = sum(
                    [feature_workloads * (1 - feature.progress)
                     for feature in features])

                # Calculate progress (for this group)
                numerator = sum(
                    [feature_workloads * feature.progress
                     for feature in features])
                progress = feature_workloads and numerator / \
                    feature_workloads or 0

            result.update({_group_id: {
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
            fnct_get_progress_remaining_workload, multi=True,
            type="float", digits=(15, 3), string="Remaining Workload")
    }
