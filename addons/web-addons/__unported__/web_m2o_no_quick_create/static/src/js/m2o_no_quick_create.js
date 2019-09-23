openerp.unleashed.module('web_m2o_no_quick_create').ready(function(instance){

    instance.web.form.FieldMany2One = instance.web.form.FieldMany2One.extend({

        init: function(field_manager, node) {
            this._super(field_manager, node);

            //disable create and edit_create by default
            if(!this.options.hasOwnProperty('create_edit')){
                this.options.create_edit = false;
            }
            if(!this.options.hasOwnProperty('create')){
                this.options.create = false;
            }
        }
    });

});