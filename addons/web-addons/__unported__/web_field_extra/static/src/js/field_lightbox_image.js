openerp.unleashed.module('web_field_extra').ready(function(instance){

    var QWeb = instance.web.qweb;

    var FieldLightboxImage = instance.web.form.FieldBinaryImage.extend({
        placeholder : "/web/static/src/img/placeholder.png",
        template: 'FieldBinaryImage',
        render_value : function() {
            var self = this;
            var url;
            if (this.get('value') && !instance.web.form.is_bin_size(this.get('value'))) {
                url = 'data:image/png;base64,' + this.get('value');
            } else if (this.get('value')) {
                var id = JSON.stringify(this.view.datarecord.id || null);
                var field = this.name;
                if (this.options.preview_image)
                    field = this.options.preview_image;
                url = this.session.url('/web/binary/image', {
                    model : this.view.dataset.model,
                    id : id,
                    field : field,
                    t : (new Date().getTime()),
                });
            } else {
                url = this.placeholder;
            }
            var $img = $(QWeb.render("FieldBinaryImage-img", {
                widget : this,
                url : url
            }));
            this.$el.find('>a img').remove();
            this.$el.prepend($img);
            $img.load(function() {
                if (!self.options.size)
                    return;
                $img.css("max-width", "" + self.options.size[0] + "px");
                $img.css("max-height", "" + self.options.size[1] + "px");
                $img.css("margin-left", "" + (self.options.size[0] - $img.width()) / 2 + "px");
                $img.css("margin-top", "" + (self.options.size[1] - $img.height()) / 2 + "px");
            });
            $img.wrap($('<a rel=\"lightbox\"></a>').attr('href', $img.attr('src')));
        }
    });

    instance.web_field_extra.FieldLightboxImage = FieldLightboxImage;
    instance.web.form.widgets.add('image_viewer', 'openerp.web_field_extra.FieldLightboxImage');
});

