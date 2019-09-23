openerp.unleashed.module("tms_audit").ready(

    function(instance, tms_audit, _, Backbone, base){

        var OpenRegion = base.views("Region");

        var Layout = Backbone.Marionette.Layout,
            _super = Layout.prototype;

        var AuditResultsCollection = tms_audit.collections("audit_results"),
            AuditResultsView = tms_audit.views("audit_results");
        	AuditResultsErrorView = tms_audit.views("audit_results_error");

        // instead of using item view, we use Layout because one
        // row displayed in the table could have extra hidden contents
        // in this case is the information about all the audit tests of
        // an project, these information are only shown when user clicking
        // on a button available in each row layout
        var AuditBoard = Layout.extend({

            tagName: "tbody",

            template: "audit.board.layout.view",

            regionType: OpenRegion,

            attributes: function(){

                return {

                    "data-model": this.model.model_name,

                    "data-model-id": this.model.get("id")
                }
            },

            regions: {

                // project test information (failed, pass, health)
                audit_board_info: ".audit-board-row",

                // project executed test results
                audit_test_results: ".audit-test-results td.results"
            },

            ui: {

                // project test information (failed, pass, health)
                audit_board_info: ".audit-board-row",

                // project executed test results
                audit_test_results: ".audit-test-results"
            },

            events: {

                "click .audit-board-row": "onOpenAuditBoardRecord",

                "click .btn-view-test-details": "onFetchAuditTestResults"
            },

            onOpenAuditBoardRecord: function(){

                tms_audit.trigger(

                    "open:record", this.model.model_name, this.model.id
                );
            },

            onFetchAuditTestResults: function($event){

                $event.stopImmediatePropagation();

                var self = this,
                    test_results_ids = this.model.get("audit_test_result_ids");

                var $toggle_icon = this.$(".btn-view-test-details");
            	
                // if there is an error message which need to show in audit board
            	if (this.model.get('error_message')){
            		
	                    if (!self.model.has("audit_test_results_error")){
	                		var resultsErrorView = new AuditResultsErrorView({
	                			error_message: this.model.get('error_message')
	                		});
	                		self.model.set("audit_test_results_error", resultsErrorView)
	                		self.audit_test_results.directShow(resultsErrorView);
	                		$toggle_icon.removeClass("fa-chevron-up").addClass("fa-chevron-down");
                    	
	                    }
		                else {
		            		if (self.audit_test_results.$el.is(":visible")){
		                        $toggle_icon.removeClass("fa-chevron-down").addClass("fa-chevron-up");
		                    }
		                    else {
		                        $toggle_icon.removeClass("fa-chevron-up").addClass("fa-chevron-down");
		                        
		                    }
		            		self.audit_test_results.$el.toggle();
		                }

		                return;
            	}
            		
                

                if (test_results_ids && this.model.has("audit_test_results")) {

                    if(self.audit_test_results.$el.is(":visible")){

                        $toggle_icon.removeClass("fa-chevron-down").addClass("fa-chevron-up");
                    }
                    else {
                        $toggle_icon.removeClass("fa-chevron-up").addClass("fa-chevron-down");
                    }

                    self.audit_test_results.$el.toggle();
                }
                else {

                    var resultsCollection = new AuditResultsCollection(),
                        resultsView = new AuditResultsView({
                            collection : resultsCollection
                        });

                    resultsCollection.fetch({
                        filter: [["id", "in", test_results_ids]]
                    })
                    .then(
                        function(){

                            // next time don't fetch, just show it
                            self.model.set("audit_test_results", resultsCollection);
                            self.audit_test_results.show(resultsView);

                            $toggle_icon.removeClass("fa-chevron-up").addClass("fa-chevron-down");
                        }
                    );
                }
            },

            serializeData: function(){

                var data = _super.serializeData.apply(this, arguments);

                var health = data["project_health"];

                // get the remaining undone and process the display progress
                var remaining = (_.isNumber(health) ? 100.00 - health : 0).toFixed(2),
                    success_text = _.isNumber(health) ? health + "%" : "",
                    remaining_text = _.isNumber(health) && remaining ? remaining + "%" : "";

                _.extend(data, {

                    progress_bar: {

                        success: {
                            percentage: health,
                            text: success_text
                        },

                        failed: {
                            percentage: remaining,
                            text: remaining_text
                        }
                    }
                });

                return data;
            },

            // FIXME this method decides how to render each row in the test result table
            processResultDisplay: function(){


            }
        });

        tms_audit.views("audit_board", AuditBoard);
    }
);