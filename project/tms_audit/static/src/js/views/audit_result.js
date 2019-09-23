openerp.unleashed.module("tms_audit").ready(

    function(instance, tms_audit, _, Backbone, base) {

        var ItemView = Backbone.Marionette.ItemView;

        var AuditResult = ItemView.extend({

            tagName: "tr",

            template: "audit.result.item.view"
        });


        tms_audit.views("audit_result", AuditResult);

    }
);