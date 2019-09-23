openerp.unleashed.module('tms_audit').ready(function(instance, tms_audit, _, Backbone, base) {

	var View = Backbone.Marionette.ItemView;

	var Buttons = View.extend({

		template: 'audit.board.list.view.buttons',

		ui: {

			'create': '.btn_create',

            'full_screen': '.btn_full_screen'
		},

		events: {

			'click .btn_create': 'createRecord',

            'click .btn_full_screen': 'enterFullScreenMode'
		},

		createRecord: function(){

			tms_audit.trigger('open:record', this.collection.model_name, null);
		},

        enterFullScreenMode: function(){

            tms_audit.trigger('fullscreen', true);
        }
	});

	tms_audit.views('Buttons', Buttons);
});