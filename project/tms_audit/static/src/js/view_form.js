openerp.unleashed.module('tms_audit').ready(

    function(instance){

        // create a custom progress bar that uses bootstrap
        // for consistency display on the list and the form,
        // the native progress bar is too ugly.
        instance["tms_audit"].audit_progress_bar = instance.web.form.FieldProgressBar.extend({

            template: "tms_audit_progress_bar",

            render_value: function(){

                var value = parseFloat(instance.web.format_value(
                    this.get('value') || 0, { type : 'float' }
                ));

                // Alternately change the display value for progress bar
                var gain_pct = value + "%";
                this.$(".percentage-bar-success").css("width", gain_pct);
                value
                    ? this.$(".percentage-text-success").text(gain_pct)
                    : this.$(".percentage-text-success").text("");

                // get the remaining from current percentage
                var remaining = _.isNumber(value) ? 100 - value : 0;
                var remaining_pct = remaining.toFixed(2).toString() + "%";
                this.$(".percentage-bar-danger").css("width", remaining_pct);

                remaining
                    ? this.$(".percentage-text-danger").text(remaining_pct)
                    : this.$(".percentage-text-danger").text("");
            }
        });

        // add custom progress bar to registry system
        instance.web.form.widgets.add(
            "audit_progress_bar", "instance.tms_audit.audit_progress_bar"
        )
    }
);