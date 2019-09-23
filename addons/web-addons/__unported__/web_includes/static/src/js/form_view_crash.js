openerp.unleashed.module('web_includes').ready(function(instance){

    var _t = instance.web._t, 
        _lt = instance.web._lt,
        QWeb = instance.web.qweb,
        _fv = instance.web.FormView;

    instance.web.FormView.include({
        on_processed_onchange : function(result, processed) {
            try {
                if (result.value) {
                    this._internal_set_values(result.value, processed);
                    if (_fv.fieldInput && processed[0] == _fv.fieldName) {
                        _fv.fieldInput.focus();
                    }
                }
                if (!_.isEmpty(result.warning)) {
                    instance.web.dialog($(QWeb.render("CrashManager.warning", result.warning)), {
                        title : result.warning.title,
                        modal : true,
                        buttons : [{
                            text : _t("Ok"),
                            click : function() {
                                $(this).dialog("close");
                            }
                        }]
                    });
                }

                var fields = this.fields;
                _(result.domain).each(function(domain, fieldname) {
                    var field = fields[fieldname];
                    if (!field) {
                        return;
                    }
                    field.node.attrs.domain = domain;
                });

                return $.Deferred().resolve();
            } catch(e) {
                console.error(e);
                instance.webclient.crashmanager.show_message(e);
                return $.Deferred().reject();
            }
        }
    });
});