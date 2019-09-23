/**
 * The purpose of this file is to create color picker widget for form field,
 * original implementation is on kanban view > migrate feature to form view.
 *
 * TODO: should create a new module for this widget in-case there are another
 * projects use this widget
 **/
openerp.unleashed.module("tms_modules").ready(function(instance, markdown, _){

    // create new widget
    instance.web.form.ColorPicker = instance.web.form.AbstractField.extend(instance.web.form.ReinitializeFieldMixin, {

        number_of_color_schemes: 10,

        template: "FormViewFieldColorPicker",

        events: {
            "click .color": "onColorSelect",
        },

        init: function (field_manager, node) {
            this._super(field_manager, node);
        },

        get_field_value: function() {
            return this.get("value");
        },

        onColorSelect: function(event) {
            event.preventDefault();
            if (!this.get('effective_readonly')) {
                $(event.currentTarget).addClass("selected").siblings().removeClass("selected");
                this.store_dom_value();
            }
        },

        store_dom_value: function() {
            if (!this.get('effective_readonly')) {
                var $selected = this.$(".selected"),
                    value = $selected.find("a").data("color");
                this.set("value", value);
            }
        }
    });

    instance.web.form.widgets.add("color_picker", "instance.web.form.ColorPicker");
});