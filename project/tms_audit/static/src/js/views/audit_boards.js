openerp.unleashed.module("tms_audit").ready(

    function(instance, tms_audit, _, Backbone, base){

        var CompositeView = Backbone.Marionette.CompositeView,
            _super = CompositeView.prototype,
            AuditBoard = tms_audit.views("audit_board");

        var AuditBoards = CompositeView.extend({

            itemView: AuditBoard,

            template: "audit.boards.comp.view",

            itemViewContainer: ".rows-container",

            serializeData: function(){

                var result = _super.serializeData.apply(this, arguments);

                var pass_percentage = 0, failed_percentage = 0;

                // for each project
                this.collection.each(function(project){

                    var project_health = project.get("project_health");

                    pass_percentage += project_health;

                    failed_percentage += (100.00 - project_health);
                });

                var total   = pass_percentage + failed_percentage,
                    pass    = Number(pass_percentage / total * 100).toFixed(2),
                    failed  = Number(100.00 - 82.95).toFixed(2);

                var pass_output = pass > 0 ? pass.toString() + "%" : "",
                    failed_output = failed > 0 ? failed.toString() + "%" : "";

                Backbone.$.extend(result, {
                    global_project_health_success: pass_output,
                    global_project_health_failed: failed_output
                });

                return result;
            }
        });

        tms_audit.views("audit_boards", AuditBoards);
    }
);