openerp.unleashed.module("web_hide_export", function(hide_export,  _, Backbone, base){
	
	var BaseModel = base.models("BaseModel");
	
	var UserModel = BaseModel.extend({
		model_name: "res.users"
	})

	hide_export.models("User", UserModel);
});