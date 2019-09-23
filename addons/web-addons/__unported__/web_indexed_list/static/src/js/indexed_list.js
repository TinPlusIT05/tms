openerp.unleashed.module('web_indexed_list').ready(function(instance, web_indexed, _, Backbone, base){



    var IndexedColumn = instance.web.list.MetaColumn.extend({
        meta: false
    });

    var IndexedListView = {
        init: function() {
            this._super.apply(this, arguments);

            // monkey patch, because add/remove may be called in silent mode at init...
            var add_record = this.records.add;
            var remove_record = this.records.remove;

            this.records.calculateIndex = function(models, options){
                _(this.records).each(function(model, index){
                    model.set('index', index + 1);
                });
                return this;
            };

            this.records.add = function(models, options){
                add_record.apply(this, [models, options]);
                return this.calculateIndex();
            };

            this.records.remove = function(){
                remove_record.apply(this, arguments);
                return this.calculateIndex();
            };

            return this;
        },

        setup_columns: function(){
            this._super.apply(this, arguments);

            var index_column = new IndexedColumn('index', base._t('No'));

            this.columns.unshift(index_column);
            this.visible_columns.unshift(index_column);
            this.aggregate_columns.unshift({});
        },



    };

    instance.web.form.IndexedOne2ManyListView = instance.web.form.One2ManyListView.extend(IndexedListView);
    instance.web.form.IndexedMany2ManyListView = instance.web.form.Many2ManyListView.extend(IndexedListView);




    var check_indexes_value = function(obj){
        return 'indexes' in obj.attrs && /^true|on|yes$/i.test(obj.attrs['indexes']) ? true : false;
    };


    instance.web.form.One2ManyViewManager = instance.web.form.One2ManyViewManager.extend({
        init: function(parent, dataset, views, flags) {
            this._super.apply(this, arguments);

            if(parent.node && check_indexes_value(parent.node)){
                this.registry.add('list', 'instance.web.form.IndexedOne2ManyListView');
            }
        }
    });

    instance.web.form.FieldMany2Many = instance.web.form.FieldMany2Many.extend({
        init: function(field_manager, node) {
            this.indexes = check_indexes_value(node);
            return this._super(field_manager, node);
        },


        initialize_content: function() {
            var self = this;

            var M2MList = this.indexes ?
                          instance.web.form.IndexedMany2ManyListView :
                          instance.web.form.Many2ManyListView;

            this.$el.addClass('oe_form_field oe_form_field_many2many');

            this.list_view = new M2MList(this, this.dataset, false, {
                        'addable': this.get("effective_readonly") ? null : base._t("Add"),
                        'deletable': this.get("effective_readonly") ? false : true,
                        'selectable': this.multi_selection,
                        'sortable': false,
                        'reorderable': false,
                        'import_enabled': false,
                        'indexes': this.indexes
                });
            var embedded = (this.field.views || {}).tree;
            if (embedded) {
                this.list_view.set_embedded_view(embedded);
            }
            this.list_view.m2m_field = this;
            var loaded = $.Deferred();
            this.list_view.on("list_view_loaded", this, function() {
                loaded.resolve();
            });
            this.list_view.appendTo(this.$el);

            var old_def = self.is_loaded;
            self.is_loaded = $.Deferred().done(function() {
                old_def.resolve();
            });
            this.list_dm.add(loaded).then(function() {
                self.is_loaded.resolve();
            });
        }
    });



});