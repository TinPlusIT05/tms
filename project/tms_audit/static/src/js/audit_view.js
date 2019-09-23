openerp.unleashed.module("tms_audit").ready(

    // callback function when loading successfully
    function(instance, tms_audit, _, Backbone, base){

        // base Unleashed View
        var UnleashedView = base.views("Unleashed");

        // add audit board view list to native view system
        instance.web.views.add('tms_audit_board_list', 'instance.tms_audit.tms_audit_board_list');

        // Audit Board List View Layout
        var AuditBoardListViewLayout = tms_audit.views("AuditBoardListViewLayout");

        // create new view type tms_audit
        instance["tms_audit"].tms_audit_board_list = UnleashedView.extend({

            view_type: "tms_audit_board_list",

            template: "tms_audit_board_list_view",

            displayName: base._lt("TMS Audit Board List View"),

            module: tms_audit,

            // layout for the entire audit list view, including some region
            // configs inside through the layout, we provide `audit_list`
            // region to be the container for our custom list view can be
            // through `this.panel.audit_list`
            Panel: AuditBoardListViewLayout,

            start: function(){

                // get audit board collection
                var AuditBoardCollection = tms_audit.collections("audit_boards");

                // get related view (pager, button, audit board composite view)
                var Pager = base.views("Pager"),
                    Buttons = tms_audit.views("Buttons"),
                    AuditBoards = tms_audit.views("audit_boards");

                // create audit boards as collection
                this.collection = new AuditBoardCollection();

                this.views = {
                    pager: new Pager({
                        collection: this.collection
                    }),
                    buttons: new Buttons({
                        collection: this.collection
                    }),
                    audit: new AuditBoards({
                        collection: this.collection
                    })
                };

                return this._super.apply(this, arguments);
            },

            ready: function(){
                tms_audit.on('fullscreen', this.fullscreen, this);

                this.panel.pager.directShow(this.views.pager);
                this.panel.buttons.directShow(this.views.buttons);
            },


            fullscreen: function(enter){

                if(enter){
                    this.enterFullscreen();
                }
                else {
                    this.exitFullscreen();
                }
            },

            enterFullscreen: function(){

                var element = this.$el.parent().get(0);

                if (element.requestFullScreen) {
                    element.requestFullScreen();
                }
                else if (element.mozRequestFullScreen) {
                    element.mozRequestFullScreen();
                }
                else if (element.webkitRequestFullScreen) {
                    element.webkitRequestFullScreen();
                }

                this.$el.parent().addClass('fullscreen');
            },

            exitFullscreen: function(){

                if(document.cancelFullScreen) {
                    document.cancelFullScreen();
                }
                else if(document.mozCancelFullScreen) {
                    document.mozCancelFullScreen();
                }
                else if(document.webkitCancelFullScreen) {
                    document.webkitCancelFullScreen();
                }

                this.$el.parent().removeClass('fullscreen');
            },

            do_search: function(domain, context){

                var self = this;

                this.collection.load({
	                filter: domain,
	                context: context,
	                persistent: true
	            })
                .then(
                    function(){
                        self.panel.audit.directShow(self.views.audit);
                    }
                )
            }
        })
    }
);