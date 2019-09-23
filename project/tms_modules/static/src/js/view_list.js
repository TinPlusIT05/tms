openerp.unleashed.module('tms_modules').ready(function(instance, tms_module, _, Backbone, base){

	var _t = instance.web._t;

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
	});

	instance.web.ListView.include({

		init: function(parent, dataset, view_id, options) {
			this._super(parent, dataset, view_id, options);
			this.classTarget = null;
		},
		
		load_list: function(data) {

			this._super(data);

			if(this.dataset.model === "tms.support.ticket"){

				// make sure sidebar is already populated
		        if (this.sidebar && this.options.$sidebar) {

		            // show export if permission check is valid
		            this.user_export_permitted().done(function(exportPermitted){
		                if (!exportPermitted) {
		                    this.sidebar.remove_items('other', _.compact([
								{ label: _t("Export"), callback: this.on_sidebar_export }
							]));
		                }
		            }.bind(this));
		        }
			}
			
			if (this.fields_view.arch.attrs.classTarget) {
	            this.classTarget = _(this.fields_view.arch.attrs.classTarget.split(';')).chain()
	                .compact()
	                .map(function(classTarget_pair) {
	                    var pair = classTarget_pair.split(':'),
	                    	classTarget = pair[0],
	                        expr = pair[1];
	                    return [classTarget, py.parse(py.tokenize(expr)), expr];
	                }).value();
	        }
		},

		// get current user profile to restrict
		user_export_permitted: function(){

			var UserModel = base.models('BaseModel').extend({ model_name: 'res.users'});
			var userModel = new UserModel();

			return userModel.sync('call', { model_name: userModel.model_name }, {
				method: "user_export_permitted", args: []
			});
		},
		
		class_for: function (record) {
	        var len, cls= '';

	        var context = _.extend({}, record.attributes, {
	            uid: this.session.uid,
	            current_date: new Date().toString('yyyy-MM-dd')
	            // TODO: time, datetime, relativedelta
	        });
	        var i;
	        var pair;
	        var expression;

	        if (!this.classTarget) { return cls; }
	        for(i=0, len=this.classTarget.length; i<len; ++i) {
	            pair = this.classTarget[i];
	            var class_name = pair[0];
	            expression = pair[1];
	            if (py.evaluate(expression, context).toJSON()) {
	                return cls += class_name;
	            }
	            // TODO: handle evaluation errors
	        }
	        return cls;
	    },
	});

	instance.web.ListView.List.include({
		render_cell: function (record, column){
            // default rendered value for the field
            var rendered_value = this._super.apply(this, arguments);

            var forge = new openerp.Model("tms.forge.ticket");
            var forge_id;
            if(this.dataset.model === "tms.forge.ticket"){
                var def = $.Deferred();
                // modify QC Estimation
            	if (column['string'] === "QC Estimate (h)") {
                    // get forge ticket number
                    forge_id = record.get('name');
                    // hidden QC Estimation number
                    forge.call("is_remove_qc_estimation", [[forge_id]]).done(function(result){
                        is_remove = result;
                        this.is_rm = is_remove;
                        if (is_remove === true) {
                            record.set(column.id, 0);        
                        }
                    });
            	}
            }
			return rendered_value;
        },
	});
});