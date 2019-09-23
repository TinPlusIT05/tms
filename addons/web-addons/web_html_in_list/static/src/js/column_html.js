openerp.unleashed.module('web_html_in_list').ready(function(instance){

    var ColumnHtmlInList = instance.web.list.Column.extend({

        format: function(row_data, options) {
            var id = options.id,
                self = this;

            setTimeout(function(){
                var $el = $('#record_' + id),
                    $content = $el.find('.html_details');
                $content.scrollTo($content[0].scrollHeight);
            }, 1000);

            return _.template(
                '<div id="record_<%=id%>" class="html_in_list">' +
                    '<div state="close" class="html_details"><%=value%></div>' +
                '</div>', {
                    value: row_data.result_detail.value,
                    id: id
                });
        }


    });

    instance.web_html_in_list.ColumnHtmlInList = ColumnHtmlInList;
    instance.web.list.columns.add("field.html_in_list", "instance.web_html_in_list.ColumnHtmlInList");
});