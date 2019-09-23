/**
 * Created by: Trobz - www.trobz.com
 * Date: 11/21/13
 * Time: 10:35 AM
 * Override Grant View Add Paging Feature
 */
openerp.web_grantt_view = function (instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    instance.web.views.add('gantt', 'instance.web_grantt_view.GanttView');
    instance.web_grantt_view.GanttView = instance.web.View.extend({
        display_name: _lt('Gantt'),
        template: "GanttView",
        view_type: "gantt",
        init: function () {
            var self = this;
            this._super.apply(this, arguments);
            this.has_been_loaded = $.Deferred();
            this.chart_id = _.uniqueId();
            //        paging
            this.page = 0
        },
        view_loading: function (r) {
            return this.load_gantt(r);
        },
        do_show: function () {
            if (this.$pager) {
                this.$pager.show();
            }
            this._super();
        },
        do_hide: function () {
            if (this.$pager) {
                this.$pager.hide();
            }
            this._super();
        },
        limit: function () {
            if (this._limit === undefined) {
                if (this.getParent()) {
                    this._limit = (this.options.limit
                        || (this.getParent().action || {}).limit
                        || 80);
                }
                else {
                    this._limit = (this.options.limit
                        || 80);
                }
            }
            return this._limit;
        },
        configure_pager: function (dataset) {
            this.dataset.ids = dataset.ids;
            // Not exactly clean
            if (dataset._length) {
                this.dataset._length = dataset._length;
            }

            var total = dataset.size();
            var limit = this.limit() || total;
            if (total == 0)
                this.$pager.hide();
            else
                this.$pager.css("display", "");
            this.$pager.toggleClass('oe_list_pager_single_page', (total <= limit));
            var spager = '-';
            if (total) {
                var range_start = this.page * limit + 1;
                var range_stop = range_start - 1 + limit;
                if (range_stop > total) {
                    range_stop = total;
                }
                spager = _.str.sprintf(_t("%d-%d of %d"), range_start, range_stop, total);
            }
            //        FIXME: Position of Pager
            this.$pager.css("margin-left", "-80px");

            this.$pager.find('.oe_list_pager_state').text(spager);
        },
        load_gantt: function (fields_view_get, fields_get) {
            var self = this;
            this.fields_view = fields_view_get;
            this.$el.addClass(this.fields_view.arch.attrs['class']);

            // Pager
            if (!this.$pager) {
                this.$pager = $(QWeb.render("ListView.pager", {'widget': self}));
                if (this.options.$buttons) {
                    this.$pager.appendTo(this.options.$pager);
                } else {
                    this.$el.find('.oe_list_pager').replaceWith(this.$pager);
                }
                this.$pager
                    .on('click', 'a[data-pager-action]',function () {
                        var $this = $(this);
                        var max_page = Math.floor(self.dataset.size() / self.limit());
                        switch ($this.data('pager-action')) {
                            case 'first':
                                self.page = 0;
                                break;
                            case 'last':
                                self.page = max_page - 1;
                                break;
                            case 'next':
                                self.page += 1;
                                break;
                            case 'previous':
                                self.page -= 1;
                                break;
                        }
                        if (self.page < 0) {
                            self.page = max_page;
                        } else if (self.page > max_page) {
                            self.page = 0;
                        }
                        self.reload();
                    }).find('.oe_list_pager_state')
                    .click(function (e) {
                        e.stopPropagation();
                        var $this = $(this);

                        var $select = $('<select>')
                            .appendTo($this.empty())
                            .click(function (e) {
                                e.stopPropagation();
                            })
                            .append('<option value="80">80</option>' +
                                '<option value="200">200</option>' +
                                '<option value="500">500</option>' +
                                '<option value="2000">2000</option>' +
                                '<option value="NaN">' + _t("Unlimited") + '</option>')
                            .change(function () {
                                var val = parseInt($select.val(), 10);
                                self._limit = (isNaN(val) ? null : val);
                                self.page = 0;
                                self.reload();
                            }).blur(function () {
                                $(this).trigger('change');
                            })
                            .val(self._limit || 'NaN');
                    });
            }

            return self.alive(new instance.web.Model(this.dataset.model)
                    .call('fields_get')).then(function (fields) {
                    self.fields = fields;
                    self.has_been_loaded.resolve();
                });
        },
        do_search: function (domains, contexts, group_bys) {
            var self = this;
            self.last_domains = domains;
            self.last_contexts = contexts;
            self.last_group_bys = group_bys;
            // select the group by
            var n_group_bys = [];
            if (this.fields_view.arch.attrs.default_group_by) {
                n_group_bys = this.fields_view.arch.attrs.default_group_by.split(',');
            }
            if (group_bys.length) {
                n_group_bys = group_bys;
            }
            // gather the fields to get
            var fields = _.compact(_.map(["date_start", "date_delay", "date_stop"], function (key) {
                return self.fields_view.arch.attrs[key] || '';
            }));
            fields = _.uniq(fields.concat(n_group_bys));
            var options = { 'offset': this.page * this.limit(), 'limit': this.limit() }
            return $.when(this.has_been_loaded).then(function () {
                return self.dataset.read_slice(fields, {
                    domain: domains,
                    limit: options.limit,
                    offset: options.offset,
                    context: contexts
                })
                    .then(function (data) {
                        self.configure_pager(self.dataset)
                        if (self.dataset.size() == data.length) {
                            // only one page
                            self.$pager.find('.oe_pager_group').hide();
                        }
                        else {
                            self.$pager.find('.oe_pager_group').show();
                        }
                        return self.on_data_loaded(data, n_group_bys);
                    })
            });
        },
        reload: function () {
            if (this.last_domains !== undefined)
                return this.do_search(this.last_domains, this.last_contexts, this.last_group_bys);
        },
        on_data_loaded: function (tasks, group_bys) {
            var self = this;
            var ids = _.pluck(tasks, "id");
            return this.dataset.name_get(ids).then(function (names) {
                var ntasks = _.map(tasks, function (task) {
                    return _.extend({__name: _.detect(names, function (name) {
                        return name[0] == task.id;
                    })[1]}, task);
                });
                return self.on_data_loaded_2(ntasks, group_bys);
            });
        },
        on_data_loaded_2: function (tasks, group_bys) {
            var self = this;
            $(".oe_gantt", this.$el).html("");

            //prevent more that 1 group by
            if (group_bys.length > 0) {
                group_bys = [group_bys[0]];
            }
            // if there is no group by, simulate it
            if (group_bys.length == 0) {
                group_bys = ["_pseudo_group_by"];
                _.each(tasks, function (el) {
                    el._pseudo_group_by = "Gantt View";
                });
                this.fields._pseudo_group_by = {type: "string"};
            }

            // get the groups
            var split_groups = function (tasks, group_bys) {
                if (group_bys.length === 0)
                    return tasks;
                var groups = [];
                _.each(tasks, function (task) {
                    var group_name = task[_.first(group_bys)];
                    var group = _.find(groups, function (group) {
                        return _.isEqual(group.name, group_name);
                    });
                    if (group === undefined) {
                        group = {name: group_name, tasks: [], __is_group: true};
                        groups.push(group);
                    }
                    group.tasks.push(task);
                });
                _.each(groups, function (group) {
                    group.tasks = split_groups(group.tasks, _.rest(group_bys));
                });
                return groups;
            }
            var groups = split_groups(tasks, group_bys);

            // track ids of task items for context menu
            var task_ids = {};
            // creation of the chart
            var generate_task_info = function (task, plevel) {
                var level = plevel || 0;
                if (task.__is_group) {
                    var task_infos = _.compact(_.map(task.tasks, function (sub_task) {
                        return generate_task_info(sub_task, level + 1);
                    }));
                    if (task_infos.length == 0)
                        return;
                    var task_start = _.reduce(_.pluck(task_infos, "task_start"), function (date, memo) {
                        return memo === undefined || date < memo ? date : memo;
                    }, undefined);
                    var task_stop = _.reduce(_.pluck(task_infos, "task_stop"), function (date, memo) {
                        return memo === undefined || date > memo ? date : memo;
                    }, undefined);
                    var duration = (task_stop.getTime() - task_start.getTime()) / (1000 * 60 * 60);
                    var group_name = instance.web.format_value(task.name, self.fields[group_bys[level]]);
                    if (level == 0) {
                        var group = new GanttProjectInfo(_.uniqueId("gantt_project_"), group_name, task_start);
                        _.each(task_infos, function (el) {
                            group.addTask(el.task_info);
                        });
                        return group;
                    } else {
                        var group = new GanttTaskInfo(_.uniqueId("gantt_project_task_"), group_name, task_start, duration || 1, 100);
                        _.each(task_infos, function (el) {
                            group.addChildTask(el.task_info);
                        });
                        return {task_info: group, task_start: task_start, task_stop: task_stop};
                    }
                } else {
                    var task_name = task.__name;
                    var task_start = instance.web.auto_str_to_date(task[self.fields_view.arch.attrs.date_start]);
                    if (!task_start)
                        return;
                    var task_stop;
                    if (self.fields_view.arch.attrs.date_stop) {
                        task_stop = instance.web.auto_str_to_date(task[self.fields_view.arch.attrs.date_stop]);
                        if (!task_stop)
                            return;
                    } else { // we assume date_duration is defined
                        var tmp = instance.web.format_value(task[self.fields_view.arch.attrs.date_delay],
                            self.fields[self.fields_view.arch.attrs.date_delay]);
                        if (!tmp)
                            return;
                        task_stop = task_start.clone().addMilliseconds(tmp * 60 * 60 * 1000);
                    }
                    var duration = (task_stop.getTime() - task_start.getTime()) / (1000 * 60 * 60);
                    var id = _.uniqueId("gantt_task_");
                    var task_info = new GanttTaskInfo(id, task_name, task_start, ((duration / 24) * 8) || 1, 100);
                    task_info.internal_task = task;
                    task_ids[id] = task_info;
                    return {task_info: task_info, task_start: task_start, task_stop: task_stop};
                }
            }
            var gantt = new GanttChart();
            _.each(_.compact(_.map(groups, function (e) {
                return generate_task_info(e, 0);
            })), function (project) {
                gantt.addProject(project);
            });
            gantt.setEditable(true);
            gantt.setImagePath("/web_gantt/static/lib/dhtmlxGantt/codebase/imgs/");
            gantt.attachEvent("onTaskEndDrag", function (task) {
                self.on_task_changed(task);
            });
            gantt.attachEvent("onTaskEndResize", function (task) {
                self.on_task_changed(task);
            });
            gantt.create(this.chart_id);

            // bind event to display task when we click the item in the tree
            $(".taskNameItem", self.$el).click(function (event) {
                var task_info = task_ids[event.target.id];
                if (task_info) {
                    self.on_task_display(task_info.internal_task);
                }
            });
            if (this.is_action_enabled('create')) {
                // insertion of create button
                var td = $($("table td", self.$el)[0]);
                var rendered = QWeb.render("GanttView-create-button");
                $(rendered).prependTo(td);
                $(".oe_gantt_button_create", this.$el).click(this.on_task_create);
            }
            // Fix for IE to display the content of gantt view.
            this.$el.find(".oe_gantt td:first > div, .oe_gantt td:eq(1) > div > div").css("overflow", "");
        },
        on_task_changed: function (task_obj) {
            var self = this;
            var itask = task_obj.TaskInfo.internal_task;
            var start = task_obj.getEST();
            var duration = (task_obj.getDuration() / 8) * 24;
            var end = start.clone().addMilliseconds(duration * 60 * 60 * 1000);
            var data = {};
            data[self.fields_view.arch.attrs.date_start] =
                instance.web.auto_date_to_str(start, self.fields[self.fields_view.arch.attrs.date_start].type);
            if (self.fields_view.arch.attrs.date_stop) {
                data[self.fields_view.arch.attrs.date_stop] =
                    instance.web.auto_date_to_str(end, self.fields[self.fields_view.arch.attrs.date_stop].type);
            } else { // we assume date_duration is defined
                data[self.fields_view.arch.attrs.date_delay] = duration;
            }
            this.dataset.write(itask.id, data);
        },
        on_task_display: function (task) {
            var self = this;
            var pop = new instance.web.form.FormOpenPopup(self);
            pop.on('write_completed', self, self.reload);
            pop.show_element(
                self.dataset.model,
                task.id,
                null,
                {}
            );
        },
        on_task_create: function () {
            var self = this;
            var pop = new instance.web.form.SelectCreatePopup(this);
            pop.on("elements_selected", self, function () {
                self.reload();
            });
            pop.select_element(
                self.dataset.model,
                {
                    initial_view: "form",
                }
            );
        },
    });

}