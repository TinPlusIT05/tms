openerp.unleashed.module("tms_audit").ready(

    function(instance, tms_audit, _, Backbone, base){

        var BaseModel = base.models("BaseModel");

        var AuditBoard = BaseModel.extend({

            model_name: "tms.audit.board"
        });

        tms_audit.models("audit_board", AuditBoard);
    }
);