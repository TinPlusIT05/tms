openerp_field_secure_view_form = function(instance){

    var QWeb = instance.web.qweb;

    var FieldSecureDialog = instance.web.form.FieldSecureDialog = instance.web.Dialog.extend({

        template: "FieldSecure.Dialog",

        events: {
            "keypress .password-input": "onWizardInputEnterKeypress",
            "keypress .decrypted-input": "onWizardInputEnterKeypress",
        },

        init: function(parent, options, contents){

        	options = options || {};

            options = _.extend(options || {}, {
                size: 'medium', buttons: [],
                title: parent.type == "list"
                        ? parent.column.string
                        : parent.parent.string
            });

            this.multiline = options["multiline"];

            contents = QWeb.render(
                this.template, { widget: this }
            );

            this._super(parent, options, contents);

            /*
             * --------------------------------
             * helpers attributes
             * --------------------------------
             */

            // can be form|list
            if(parent.type === "form"){
                this.field_name = parent.parent.name;
                this.fieldRequired = parent.parent.field.required;
                this.containerView = parent.parent.view;
                this.dataRecord = this.containerView.datarecord;
                this.dataRecordID = this.dataRecord.id;
                this.model_name = this.containerView.dataset.model;
            }
            else if (parent.type === "list") {
                this.field_name = parent.column.name;
                this.fieldRequired = parent.column.required;
                this.dataRecordID = parent.record.attributes.id;
                this.model_name = parent.parent.dataset.model;
            }
        },

        start: function(){

            var self = this;
            var call_super = this._super.apply(this, arguments);

            return $.when.apply($, [call_super]).then(
            	function() {
                    // focus on password field if possible
                    self.$(".password-input").focus();

                    self.$buttons
                        .html($(QWeb.render("FieldSecure.Dialog.Footer", {widget: this})));
                    self.$buttons
                        .on("click", ".next-button", self.onNextButtonClick.bind(self));
                    self.$buttons
                        .on("click", ".submit-button", self.onSubmitButtonClick.bind(self));
                    self.$buttons
                        .on("click", ".close-button", self.destroy.bind(self));
                    return $.when();
                }
            );
        },

        destroy: function(){
            this.remove_token();
            this._super.apply(this, arguments);
        },

        onWizardInputEnterKeypress: function(event) {
            if (event.which === 13) {
                var $current = $(event.currentTarget);
                if ($current.hasClass("password-input")) {
                    this.$buttons.find(".next-button").trigger("click");
                }
                else if ($current.hasClass("decrypted-input")) {
                    this.$buttons.find(".submit-button").trigger("click");
                }
            }
        },

        onNextButtonClick: function(event){

            // save current context
            var self = this;

            // show loading - remove message
            this.$buttons.find(".message").text("");
            this.$buttons.find(".loading-wrapper").addClass("active");

            // authentication
            this.onPasswordValidation().then(function(info){

                var isValid = info["valid"],
                    message = info.message,
                    token = self.token = info["token"];

                // user free to go
                if (isValid) {

                    // remove event binding
                    self.$("input.password-input").attr({"disabled": "disabled"});
                    self.$buttons.off("click", ".next-button");
                    self.$buttons.find(".message").text(message);
                    self.$buttons.find(".next-button").removeClass("active");
                    self.$buttons.find(".submit-button").addClass("active");

                    // decrypt value
                    self.decrypting_message(token).then(function(response){

                        // check response
                        if(response.result){
                            var record = response.result[0],
                            	value = record[self.field_name];
                            self.$(".wizard-step[step='authentication']").removeClass("active");
                            self.$(".wizard-step[step='decryption']").addClass("active");
                            self.multiline
                            	? self.$("textarea.decrypted-input").val(value)
                    			: self.$("input.decrypted-input").val(value);

                            if (!record[self.field_name]){
                                self.$buttons.find(".message").text(
                                    message + " - value is empty"
                                );
                            }

                            self.$(".decrypted-input").focus();
                        }
                        else {
                            // token expired / user bypass authentication
                            self.$buttons.find(".message").text(response.message);
                        }
                        self.$buttons.find(".loading-wrapper").removeClass("active");
                    },

                    // error, decryption failed due to incorrect/missing secret key
                    function(){
                        self.destroy();
                    });
                }
                else {
                    // authentication failed
                    self.$("input.password-input").val("");
                    self.$buttons.find(".message").text(info.message);
                    self.$buttons.find(".loading-wrapper").removeClass("active");
                }
            });
        },

        onSubmitButtonClick: function(event){

            var self = this;

            // show loading - remove message
            this.$buttons.find(".message").text("");
            this.$buttons.find(".loading-wrapper").addClass("active");

            this.onEncryptValidation().then(

                function(info){

                    var message = info["message"];

                    // hide loading
                    self.$buttons.find(".message").text(message);
                    self.$buttons.find(".message-wrapper").addClass("active");
                    self.$buttons.find(".loading-wrapper").removeClass("active");
                }
            );
        },

        onPasswordValidation: function(){

            var self = this,
            	def = $.Deferred();

            var password = this.$('.password-input').val();

            // client password validation
            if(!password.length){
                def.resolve({
                    valid: false, token: false,
                    message: "Password can not be empty."
                });
            }

            // server password authentication
            this.password_auth(password).then(
                function(info){
                    def.resolve({
                        token: info["token"],
                        valid: info["authorized"],
                        message: info["message"]
                    });
                },
                function(){
                    self.destroy();
                }
            );

            return def.promise();
        },

        onEncryptValidation: function(){

            var self = this,
                def = $.Deferred();

            var encrypting = this.$('.decrypted-input').val();

            if(!this.token){
                // must be authenticated
                def.resolve({
                    valid: false, token: false,
                    message: "token expired"
                });
            }
            else if(!encrypting.length && this.fieldRequired){
                // must pass normal input check
                def.resolve({
                    valid: false, token: false,
                    message: "New value can not be empty."
                });
            }
            else {
                // make a call to server to write directly
                this.encrypting_message(this.token, encrypting).
                then(
                    function(info){
                        def.resolve({
                            valid: info["authorized"],
                            message: info["message"]
                        });
                    },
                    // failed to write value due to unicode ...
                    function(){
                        self.destroy();
                    }
                );
            }

            return def.promise();
        },

        // perform login to check authority and get the token
        password_auth: function(password){
            return instance.session.rpc(
                "/web/secure/authenticate", {
                    ids: [this.dataRecordID],
                    password: password,
                    model: this.model_name,
                    field: this.field_name
                }
            );
        },

        // send request to server along with token
        decrypting_message: function(token){
            return instance.session.rpc(
                "/web/secure/read", {
                    ids: [this.dataRecordID],
                    model: this.model_name,
                    field: this.field_name,
                    token: this.token || ""
                }
            );
        },

        // send request to server along with token
        // to encrypt raw value and store in database
        encrypting_message: function(token, value){

            return instance.session.rpc(
                "/web/secure/write", {
                    ids: [this.dataRecordID],
                    model: this.model_name,
                    field: this.field_name,
                    value: value,
                    token: this.token || ""
                }
            );
        },

        // remove token from server side
        remove_token: function(){
            return this.token && instance.session.rpc(
                "/web/secure/remove_token", {
                    token: this.token
                }
            ) || $.when();
        }
    });

    /*
    * ======================================================================
    * make a new Widget UI for secure field
    * ======================================================================
    **/
    instance.web.form.FieldSecure = instance.web.form.FieldChar.extend({

        template: 'FieldSecure',

        events: {
            "click .request-secure": "onShowWizard",
            "change textarea": "store_dom_value",
            "change input": "store_dom_value"
        },

        /**
         * change init to get flags configured for secure field
         * from calling `fields_get`
         **/
        init: function(parent, node){

        	// setup in parent
            this._super(parent, node);

            // get extra information from field manager fields_view
            var fields_view = this.field_manager.fields_view.fields[this.name];

            // cache dynamic setting from server
            this.set({
            	"is_pwd_auth_required": fields_view["is_pwd_auth_required"],
            	"is_multiline_required": fields_view["is_multiline_required"]
            });
        },

        /**
         * indicate widget class to be used on DOM depending on
         * flag data `is_multiline_required` configured for this field
         *
         * @return {string} widget class
         **/
        get_widget_class: function() {
        	var multiline = this.get("is_multiline_required");
        	return !!multiline ? "oe_form_field_text" : "oe_form_field_char";
        },

        /**
         * get source of data, can be `textarea` or `input` depending on
         * flag data `is_multiline_required` configured for this field
         *
         * @return {jQuery object} data source
         **/
        get_source_input: function() {
        	var is_multiline = this.get("is_multiline_required")
        	return is_multiline ? this.$("textarea") : this.$("input");
        },

        /**
         * Support store DOM value depending on source storages
         * which can be textarea or input
         **/
        store_dom_value: function () {

        	var $source =  this.get_source_input();

        	var readonly = this.get('effective_readonly'),
        		syntax_valid = this.is_syntax_valid();

    		if (!readonly && $source.length && syntax_valid) {
    			var parsed_value = this.parse_value($source.val());
                this.internal_set_value(parsed_value);
            }
        },

        render_value: function() {

    		var readonly = this.get("effective_readonly");

    		var password_required = this.get("is_pwd_auth_required"),
    			multiline_required = this.get("is_multiline_required");

    		var raw_value = this.get("value");

    		if (password_required || readonly) {
    			this.$(".oe_form_secure_content").text(raw_value || "");
    		}
    		else {
    			if (!readonly) {
            		// indicate widget class
    				var $source = this.get_source_input();

        			// format then show the value
        			$source.val(this.format_value(raw_value, ""));
            	}
    		}
        },

        is_false: function() {
            return this.get('value') === '' || this._super();
        },

        onShowWizard: function(event){

        	event.stopImmediatePropagation();

        	var self = this,
        		opt = $(self).attr('options');

            // show dialog
            var dialog = new FieldSecureDialog(
        		{ type: "form", parent: self },
        		{ multiline: this.get("is_multiline_required") }
        	);
            dialog.open();
        }
    });

    // register FieldSecure in view field system
    instance.web.form.widgets.add("secure", "instance.web.form.FieldSecure");
};
