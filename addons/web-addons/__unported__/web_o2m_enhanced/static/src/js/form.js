/**
 * Created by: Trobz - www.trobz.com
 * Date: 9/6/13
 * Time: 5:51 PM
 */


openerp.web_o2m_enhanced = function (instance) {

    instance.web.form.FieldOne2Many.include({
        load_views: function () {
            var self = this;
            var modes = this.node.attrs.mode;
            modes = !!modes ? modes.split(",") : ["tree"];
            var views = [];
            _.each(modes, function (mode) {
                if (!_.include(["list", "tree", "graph", "kanban"], mode)) {
                    throw new Error(_.str.sprintf(_t("View type '%s' is not supported in One2Many."), mode));
                }
                var view = {
                    view_id: false,
                    view_type: mode == "tree" ? "list" : mode,
                    options: {'option_view': self.options}
                };
                if (self.field.views && self.field.views[mode]) {
                    view.embedded_view = self.field.views[mode];
                }
                if (view.view_type === "list") {
                    _.extend(view.options, {
                        addable: null,
                        selectable: self.multi_selection,
                        sortable: true,
                        import_enabled: false,
                        deletable: true,
//                        set option limit
                        limit: self.options.limit || 80
                    });
                    if (self.get("effective_readonly")) {
                        _.extend(view.options, {
                            deletable: null,
                            reorderable: false,
                        });
                    }
                } else if (view.view_type === "form") {
                    if (self.get("effective_readonly")) {
                        view.view_type = 'form';
                    }
                    _.extend(view.options, {
                        not_interactible_on_create: true,
                    });
                } else if (view.view_type === "kanban") {
                    _.extend(view.options, {
                        confirm_on_delete: false,
                    });
                    if (self.get("effective_readonly")) {
                        _.extend(view.options, {
                            action_buttons: false,
                            quick_creatable: false,
                            creatable: false,
                            read_only_mode: true,
                        });
                    }
                }
                views.push(view);
            });

            this.viewmanager = new instance.web.form.One2ManyViewManager(this, this.dataset, views, {});
            this.viewmanager.o2m = self;
            var once = $.Deferred().done(function () {
                self.init_form_last_update.resolve();
            });
            var def = $.Deferred().done(function () {
                self.initial_is_loaded.resolve();
            });
            this.viewmanager.on("controller_inited", self, function (view_type, controller) {
                controller.o2m = self;
                if (view_type == "list") {
                    if (self.get("effective_readonly")) {
                        controller.on('edit:before', self, function (e) {
                            e.cancel = true;
                        });
                        _(controller.columns).find(function (column) {
                            if (!(column instanceof instance.web.list.Handle)) {
                                return false;
                            }
                            column.modifiers.invisible = true;
                            return true;
                        });
                    }
                } else if (view_type === "form") {
                    if (self.get("effective_readonly")) {
                        $(".oe_form_buttons", controller.$el).children().remove();
                    }
                    controller.on("load_record", self, function () {
                        once.resolve();
                    });
                    controller.on('pager_action_executed', self, self.save_any_view);
                } else if (view_type == "graph") {
                    self.reload_current_view()
                }
                def.resolve();
            });
            this.viewmanager.on("switch_mode", self, function (n_mode, b, c, d, e) {
                $.when(self.save_any_view()).done(function () {
                    if (n_mode === "list") {
                        $.async_when().done(function () {
                            self.reload_current_view();
                        });
                    }
                });
            });
            $.async_when().done(function () {
                self.viewmanager.appendTo(self.$el);
            });
            return def;
        }
    })
}




