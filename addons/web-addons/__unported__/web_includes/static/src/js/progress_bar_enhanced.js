openerp.unleashed.module('web_includes').ready(function (instance) {

    instance.web.list.ProgressBar.include({
        _format: function (row_data, options) {
            var template = ['<div class="progress_bar_enhanced_container">',
                '<div class="progress_bar_enhanced_bar" style="width: <%-value%>%;"></div>',
                '<div class="progress_bar_enhanced_value" style="width: 100%;"><%-value%>%</div>',
                '</div>']
                .join('\n');
            return _.template(
                template, {
                    value: _.str.sprintf("%.0f", row_data[this.id].value > 100 ? 100 : row_data[this.id].value || 0)
                });
        }
    });

});