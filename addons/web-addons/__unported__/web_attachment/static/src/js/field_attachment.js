openerp.unleashed.module('web_attachment').ready(function (instance) {
   
    var SimpleAttachment = instance.web.form.FieldBinaryFile.extend({

        init: function (field_manager, node) {
            var self = this;
            this._super(field_manager, node);
//           initial value
            this.filename_field = 'name'
            this.data_field = 'datas'
            this.id = ''
            this.size = 0
            this.dataset = new instance.web.DataSetStatic(this, this.field.relation, this.build_context());
        },

        render_value: function () {
            var self = this
            if (!this.get("effective_readonly")) {
                var show_value = '';
                if (this.get('value')) {
                    show_value = this.get('value')[1] || '';
                    this.id = this.get('value')[0] || '';
                }
                this.$el.find('input').eq(0).val(show_value);
            } else {
                this.$el.find('a').toggle(!!this.get('value'));
                if (this.get('value')) {
                    var show_value = _t("Download")
                    this.id = this.get('value')[0] || '';
                    if (this.view) {
                        this.dataset.name_get(this.id).done(function (result) {
                            this.size = result
                            show_value += " " + result[0][1]
                            self.$el.find('a').text(show_value);
                        })
                    }
                }
            }
        },

        on_file_uploaded_and_valid: function (size, name, content_type, file_base64) {
            var self = this
            // initial data for attachment
            var attachment_data = {}
            attachment_data['name'] = name
            attachment_data['type'] = 'binary'
            attachment_data['datas'] = file_base64
            attachment_data['datas_fname'] = name
            this.dataset.create(attachment_data).done(function (id) {
                self.set({'value': id});
                this.id = null // this moment can't get datas then we set to null
                self.$el.find('input').eq(0).val(name);
            })
        },

        on_clear: function () {
            this._super.apply(this, arguments);
            var self = this
            this.dataset.unlink([this.id]).done(function () {
                self.$el.find('input').eq(0).val('');
                self.set({'value': null});
            })
        },

        on_save_as: function (ev) {
            if (!this.id) {
                this.do_warn(_t("Save As..."), _t("The field is empty, there's nothing to save !"));
                ev.stopPropagation();
            } else {
                instance.web.blockUI();
                var c = instance.webclient.crashmanager;

                this.session.get_file({
                    url: '/web/binary/saveas_ajax',
                    data: {data: JSON.stringify({
                        model: this.field.relation,
                        id: (this.id || ''),
                        field: this.data_field,
                        filename_field: ( this.filename_field || ''),
                        data: null,
                        context: this.view.dataset.get_context()
                    })},
                    complete: instance.web.unblockUI,
                    error: c.rpc_error.bind(c)
                });
                ev.stopPropagation();
                return false;
            }
        }

    })
    instance.web_attachment.SimpleAttachment = SimpleAttachment;
    instance.web.form.widgets.add('simple_attachment', 'openerp.web_attachment.SimpleAttachment');

})


