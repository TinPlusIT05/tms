openerp.unleashed.module('web_field_extra').ready(function (instance) {

    var FieldBarcode = instance.web.form.FieldChar.extend({
        events: {
            'keyup': function (e) {
                var input = this.$('input:first')[0]
                if (input.value.length > 12) {
                        this.commit_value()
                }
            }

        }
    });

    instance.web_field_extra.FieldBarcode = FieldBarcode;
    instance.web.form.widgets.add('barcode', 'openerp.web_field_extra.FieldBarcode');
});