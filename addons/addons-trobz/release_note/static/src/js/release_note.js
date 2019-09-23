/*---------------------------------------------------------
 * Trobz: Web Release Note
 *---------------------------------------------------------*/

openerp.release_note = function(instance){

	var QWeb = instance.web.qweb;

	instance.web.ReleaseUserMenu =  instance.web.UserMenu.include({
		init: function(){
			this._super.apply(this, arguments);
			this.fetched = false;
		},
		start: function() {
	        var self = this;
	        this._super.apply(this, arguments);
		},
		on_menu_release_note: function() {
	        var self = this;
	        var deff = $.when();

	        if(!this.fetched){
	        	deff = deff.then(function(){
	        		return self.rpc("/web/webclient/release_note", {}).done(function(res) {
	        			html = "<div class='release-note-popup'>" + marked(res) + "</div>"
			            self.$('#release-note-hidden').magnificPopup({
							  items: {
							      src: $(html),
							      type: 'inline'
							  }
						});
			    		self.fetched = true;
			    		return $.when();
			        });
	        	});
	        }
	        return deff.then(function(){
	        	self.$('#release-note-hidden').trigger("click");
	        })
	    },
	});

}