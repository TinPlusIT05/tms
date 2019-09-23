openerp.unleashed.module("tms_audit").ready(

    function(instance, tms_audit, _, Backbone, base){

        var CompositeView = Backbone.Marionette.CompositeView,
        	ItemView = Backbone.Marionette.ItemView,
        	_superItemView = ItemView.prototype;

            AuditResult = tms_audit.views("audit_result");

        var AuditResults = CompositeView.extend({

            itemView: AuditResult,

            template: "audit.results.comp.view",

            itemViewContainer: "tbody"
        });
        
        /*
         * Audit result Error Item view
         * Show the error message when auditing
         */
        var AuditResultsError = ItemView.extend({
        	template: "audit.result.error.item.view",
        		
        	initialize: function(options){
        		this.error_message = options.error_message;
        	},
        	serializeData: function(){
        		var result = _superItemView.serializeData.apply(this, arguments);
                _.extend(result, {
                	error_message: this.error_message
                });
                return result;
        	}
        	
        });        

        tms_audit.views("audit_results", AuditResults);
        tms_audit.views("audit_results_error", AuditResultsError);
    }
);