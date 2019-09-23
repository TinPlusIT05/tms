openerp.unleashed.module('web_includes').ready(function (instance) {
    
    var DocumentPages = this.collections('DocumentPages'),
        documentPages = new DocumentPages();
    
    var document_page = function(model) {
        documentPages.fetch({
            fields: [],
            filter: [
                ['model_name', '=', model],
            ]
        }).done(function (docs) {
            if (docs.length) {
                $('#btn_help_list').show();
                $('#btn_help_list').colorbox({
                    html: docs[0].display_content,
                    title: docs[0].name,
                    width: "90%",
                    height: "90%"
                });
            }
            else {
                $('#btn_help_list').colorbox.remove();
                $('#btn_help_list').hide();
            }
        });
    };

    instance.web.FormView.include({
        load_form: function (data) {
            this._super(data);
            if(data.model)
                document_page(data.model);
        }
    });
    
    instance.web.ListView.include({
        load_list: function (data) {
            this._super(data);
            if(data.model)
                document_page(data.model);
        }
    });

    instance.web_kanban.KanbanView.include({
        load_kanban: function (data) {
            this._super(data);
            if(data.model)
                document_page(data.model);
        }
    });

});


