openerp.web_m2o_enhanced = function (instance) {

    "use strict";

    var QWeb = instance.web.qweb,
        _t  = instance.web._t,
        _lt = instance.web._lt;

    instance.web.form.FieldMany2One.include({

        show_error_displayer: function () {
            if ((typeof this.options.m2o_dialog === 'undefined' && this.can_create) ||
                this.options.m2o_dialog) {
                new instance.web.form.M2ODialog(this).open();
            }
        },

        get_search_result: function (search_val) {
            var def = $.Deferred();
            var self = this;
            // add options limit used to change number of selections record
            // returned.

            if (typeof this.options.limit === 'number') {
                this.limit = this.options.limit;
            }

            var dataset = new instance.web.DataSet(this, this.field.relation,
                                                   self.build_context());
            var blacklist = this.get_search_blacklist();
            this.last_query = search_val;

            var search_result = this.orderer.add(dataset.name_search(
                search_val,
                new instance.web.CompoundDomain(
                    self.build_domain(), [["id", "not in", blacklist]]),
                'ilike', this.limit + 1,
                self.build_context()));

            var create_rights;
            if (typeof this.options.create === "undefined" ||
                typeof this.options.create_edit === "undefined") {
                create_rights = new instance.web.Model(this.field.relation).call(
                    "check_access_rights", ["create", false]);
            }

            $.when(search_result, create_rights).then(function (_data, _can_create) {
            	
            	// FIXME:: var data = _data[0]; => should be var data = _data;
                var data = _data;

                // FIXME:: var can_create = _can_create ? _can_create[0] : null;
                // if user has no right -> disable it
                // if user has right -> disable on options flag
                var can_create = _can_create ? _can_create : self.can_create;

                self.can_create = can_create;  // for ``.show_error_displayer()``
                self.last_search = data;

                // possible selections for the m2o
                var values = _.map(data, function (x) {
                	if (x && x[1]) {
	                    x[1] = x[1].split("\n")[0];
	                    return {
	                        label: _.str.escapeHTML(x[1]),
	                        value: x[1],
	                        name: x[1],
	                        id: x[0]
	                    };
	                }
	                return {
	                	label: '',
                        value: '',
                        name: '',
                        id: x[0]
	                }
                });

                // search more... if more results that max
                if (values.length > self.limit) {
                    values = values.slice(0, self.limit);
                    values.push({
                        label: _t("Search More..."),
                        action: function () {
                            dataset.name_search(
                                search_val, self.build_domain(),
                                'ilike', false).done(function (data) {
                                    self._search_create_popup("search", data);
                                });
                        },
                        classname: 'oe_m2o_dropdown_option'
                    });
                }

                // quick create
                var raw_result = _(data.result).map(function (x) {
                    return x[1];
                });

                if ((typeof self.options.create === 'undefined' && can_create) ||
                    self.options.create) {

                    if (search_val.length > 0 &&
                        !_.include(raw_result, search_val)) {

                        values.push({
                            label: _.str.sprintf(
                                _t('Create "<strong>%s</strong>"'),
                                $('<span />').text(search_val).html()),
                            action: function () {
                                self._quick_create(search_val);
                            },
                            classname: 'oe_m2o_dropdown_option'
                        });
                    }
                }

                // Create and Edit...
                if ((typeof self.options.create_edit === 'undefined' && can_create) ||
                    self.options.create_edit) {

                    values.push({
                        label: _t("Create and Edit..."),
                        action: function () {
                            self._search_create_popup(
                                "form", undefined,
                                self._create_context(search_val));
                        },
                        classname: 'oe_m2o_dropdown_option'
                    });
                }

                def.resolve(values);
            });

            return def;
        }
    });

    // Override to add option disable create in Search More form
    instance.web.form.CompletionFieldMixin =  _.extend({}, instance.web.form.CompletionFieldMixin, {

	    _search_create_popup: function(view, ids, context) {
	        var self = this;
	        var pop = new instance.web.form.SelectCreatePopup(this);

	        //Check if exists "create" in options
	        var disable_create = false
	        if ('create' in self.options){
	        	disable_create = !this.options.create
            }

	        pop.select_element(
	            self.field.relation,
	            {
	                title: (view === 'search' ? _t("Search: ") : _t("Create: ")) + this.string,
	                initial_ids: ids ? _.map(ids, function(x) {return x[0]}) : undefined,
	                initial_view: view,
	                disable_multiple_selection: true,
	                disable_create: disable_create //Disable create
	            },
	            self.build_domain(),
	            new instance.web.CompoundContext(self.build_context(), context || {})
	        );

	        pop.on("elements_selected", self, function(element_ids) {
	            self.add_id(element_ids[0]);
	            self.focus();
	        });
	    }
	});
};

