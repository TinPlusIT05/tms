openerp.unleashed.module("tms_modules").ready(function(instance, markdown, _){

    // open new tab on link click
    _.extend(marked.Renderer.prototype, {

        link: function(href, title, text){

            if (this.options.sanitize) {
                try {
                    var prot = decodeURIComponent(unescape(href))
                        .replace(/[^\w:]/g, '').toLowerCase();
                }
                catch (e) {
                    return '';
                }
                if (prot.indexOf('javascript:') === 0) {
                    return '';
                }
            }

            var out = '<a target="_blank" href="' + href + '"';

            if (title) {
                out += ' title="' + title + '"';
            }
            out += '>' + text + '</a>';

            return out;
        }
    });

    instance.web_widget_text_markdown.FieldTextMarkDown.include({

        /**
         * The purpose of this method is to provide way for markdown field
         * to render forge ticket and support ticket links inside the field
         * and also provide some data related to forge/support for user to
         * be able to read quickly without opening ticket form view to see
         * contents:
         *  + The following should be supported after customization:
         *    - tab indentation by using [tab] key on markdown editor
         *    - apply color to ticket label
         *    - generate ticket link when user use format S#number or F#number
         *    - add description tool-tip when user hover mouse over ticket link
         **/
        start: function() {
            this._super.apply(this, arguments);
            if (this.field.type === "secure") {
                this.$label.append($("<i class='fa fa-key'></i>"));
            }
        },

        render_value: function() {

            // Gets called at each redraw/save of widget
            //  - switching between read-only mode and edit mode
            //  - when switching to next object.
            var show_value = this.format_value(this.get('value'), '');

            if (!this.get("effective_readonly")) {

                this.$txt.val(show_value);
                this.$el.trigger('resize');
                // allow to use tab
            	this.$("textarea").tabby({ tabString: '  ' });
            }
           	else {
                // avoids loading markitup...
                marked.setOptions({
                    sanitize: true,
                    highlight: function (code) {
                        return hljs.highlightAuto(code).value;
                    }
                });
                var self = this,
                    white_list = [
                        "tms.support.ticket",
                        "tms.forge.ticket",
                        "tms.ticket.comment"
                    ];

                var show_value_html = "<div>" + marked(show_value) + "</div>";

                // only use markdown for these models in white-list
                if (_.contains(white_list, this.field_manager.dataset.model)) {

                    // base for forge and support tickets
                    var model = new instance.web.Model(instance.session, "tms.ticket");

                    // data to be transfered to server
                    var data = { forge: [], support: [] };

                    // try to match all tickets
                    var tickets = show_value.match(/(S|F)\#\d+/gi);

                    // process link after the match
                    _.each(tickets, function(ticket_ref) {

                        var ticket_data = ticket_ref.split("#");

                        if (ticket_data[0].toLowerCase() === "f") {
                            data['forge'].push(ticket_data[1]);
                        }
                        else if(!ticket_data[0] || ticket_data[0].toLowerCase() === "s") {
                            data['support'].push(ticket_data[1]);
                        }

                        var $link_anchor = $("<div><a target='_blank' data-ticket-ref='" + ticket_ref + "'>" + ticket_ref + "</a></div>");

                        show_value_html = show_value_html.replace(ticket_ref, $link_anchor.html());
                    });

                    model.call("get_ticket_information", [data]).then(

                        function(response) {

                            var $doc = $(show_value_html);

                            // process each type (forge or support)
                            _.each(response, function(_items, _type) {

                                // for each ticket in each type
                                _.each(_items, function(ticket, ticket_id) {

                                    var ticket_ref = (_type == "forge" ? "F#" : "S#") + ticket_id;

                                    var anchor = $doc.find("a[data-ticket-ref='" + ticket_ref + "']");
                                    anchor.attr("href", ticket.url)
                                        .tooltip({ title: ticket.tooltip })
                                        .css({"color": ticket.color, "font-weight": "bold"});

                                    (!ticket.valid) && anchor.css("text-decoration", "line-through")
                                });
                            });

                            self.$el.find('span[class="oe_form_text_content"]').html($doc);
                        },

                        // in case of error
                        function(){
                            self.$el.find('span[class="oe_form_text_content"]').html(marked(show_value));
                        }
                    );
                }
                else {
                    this.$el.find('span[class="oe_form_text_content"]').html(marked(show_value));
                }
            }
        }
    });

    // invalid line should have a strike line
    instance.web_widget_text_markdown.FieldTextMarkDownList.include({

        _format: function(row_data, options){
            var result = this._super.apply(this, arguments);

            // is exist is_invalid field in the row_data, strike marked as in
            // error (line-through + grey)
            if (_.result(row_data, "is_invalid")) {
                if (_.isObject(row_data['is_invalid']) && row_data['is_invalid'].value)
                {
                    // strike and put color in grey
                    return '<strike style="color:grey">' + result + '</strike>';
                }

            }
            return result;
        },

    });
});