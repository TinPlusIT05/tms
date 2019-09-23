openerp.trobz_base = function(instance){

	var QWeb = instance.web.qweb;
	_t = instance.web._t;

	instance.web.CrashManager.include({
		show_error: function(error) {
			if (!this.active) {
			    return;
			}
			
			var $currentDate = new Date();
	    	var $day = $currentDate.getDate();
	    	if ($day < 10)
	    		$day = "0" + $day;
	    	var $month = $currentDate.getMonth() + 1;
	    	if ($month < 10)
	    		$month = "0" + $month;
	    	var $year = $currentDate.getFullYear();
	    	var $hours = $currentDate.getHours();
	    	if ($hours < 10)
	    		$hours = "0" + $hours;
	    	var $minutes = $currentDate.getMinutes();
	    	if ($minutes < 10)
	    		$minutes = "0" + $minutes;
	    	var $seconds = $currentDate.getMinutes();
	    	if ($seconds < 10)
	    		$seconds = "0" + $seconds;
	    	var $now = $year + "-" + $month + "-" + $day + " " + $hours + ":" + $minutes + ":" + $seconds;

	    	error.data.message = error.message;
	    	new instance.web.Model('trobz.maintenance.error').call('send', [error.data, $now]).then(function(result) {
			    if (result === false) {
			        alert('There was a communication error.');
			    }
	    	});
		    	
	    	var buttons = {};
	        buttons[_t("Ok")] = function() {
	            this.parents('.modal').modal('hide');
	        };
	        new instance.web.Dialog(this, {
	            title: "Odoo " + _.str.capitalize(error.type),
	            buttons: buttons
	        }, QWeb.render('CrashManager.error', {session: instance.session, error: error})).open();
	    },
	});
	
	
	instance.web.FormView.include({

		load_form: function() {
			var self = this;
		    return this._super.apply(this, arguments).then(function() {
		    	if (self.sidebar) {
			    	//Trobz: add button More > View Log
		            self.sidebar.add_items('other', _.compact([
		                { label: _t('View Metadata'), callback: self.on_button_view_metadata }
		            ]));
	            }
		    	return $.when();
		    });
		},

		on_button_view_metadata: function() {
			var self = this;
			var id = [self.datarecord.id];
		    this.dataset.call('get_metadata', [id]).done(function(result) {
		        var dialog = new instance.web.Dialog(this, {
		            title: _.str.sprintf(_t("View Metadata (%s)"), self.dataset.model),
		            size: "medium"
		        }, QWeb.render('ViewManagerDebugViewLog', {
		            perm : result[0],
		            format : instance.web.format_value
		        })).open();
		    });
		},
	});
}
