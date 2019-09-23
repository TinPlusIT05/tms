openerp.unleashed.module('tms_modules').ready(

    function(instance, tms_module, _, Backbone, base){

        // jquery selector support matching element using regular expression
        jQuery.expr[':'].regex = function(elem, index, match) {
            var matchParams = match[3].split(','),
                validLabels = /^(data|css):/,
            attr = {
                method: matchParams[0].match(validLabels) ?
                        matchParams[0].split(':')[0] : 'attr',
                property: matchParams.shift().replace(validLabels,'')
            },
            regexFlags = 'ig',
            regex = new RegExp(matchParams.join('').replace(/^s+|s+$/g,''), regexFlags);
            return regex.test(jQuery(elem)[attr.method](attr.property));
        };

        instance.web.form.One2ManyList.include({

            pad_table_to: function(count){

                this._super.apply(this, arguments);

                // check if we have the context to put button on top
                var context_obj = this.dataset.context;

                if(context_obj.eval) {

                    // eval the context from current dataset
                    var context = context_obj.eval();

                    // check if we have the context specified for the customization
                    if ("add_item_on_top" in context){

                        var $padding = this.$current.find('tr:not([data-id]):first');

                            if ($padding.length) {

                            // detach button cell row from DOM $current dom
                            var $add_button = $(
                                ".oe_form_field_one2many_list_row_add",
                                this.$current
                            ).detach();

                            // then insert it at the top
                            this.$current.prepend($add_button);
                        }

                        // also move new added item to top using
                        var $new_rows = this.$current.find("tr:regex(data-id,one2many_v_id_\d*)");

                        if ($new_rows.length) {
                            $new_rows.insertAfter($add_button);
                        }
                    }
                }
            }
        });

        instance.web.FormView.include({
            /**
             * Ask the view to switch to a precise mode if possible. The view is free to
             * not respect this command if the state of the dataset is not compatible with
             * the new mode. For example, it is not possible to switch to edit mode if
             * the current record is not yet saved in database.
             *
             * @param {string} [new_mode] Can be "edit", "view", "create" or undefined. If
             * undefined the view will test the actual mode to check if it is still consistent
             * with the dataset state.
             */
            init: function(parent, dataset, view_id, options) {
                this.is_rm = true;
                return this._super(parent, dataset, view_id, options);
            },
            load_record: function(record){
                var self = this;
                // when form is_initialized, highlight button
                this.is_initialized.then(function(){
                    self.$el.find('.empty_button').removeClass('button_highlight');
                    self.$el.find('.empty_button.hide_record').addClass('button_highlight');
                });
                // Hide Std Development Time except TPM profile or higher
                this.is_rm = true;
                forge_id = self.get_fields_values()['id'];
                var forge = new openerp.Model("tms.forge.ticket");
                if (self.model == 'tms.forge.ticket') {
                    var def = $.Deferred();
                    forge.call("is_remove_std_dev_estimation", [[forge_id]]).done(function(result){
                        is_rm = result['is_remove']
                        this.is_rm = is_rm;

                        lbs = document.getElementsByTagName('label');
                        var lb_std_est = 'Std Dev Estimate (h)'.trim();
                        for (i = 0; i < lbs.length; i++) {
                            if (lbs[i].textContent.trim() == lb_std_est) {
                                std_element = lbs[i].parentElement.parentElement
                                std_element.setAttribute("class", "oe_form_group_row")
                                if (is_rm === true) {
                                    std_element.setAttribute("class", "oe_form_invisible")
                                }
                            }
                        }
                        def.resolve();
                    });
                    forge.call("is_remove_qc_estimation", [[forge_id]]).done(function(result){
                        is_rm = result
                        this.is_rm = is_rm;

                        lbs = document.getElementsByTagName('label');
                        var lb_std_est = 'QC Estimate (h)'.trim();
                        for (i = 0; i < lbs.length; i++) {
                            if (lbs[i].textContent.trim() == lb_std_est) {
                                qc_element = lbs[i].parentElement.parentElement
                                qc_element.setAttribute("class", "oe_form_group_row")
                                if (is_rm === true) {
                                    qc_element.setAttribute("class", "oe_form_invisible")
                                }
                            }
                        }
                        def.resolve();
                    });
                }
                return this._super(record);
            },
        });

        instance.web.form.WidgetButton.include({
            init: function(field_manager, node) {
                this._super(field_manager, node);
                this.is_empty_button = /\bempty_button\b/.test(node.attrs['class']);
            },

            on_click: function() {
                var self = this;
                if (this.is_empty_button) {
                    $('.empty_button').removeClass('button_highlight');
                    this.$el.addClass('button_highlight');
                    if (this.$el.hasClass('hide_record')) {
                        $('.empty_button.hide_record').trigger('hideRecord');
                  }else if (this.$el.hasClass('show_all')) {
                      $('.empty_button.show_all').trigger('showAll');
                  }
                } else {
                    this._super();
                }
            },
        });

        /*
        * For model tms.forge.ticket, field `name` of the model is used to store
        * ID of an ticket, there for in case of quick create forge ticket from
        * many2one field (in working hour list view) user will get an error when
        * trying to perform quick create on the drop-down list or in a dialog
        *
        * the purpose of the script below is to allow user to quick create
        * tms.forge.ticket without the use of `name` field.
        **/
        _.extend(instance.web.form.CompletionFieldMixin, {

            // this method is used to quickly create a record of an object
            // without the default name field used of the model
            _quick_create_no_name: function(default_field, name) {

                var context = this._create_context();

                context["default_" + default_field] = name

                this._search_create_popup("form", undefined, context);
            }
        });

        instance.web.form.FieldMany2One.include({

            _quick_create: function(name) {

                this.no_ed = true; this.ed_def.reject();

                var _super = instance.web.form.CompletionFieldMixin,
                    context = this.build_context().eval();

                var quick_create_field = _.result(
                    context, "quick_create_no_name"
                )

                if (quick_create_field) {
                    return _super._quick_create_no_name.apply(
                        this, [context["quick_create_no_name"], name]
                    );
                }

                return _super._quick_create.apply(this, arguments);
            },

            _search_create_popup: function(view, ids, context) {

                var field_context = this.build_context().eval();

                var quick_create_field = _.result(
                    field_context, "quick_create_no_name"
                );

                // only when we have a context
                if (quick_create_field && view === 'form') {
                	var new_context = this._create_context();
                	new_context["default_" + quick_create_field]
                        = new_context["default_" + quick_create_field]
                            || this.$("input").val() || "";

                    this._super.apply(
                        this, ["form", undefined, new_context]
                    );

                    return
                }

                this._super.apply(this, arguments);
            }
        });

        instance.web.form.FieldDatetime.include({
            initialize_content: function() {
                this._super.apply(this, arguments);
                var self = this;
                if (this.datewidget) {
                    if (typeof this.options.datepicker === 'object') {
                        $.map(this.options.datepicker, function(value, key) {
                            if(key == 'beforeShowDay'){
                                self.datewidget.picker(
                                    'option',
                                    key,
                                    function(date){ 
                                        var day = date.getDay();
                                        return [value.indexOf(day) == -1];
                                    });
                            }
                        });
                    }
                }
            },
        })
    }
);
