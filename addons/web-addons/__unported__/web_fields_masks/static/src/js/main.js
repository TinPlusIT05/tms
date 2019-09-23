openerp.web_fields_masks = function (instance) {
    instance.web.form.FieldChar.include({
        mask: '',
        init: function(field_manager, node) {
            this._super(field_manager, node);
            if (_.has(this.node.attrs, 'data-inputmask')) {
                this.mask = this.node.attrs['data-inputmask'];
            }
        },

        render_value: function () {
            this._super();
            if (this.mask !== '') {
                attrs_str = "{" + this.mask.replace(/\'/g, '"') + "}";
                attrs_dict = JSON.parse(attrs_str);
                this.$el.find('input').inputmask(attrs_dict);
            }
        },
    });
}
