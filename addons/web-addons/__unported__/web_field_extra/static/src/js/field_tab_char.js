openerp.unleashed.module('web_field_extra').ready(function(instance){

   	var form_view  = instance.web.FormView;
    var FieldTabChar = instance.web.form.FieldChar.extend({
        events : {
            'change input' : 'store_dom_value',
            // FIXME: more clear with a method 
            'keydown' : function(e) {
                if (e.which == 9) {
                    try {
                        form_view.fieldInput = this.$('input:first')[0];
                        form_view.fieldName = this.name;
                    } catch (err) {
                        return;
                    }
                }
            },

        },
        format_value : function(val, def) {
            if (val === "") {
                val = false;
            }
            return instance.web.format_value(val, this, def);
        },
    });
    
    instance.web_field_extra.FieldTabChar = FieldTabChar;
    instance.web.form.widgets.add('TabCharWidget', 'openerp.web_field_extra.FieldTabChar');
});
