/**
 * Created by chanhle on 11/7/13.
 */

openerp.unleashed.module('web_field_extra').ready(function (instance) {
//    REMEMBER: extends object web.DateWidget first
    var DateUSWidget = instance.web.DateWidget.extend({
        start: function () {
            $.datepicker.setDefaults({
                showOtherMonths: true,
                selectOtherMonths: true,
                calculateWeek: this.weekNumberUS
            })
            this._super();
        },

        weekNumberUS: function (date) {
            var checkDate = new Date(date.getTime());
            var one_jan = new Date(checkDate.getFullYear(), 0, 1);
            var date_number = Math.ceil((checkDate - one_jan) / 86400000);
            var week_number = Math.floor((date_number - checkDate.getDay() + 10 ) / 7)
            return week_number > 52 ? 1 : week_number
        }

    })

    var FieldDate = instance.web.form.FieldDate.extend({
        build_widget: function () {
            return new DateUSWidget(this);
        }
    });
    instance.web_field_extra.FieldDate = FieldDate;
    instance.web.form.widgets.add('date_us', 'openerp.web_field_extra.FieldDate');
})

