/**
 * Created by sepdau on 1/15/14.
 */
openerp.web_create_edit_warning = function (instance) {
    var _t = instance.web._t,
        QWeb = instance.web.qweb;

    instance.web.FormView.include({
        on_button_save: function (e) {
            var self = this;
            $(e.target).attr("disabled", true);
            return this.save().done(function (result) {
                if (result.warning != undefined && result.warning.message != undefined && result.warning.message != undefined) {
                    instance.web.dialog($(QWeb.render("CrashManager.warning", result.warning)), {
                        title: result.warning.title,
                        modal: true,
                        buttons: [
                            {text: _t("Ok"), click: function () {
                                $(this).dialog("close");
                            }}
                        ]
                    });
                    result = result.result;
                }
                self.trigger("save", result);
                
	            self.reload().then(function (result) {
	            	self.to_view_mode();
	                    var parent = self.ViewManager.ActionManager.getParent();
	                    if (parent) {
	                        parent.menu.do_reload_needaction();
	                    }
	                });
        	}).always(function(){
	            $(e.target).attr("disabled", false);
	        });
        },
        record_created: function (r, prepend_on_create) {
            var self = this;
            if (!r) {
                // should not happen in the server, but may happen for internal purpose
                this.trigger('record_created', r);
                return $.Deferred().reject();
            } else {
                var id = null;
                if (r.result != undefined)
                    id = r.result;
                this.datarecord.id = id ? id : r;
                if (!prepend_on_create) {
                    this.dataset.alter_ids(this.dataset.ids.concat([this.datarecord.id]));
                    this.dataset.index = this.dataset.ids.length - 1;
                } else {
                    this.dataset.alter_ids([this.datarecord.id].concat(this.dataset.ids));
                    this.dataset.index = 0;
                }
                this.do_update_pager();
                if (this.sidebar) {
                    this.sidebar.do_attachement_update(this.dataset, this.datarecord.id);
                }
                //openerp.log("The record has been created with id #" + this.datarecord.id);
                return $.when(this.reload()).then(function () {
                    self.trigger('record_created', r);
                    return _.extend(r, {created: true});
                });
            }
        }
    });
};
