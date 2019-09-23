openerp.web_widget_text_markdown = function (oe) {

    var _lt = oe.web._lt,
        QWeb = oe.web.qweb;

    oe.web.form.widgets.add('bootstrap_markdown', 'openerp.web_widget_text_markdown.FieldTextMarkDown');

    oe.web_widget_text_markdown.FieldTextMarkDown = oe.web.form.AbstractField.extend(
        oe.web.form.ReinitializeFieldMixin,
        {

            template: 'FieldMarkDown',
            display_name: _lt('MarkDown'),
            widget_class: 'oe_form_field_bootstrap_markdown',
            events: {
                'change input': 'store_dom_value',
                'drop textarea': 'drop_image',
                'paste textarea': 'copy_paste'
            },

            init: function (field_manager, node) {
                this._super(field_manager, node);
                this.$txt = false;

                this.old_value = null;
            },

            parse_value: function(val, def) {
                return oe.web.parse_value(val, this, def);
            },

            drop_image: function(event) {
                event.stopPropagation();
                event.preventDefault();
                var files = event.originalEvent.dataTransfer.files;
                if (files.length <= 0) return;
                if (!['image/png', 'image/jpeg', 'image/jpg',].includes(files[0].type)) return;
                if (this.get('value')){
                    var index_cursor = this.get('value').slice(0, event.currentTarget.selectionStart).length;
                }
                else{
                    var index_cursor = 0;
                }
                this.upload(files[0], index_cursor);
            },

            upload: function (files, index_cursor) {
                var content = this.$txt.val();
                var self = this;
                var reader = new FileReader();
                reader.onload = function (e) {
                    var unique_name_from_date = new Date().getTime();
                    var fname = _.uniqueId('image_') + '-' + unique_name_from_date + '_' + files.name;
                    var model = self.view.dataset.model;
                    var res_id = self.view.datarecord.id;
                    var mimetype = reader.result.substring(5, reader.result.indexOf(';'));
                    var base64_data = reader.result.substr(reader.result.indexOf(',') + 1, reader.result.length);
                    if(model){
                        if(res_id)
                            var vals = {
                                'name': fname,
                                'datas':base64_data,
                                'datas_fname': fname,
                                'description': '',
                                'res_model': model,
                                'res_id': res_id,
                            };
                        else{
                            var vals = {
                                'name': fname,
                                'datas':base64_data,
                                'datas_fname': fname,
                                'description': '',
                                'res_model': model,
                            };
                        }
                        new oe.web.Model("ir.attachment").call("create", [vals]).then(function(result) {
                            if (result) {
                                var start_str = content.substring(0, index_cursor);
                                var extend_str = _.str.sprintf('\n\!\[enter image description here\]\(\%s/web/binary/saveas?model=ir.attachment&field=datas&filename_field=name&id=%s "enter image title here")\n',self.session.origin, result);
                                var end_str = content.substring(index_cursor);
                                var res_text = [start_str, extend_str, end_str].join('');
                                self.set({'value': res_text});
                            }
                        });
                    }
                };
                reader.readAsDataURL(files);
            },

            copy_paste: function(event){
                // event.preventDefault();
                var items = event.originalEvent.clipboardData.items;
                for(var i = 0 ; i < items.length; i++){
                    if(items[i].kind == "file" && ['image/png', 'image/jpeg', 'image/jpg',].includes(items[i].type)){
                        if (this.get('value')){
                            var index_cursor = this.get('value').slice(0, event.currentTarget.selectionStart).length;
                        }
                        else{
                            var index_cursor = 0;
                        }
                        
                        this.upload(items[i].getAsFile(), index_cursor);
                    }
                }
                // Return true to run as native function copy paste
                return true
            },

            initialize_content: function () {
                // Gets called at each redraw of widget
                //  - switching between read-only mode and edit mode
                //  - BUT NOT when switching to next object.
                this.$txt = this.$el.find('textarea[name="' + this.name + '"]');
                if (!this.get('effective_readonly')) {
                    this.$txt.markdown({autofocus: false, savable: false});
                }
                this.old_value = null; // will trigger a redraw
            },

            store_dom_value: function () {
                if (!this.get('effective_readonly') &&
                    this.is_syntax_valid()) {
                    // We use internal_set_value because we were called by
                    // ``.commit_value()`` which is called by a ``.set_value()``
                    // itself called because of a ``onchange`` event
                    this.internal_set_value(
                        this.parse_value(
                            this._get_raw_value()
                        )
                    );
                }
            },

            commit_value: function () {
                this.store_dom_value();
                return this._super();
            },

            _get_raw_value: function() {
                if (this.$txt === false)
                    return '';
                return this.$txt.val();
            },

            render_value: function () {
                // Gets called at each redraw/save of widget
                //  - switching between read-only mode and edit mode
                //  - when switching to next object.

                var show_value = this.format_value(this.get('value'), '');
                if (!this.get("effective_readonly")) {
                    this.$txt.val(show_value);
                    this.$el.trigger('resize');
                } else {
                    // avoids loading markitup...
                    marked.setOptions({
                        sanitize: true,
                        highlight: function (code) {
                            return hljs.highlightAuto(code).value;
                        }
                    });
                    this.$el.find('span[class="oe_form_text_content"]').html(marked(show_value));
                }
            },

            format_value: function (val, def) {
                return oe.web.format_value(val, this, def);
            }
        }
    );

    /**
     * bootstrap_markdown support on list view
     **/
    oe.web_widget_text_markdown.FieldTextMarkDownList = oe.web.list.Char.extend({

        init: function(){
            this._super.apply(this, arguments);
            hljs.initHighlightingOnLoad();
            marked.setOptions({
                sanitize: true,
                highlight: function (code) {
                    return hljs.highlightAuto(code).value;
                }
            });
        },

        _format: function(row_data, options){
            options = options || {};
            var markdown_text = marked(
                oe.web.format_value(
                    row_data[this.id].value, this, options.value_if_empty
                )
            );
            return markdown_text;
        }
    });

    oe.web.list.columns.add(
        "field.bootstrap_markdown", "oe.web_widget_text_markdown.FieldTextMarkDownList"
    );
};
