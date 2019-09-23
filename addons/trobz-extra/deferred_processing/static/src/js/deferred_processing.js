openerp.deferred_processing = function (session) {
    var _t = session.web._t,
       _lt = session.web._lt;

    /**
     * ------------------------------------------------------------
     * Open list of Deferred Processes
     * ------------------------------------------------------------
     * 
     * Add a link on the top user bar for open my deferred process button
     */
    session.web.OpenDeferred = session.web.Widget.extend({
        template:'deferred_processing.OpenDeferred',

        start: function () {
            this.$('button').on('click', this.on_call_token );
            this._super();
        },

        on_call_token: function (event) {
            event.stopPropagation();
            var action = {
                name: _t("My Deferred Processes"),
                type: 'ir.actions.act_window',
                res_model: 'deferred_processing.task',
                view_type : "list",
                view_mode : "list",
                views: [[false, 'list'], [false, 'form']],
                context: {},
            };
            session.client.action_manager.do_action(action);
        },

    });

    session.web.UserMenu.include({
        do_update: function(){
            var self = this;
            this._super.apply(this, arguments);
            this.update_promise.then(function() {
                var ct_button = new session.web.OpenDeferred();
                ct_button.prependTo(session.webclient.$el.find('.oe_systray'));
            });
        },
    });

};
