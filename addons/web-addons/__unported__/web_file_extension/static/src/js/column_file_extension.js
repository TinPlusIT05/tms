openerp.unleashed.module('web_file_extension').ready(function(instance){

    //FIXME: async request is not good in general... there's always a way to do it async (look at jQuery.Deferred...)
    var urlExists = function(url){
        var http = new XMLHttpRequest();
        http.open('HEAD', url, false);
        http.send();
        return http.status != 404;
    };
    
    
    var ColumnExtensionAndDownload = instance.web.list.Column.extend({
        
        _format: function(row_data, options) {
        
            // Get extension icon
            var extension = row_data['file_extension'].value;
            var src_image = '/web_file_extension/static/src/img/icons/' + extension + '_icon.png';
            
            if (!urlExists(src_image))
            {
                src_image = '/web/static/src/img/placeholder.png';
            }
            
            var width = 16;
            var height = 16;
            
            // Get download link
            var download_url = instance.session.url('/web/binary/saveas', {
                model: options.model,
                field: "datas",
                id: options.id,
                filename_field: "name"
            });

            return _.template('<a title="<%-title%>" href="<%-href%>"><img src="<%-image%>" width="<%-width%>" height="<%-height%>" /></a>', {
                image: src_image,
                href: download_url,
                title: _t("Download") + " " + row_data[this.id].value,
                width: width,
                height: height
            });
        }
    });

    instance.web_file_extension.ColumnExtensionAndDownload = ColumnExtensionAndDownload;
    instance.web.list.columns.add("field.extension_and_download", "instance.web_file_extension.ColumnExtensionAndDownload");
});