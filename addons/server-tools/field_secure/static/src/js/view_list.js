openerp_field_secure_view_list = function(instance){

    var QWeb = instance.web.qweb;

    instance.web.list.Secure = instance.web.list.Char.extend({

        init: function(){
            this._super.apply(this, arguments)
        }
    });

    instance.web.ListView.List.include({

        init: function(){

            this._super.apply(this, arguments);

            this.$current.on(
                "click", ".request-secure",
                this.onRequestSecureClick.bind(this)
            );
        },

        onRequestSecureClick: function(event){

            event.stopImmediatePropagation();

            var currentTarget = $(event.currentTarget);

            var field_name = currentTarget.data("field"),
                record_id = currentTarget.data("record-id");

            var column = _.find(this.columns, function(item){
                return item.name === field_name
            });

            var currentRecord = _.find(this.records.records, function(record){
                return record.attributes.id === record_id;
            });

            var parent = {
                type: "list", parent: this,
                column: column, record: currentRecord
            };
            var options = {
            	multiline: column["is_multiline_required"]
            };

            // list view structure is not the same as form
            (new instance.web.form.FieldSecureDialog(parent, options)).open()
        },

        // should be called each time a cell is rendered with value
        render_cell: function (record, column){

            // default rendered value for the field
            var rendered_value = this._super.apply(this, arguments);

            // only render the button when password is required
            if (column.type == "secure" && column["is_pwd_auth_required"]) {

            	// avoid the case where user add a new line through editable option
            	if (/^\d+$/gi.test(record.attributes.id)) {

	                var button = QWeb.render("FieldSecure.Request.Button", {
	                    name: column.name, record_id: record.attributes.id
	                });
	                rendered_value += button;
            	}
            	else {
            		rendered_value += "Unable to set value in create mode with password enabled";
            	}
            }

            return rendered_value;
        }
	});

    instance.web.list.columns.add("secure", "instance.web.list.Secure");
};