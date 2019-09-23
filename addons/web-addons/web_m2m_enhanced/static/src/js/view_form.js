openerp.unleashed.module('web_m2m_enhanced').ready(function(instance){

    var _t = instance.web._t,
		QWeb = instance.web.qweb;
	
	//Override to add option disable create in Add form of many2many fields
	//Add data disable_create when create new instance.web.form.Many2ManyListView
	instance.web.form.FieldMany2Many.include({

		multi_selection: false,

    	disable_utility_classes: true,

    	initialize_content: function() {

	        var self = this;

	        //Check if exists "create" in options
	        var disable_create = false;

	        if ('create' in this.options) {
				disable_create = !this.options.create;
	        }

	        this.$el.addClass('oe_form_field oe_form_field_many2many');
	
	        this.list_view = new instance.web.form.Many2ManyListView(this, this.dataset, false, {
                'addable': this.get("effective_readonly") ? null : _t("Add"),
                'deletable': this.get("effective_readonly") ? false : true,
                'selectable': this.multi_selection,
		        /*
		            re-enable sorting feature on many2many list view
					check 'sort_by_column' function from instance.web.ListView
					to enable sort for numberic field....
		        */
                'sortable': true,
                'reorderable': false,
                'import_enabled': false,
                'disable_create': disable_create
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
	
    instance.web.form.Many2ManyListView.include({
   	
	   	do_add_record: function () {
	        var pop = new instance.web.form.SelectCreatePopup(this);
	        var self = this;
	        pop.select_element(
	            this.model,
	            {
	                title: _t("Add: ") + this.m2m_field.string,
	                disable_create: this.options.disable_create //Disable create
	            },
	            new instance.web.CompoundDomain(this.m2m_field.build_domain(), ["!", ["id", "in", this.m2m_field.dataset.ids]]),
	            this.m2m_field.build_context()
	        );
	        pop.on("elements_selected", self, function(element_ids) {
	            var reload = false;
	            _(element_ids).each(function (id) {
	                if(! _.detect(self.dataset.ids, function(x) {return x == id;})) {
	                    self.dataset.set_ids(self.dataset.ids.concat([id]));
	                    self.m2m_field.dataset_changed();
	                    reload = true;
	                }
	            });
	            if (reload) {
	                self.reload_content();
	            }
	        });
    	}
   });
   
   instance.web.form.FieldMany2ManyTags = instance.web.form.FieldMany2ManyTags.extend({

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

                var data = _data;

                var can_create = _can_create ? _can_create[0] : null;

                self.can_create = can_create;  // for ``.show_error_displayer()``
                self.last_search = data;
                // possible selections for the m2m
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
                        classname: 'oe_m2m_dropdown_option'
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
                            classname: 'oe_m2m_dropdown_option'
                        });
                    }
                }

                // create...

                if ((typeof self.options.create_edit === 'undefined' && can_create) ||
                    self.options.create_edit) {

                    values.push({
                        label: _t("Create and Edit..."),
                        action: function () {
                            self._search_create_popup(
                                "form", undefined,
                                self._create_context(search_val));
                        },
                        classname: 'oe_m2m_dropdown_option'
                    });
                }

                def.resolve(values);
            });

            return def;
        }
	});

	/*
	 * ============================================================
	 * Override instance.web.form.Many2ManyDataSet to allow sorting
	 * on many2many List View placed on form view
	 * ============================================================
	 */
	instance.web.form.Many2ManyDataSet.include({

		compare_ids: function(a, b) {

			a = a && a.toString() || "";
			b = b && b.toString() || "";

			function chunkify(t) {

				var tz = [], x = 0, y = -1, n = 0, i, j;

				while (i = (j = t.charAt(x++)).charCodeAt(0)) {

					var m = (i == 46 || (i >=48 && i <= 57));

					if (m !== n) {
						tz[++y] = "";
						n = m;
					}

					tz[y] += j;
				}
				return tz;
			}

			var aa = chunkify(a);
			var bb = chunkify(b);

			for (x = 0; aa[x] && bb[x]; x++) {

				if (aa[x] !== bb[x]) {

					var c = Number(aa[x]), d = Number(bb[x]);

					if (c == aa[x] && d == bb[x]) {
						return c - d;
					}

					else return (aa[x] > bb[x]) ? 1 : -1;
				}
			}

			return aa.length - bb.length;
		},

		read_ids: function (ids, fields, options) {
			var self = this;
			var task = $.Deferred();

			this._super(ids, fields, options).then(function(records){
				/*
				 * this part is taken from instance.web.BufferedDataSet, 
				 * originally used by instance.web.form.One2ManyDataSet.
				 * --------------------------------------------------------
				 * Modified for use of instance.web.form.Many2ManyDataSet
				 */

				// check if record is loaded correctly in debug mode
				if (self.debug_mode) {
				    if (_.include(records, undefined)) {
				        throw "Record not correctly loaded";
				    }
				}

				// get field name criteria need to be used to sort the many2many list view
				var sort_fields = self._sort;

				if (sort_fields.length) {
					records.sort(function (a, b) {
						return _.reduce(sort_fields, function (acc, field) {
							if (acc) { return acc; }
							var sign = 1;
							if (field[0] === '-') {
							    sign = -1;
							    field = field.slice(1);
							}
							//m2o should be searched based on value[1] not based whole value(i.e. [id, value])
							if(_.isArray(a[field]) && a[field].length == 2 && _.isString(a[field][1])){
							    return sign * self.compare_ids(a[field][1], b[field][1]);
							}
							return sign * self.compare_ids(a[field], b[field]);
						}, 0);
					});
					task.resolve(records);
				}
				task.resolve(records);
			});
			return task.promise();
		}
	});
});