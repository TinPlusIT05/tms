openerp.unleashed.module("web_hide_export").ready(function(instance, hide_export,  _, Backbone, base){

	var _t = instance.web._t;
	var UserModel = hide_export.models("User");
	
	instance.web.Sidebar.include({
		/**
		 * Add a function that allow to remove items from sidebar
		 **/
		remove_items: function(section_code, items){
			var self = this, current_bar_node = self.items[section_code];
	        if (items) {
	        	// FIXME: remove_items function get called twice while items.length = 1
	        	_.each(items, function(to_remove_item){
	        		var to_remove = _.find(current_bar_node, function(sidebar_item){
	        			return sidebar_item.label === to_remove_item.label;
	        		});
	        		to_remove && current_bar_node.splice(current_bar_node.indexOf(to_remove), 1);
	        	});
	        	this.redraw();
	        }
		}
	})

	instance.web.ListView.include({
		/** 
		 * Override the default load_list setup for side bar in
		 * native openerp to show or not to show the export feature 
		 * using permission validation
		 **/
		load_list: function(data) {

	        this._super(data);

	        // make sure sidebar is already populated
	        if (this.sidebar && this.options.$sidebar) {

	            // show export if permission check is valid	            
	            this.check_user_export_right().done(function(exportPermitted){
	            	if (!exportPermitted) {
	            		/* 
	            		 * please make sure you have patched the .rng from the server to allow "export" 
	            		 * attribute support for tree view, otherwise (remove the left check operand)
	            		 * (openerp/addons/base/rng/view.rng)
	            		 */
	            		this.sidebar.remove_items('other', _.compact([
							{ label: _t("Export"), callback: this.on_sidebar_export }
						]));
	            	}
	            }.bind(this));
	        }
	    },
		
		check_user_export_right: function(){
			var userModel = new UserModel();

			/* call check access right on the server */
			return userModel.sync("call", { model_name: userModel.model_name }, {
				method: "client_check_access_rights", args: [this.dataset.model, "export"]
			});
		}
	});
});