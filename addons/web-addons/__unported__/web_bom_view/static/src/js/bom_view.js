/**
 * Created by: Trobz - www.trobz.com
 * Date: 11/21/13
 * Time: 10:18 AM
 */
openerp.web_bom_view = function (instance) {
    var QWeb = instance.web.qweb

    instance.web.TreeView.include({
        // get child data of selected value
        getdata: function (id, children_ids) {
            var self = this;
            self.dataset.read_ids(children_ids, this.fields_list()).done(function (records) {
                // FIXME: check if field type other char or text. It only for char or text field
                var key = Object.keys(self.fields) && Object.keys(self.fields)[0] || ''
                if (key)
                    records = _(records).sortBy(function (record) {
                        return record[key]
                    })
                _(records).each(function (record) {
                    self.records[record.id] = record;
                });

                var $curr_node = self.$el.find('#treerow_' + id);
                var children_rows = QWeb.render('TreeView.rows', {
                    'records': records,
                    'children_field': self.children_field,
                    'fields_view': self.fields_view.arch.children,
                    'fields': self.fields,
                    'level': $curr_node.data('level') || 0,
                    'render': instance.web.format_value,
                    'color_for': self.color_for,
                    'row_parent_id': id
                });

                if ($curr_node.length) {
                    $curr_node.addClass('oe_open');
                    $curr_node.after(children_rows);
                } else {
                    self.$el.find('tbody').html(children_rows);
                }
            });
        },
    })
}