openerp.unleashed.module('web_attachment').ready(function(instance){

    var ColumnAttachments = instance.web.list.Column.extend({
        _format: function(row_data, options) {
            var self = this;
            if (!_.isEmpty(row_data[this.id].value))
            {
                var list_attachment_ids = row_data[this.id].value
                var display_names = row_data[this.id + "__display"].value.split(",");
                var links = "";
                for (index in list_attachment_ids)
                {
                    var download_url = instance.session.url('/web/binary/saveas', {model: "ir.attachment",
                                                                        field: "datas",
                                                                        id: list_attachment_ids[index],
                                                                        filename_field: "name"});
                    links += _.template('<a title="<%-title%>" href="<%-href%>"><%-text%></a>', {
                        text: display_names[index],
                        href: download_url,
                        title: _t("Download") + " " + display_names[index]
                    }) + ', ';
                }
                return links.substring(0, links.length - 2);
            }
            return this._super(row_data, options);
        }
    });
    
    instance.web_attachment.ColumnAttachments = ColumnAttachments;
    instance.web.list.columns.add("field.attachments", "instance.web_attachment.ColumnAttachments");

});