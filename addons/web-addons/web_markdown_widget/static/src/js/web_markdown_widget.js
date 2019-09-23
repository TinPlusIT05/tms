openerp.unleashed.module("web_markdown_widget").ready(function(instance, markdown, _){

	/**
	 * ====================================================
	 * COMMON SETTINGS SHOULD BE SET BEFORE MARKDOWN IS RUN
	 * ====================================================
	 */
	
	// Setting Markdown and Highlight
	$(function() {
		if (marked && hljs){
			// for highlight
			hljs.initHighlightingOnLoad();
			// for markdown
			marked.setOptions({
				renderer: new marked.Renderer(),
				gfm: true,
				tables: true,
				breaks: false,
				pedantic: false,
				sanitize: false,
				smartLists: true,
				smartypants: false,
				/* config highlight */
				highlight: function (code) {
				    return hljs.highlightAuto(code).value;
				}
			});
		}
		else {
			console.error("Could not load 'Marked' markdown and 'Highlight' library, please check...");
		}
	});

	/**
	 * =================================================
	 * ADJUST FORM FIELD VIEW FOR MARKDOWN DISPLAY
	 * =================================================
	 */

	instance.web.form.FieldTextMarkdown = instance.web.form.FieldText.extend({

		template: "FieldTextMarkdown",

		render_value: function() {
			this._super.apply(this, arguments);

			// Should render HTML result instead of text
			if (this.get("effective_readonly")) {
	            var txt = this.get("value") || '';
	            this.$(".oe_form_text_content").html(marked(txt));
	        } 
			else {
	        	// Support [Tab] indentation
				if ($.fn.tabby){
					this.$("textarea").tabby();
				}
	        }
	    },
	});
	
	// Add widget into form widgets collection
	instance.web.form.widgets.add("markdown", "instance.web.form.FieldTextMarkdown");

	/**
	 * =================================================
	 * ADJUST LIST VIEW CELL FOR MARKDOWN DISPLAY
	 * -------------------------------------------------
	 * The list view cell should have height adjustable
	 * if the current height of markdown cell break the
	 * layout
	 * =================================================
	 */
	
	// Add method support render markdown value for column
	instance.web.list.Column.include({

		_format: function(row_data, options){

			// render it as markdown or normal escaped contents then return
			if (_.result(options, "markdown")) {

				// get the raw data (before being processed)
				var raw_data = instance.web.format_value(row_data[this.id].value, this, options.value_if_empty);
				
				return marked(raw_data);
			}

			return this._super.apply(this, arguments);
		}
	});

	// modify the way a cell is rendered
	instance.web.ListView.List.include({

		// should be called each time a cell is rendered with value
		render_cell: function (record, column){

			// default rendered value for other type of fields
			var rendered_value = this._super.apply(this, arguments);

			// incase the current cell is used markdown widget
			if (column.type == "text" && column.widget == "markdown") {

				rendered_value = column.format(record.toForm().data, {
					/* two original options */
					model: this.dataset.model,
		            id: record.get('id'),
		            /**
		             * should pass addition custom option to indicate 
		             * a cell should be rendered using markdown or not
		             */
		            markdown: true
		        });
			}

			return rendered_value;
		}
	});
});