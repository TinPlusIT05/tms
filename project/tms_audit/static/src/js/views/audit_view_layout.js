openerp.unleashed.module("tms_audit").ready(

    // This is the layout will be used by the audit view
    // allow user to access most of view components like
    // buttons on the top, pagination etc ....

    // callback function when loading successfully
    function(instance, tms_audit, _, Backbone, base){

        var PanelLayout = base.views("Panel");

        var AuditBoardListViewLayout = PanelLayout.extend({

            regions: {
                "audit": ".audit-board-list-contents"
            }
        });

        tms_audit.views("AuditBoardListViewLayout", AuditBoardListViewLayout)
    }
);