openerp.unleashed.module('tms_modules').ready(

    function(instance, tms_module, _, Backbone, base) {

        instance.web.WebClient.include({

            init: function (parent, client_options) {

                this._super.apply(this, arguments);

                this.set('title_part', {"zopenerp": "TMS"});
            }
        });
    }
);