openerp.unleashed.module("tms_modules").ready(function(instance){


    instance.tms_modules.FieldDiffView = instance.web.form.FieldText.extend(
    		{
    			template: 'FieldDiffView',
    			init: function(field_manager, node){
    				this._super(field_manager, node);
    			},
    		    render_value: function() {
    		    	var self = this;
    		        if (! this.get("effective_readonly")) {
    		            var show_value = instance.web.format_value(this.get('value'), this, '');
    		            if (show_value === '') {
    		                this.$textarea.css('height', parseInt(this.default_height, 10)+"px");
    		            }
    		            this.$textarea.val(show_value);
    		            if (! this.auto_sized) {
    		                this.auto_sized = true;
    		                this.$textarea.autosize();
    		            } else {
    		                this.$textarea.trigger("autosize");
    		            }
    		        } else {
    		            var txt = this.get("value") || '';

    		            // Check if the Text is in format FROM:... TO:...
    		            // If yes, this is a changes in ticket comment
    		            var new_txt = txt.replace("FROM:", "");
    		            var splited_txt = new_txt.split("TO:");
    		            if (splited_txt.length === 2){

        		              // split 2 parts (FROM and TO) in text
    		            	  var text1 = splited_txt ? splited_txt[0] : '';
        		              var text2 = splited_txt ? splited_txt[1] : '';

        		              // Start compare oldStr and newStr
        		              var dmp = new diff_match_patch();
        		              var d = dmp.diff_main(text1, text2);
        		              dmp.diff_cleanupEfficiency(d);


        		              // Create a html value
        		              var oldStr = "",
    		                  newStr = "";
        		              for (var i = 0, j = d.length; i < j; i++) {
        		                  var arr = d[i];
        		                  if (arr[0] == 0) {
        		                      oldStr += arr[1];
        		                      newStr += arr[1];
        		                  } else if (arr[0] == -1) {
        		                      oldStr += "<span class='diffview-text-del'>" + arr[1] + "</span>";
        		                  } else {
        		                      newStr += "<span class='diffview-text-add'>" + arr[1] + "</span>";
        		                  }
        		              }

        		              // Compute Diff String
        		              dmp.diff_cleanupSemantic(d);
        		              var diff_as_html = $.map(d, function(diff) {
        		                  return self.createDiffViewHTML(diff);
        		                });
        		              var diff = diff_as_html.join('');

        		              txt = "<h3>DIFF</h3><div class='diffview-container'>" + diff + '</div>';
        		              txt += "<h3>FROM</h3><div class='diffview-container'>" + oldStr + '</div>';
        		              txt += "<h3>TO</h3><div class='diffview-container'>" + newStr + '</div>';

    		            }


    		            this.$(".oe_form_text_content").html(txt);
    		        }
    		    },
    		    createDiffViewHTML: function(diff) {
    		        var data, html, operation, pattern_amp, pattern_gt, pattern_lt, pattern_para, text;
    		        html = [];
    		        pattern_amp = /&/g;
    		        pattern_lt = /</g;
    		        pattern_gt = />/g;
    		        pattern_para = /\n/g;
    		        operation = diff[0], data = diff[1];
    		        text = data.replace(pattern_amp, '&amp;').replace(pattern_lt, '&lt;').
    		        replace(pattern_gt, '&gt;').replace(pattern_para, '<br>');
    		        switch (operation) {
    		          case DIFF_INSERT:
    		            return "<span class='diffview-text-add'>" + text + '</span>';
    		          case DIFF_DELETE:
    		            return "<span class='diffview-text-del'>" + text + "</span>";
    		          case DIFF_EQUAL:
    		            return '<span>' + text + '</span>';
    		        }
    		      }


    });
    instance.web.form.widgets.add('diff_view', 'instance.tms_modules.FieldDiffView');
});