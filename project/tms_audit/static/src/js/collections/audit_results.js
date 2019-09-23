openerp.unleashed.module("tms_audit").ready(

    function(instance, tms_audit, _, Backbone, base){

        var Pager = base.collections("Pager"),
            AuditResultModel = tms_audit.models("audit_result");

        var AuditResults = Pager.extend({

            model_name: "tms.audit.result",

            model: AuditResultModel
        });

        tms_audit.collections("audit_results", AuditResults);
    }
);