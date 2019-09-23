openerp.unleashed.module('booking_chart').ready(

	function (instance, booking, _, Backbone, base) {
		
		var Resource = booking.collections('Resources'),
			_superRes = Resource.prototype;
			
		var Group = _superRes.collection_group,
			_superGroup = Group.prototype;
			
		_.extend(_superGroup, {
			label: function(){
	            var title = [];
	            var numbers = [];
	            this.each(function(model){
	            	var _model = model.get("resource_model"),
	            		name = model.get("name");
	
	                title.push(name);
	
	                if(_model == "hr.employee") {
	                	var _n = name.split(" ")[0];
	                	var _p = _n.substring(_n.indexOf("[") + 1, _n.indexOf("%]"));

	                	// convert to boolean expression !!
	                	/(^[0-9]+$)|(^[0-9]+(\.){1}\d+$)/gi.test(_p) && numbers.push(parseFloat(_p));
	                }
	            });
	            
	            var result = title.join(', ');
	
	            if (!_.isEmpty(numbers)) {
	
	            	var sum = numbers.reduce(function(sum, el) {
						return sum + el
					}, 0);
	
	            	result = ["[", sum, "% Total]", " - ", result].join("");
	            }
	
	            return result;
	        }
		});
	}
);