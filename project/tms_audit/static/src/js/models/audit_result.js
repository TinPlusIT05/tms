openerp.unleashed.module("tms_audit").ready(

    function(instance, tms_audit, _, Backbone, base){

        var BaseModel = base.models("BaseModel");

        var AuditResult = BaseModel.extend({

            model_name: "tms.audit.result"
        });

        tms_audit.models("audit_result", AuditResult);
    }
);