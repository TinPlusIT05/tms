openerp.unleashed.module("tms_audit").ready(

    function(instance, tms_audit, _, Backbone, base){

        var Pager = base.collections("Pager"),
            AuditBoardModel = tms_audit.models("audit_board");

        var AuditBoards = Pager.extend({

            model_name: "tms.audit.board",

            model: AuditBoardModel
        });

        tms_audit.collections("audit_boards", AuditBoards);
    }
);