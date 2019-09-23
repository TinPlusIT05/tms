openerp.unleashed.module('web_includes', function (includes, _, Backbone, base) {

    var BaseModel = base.models('BaseModel'),
        BaseCollection = base.collections('BaseCollection'),
        _super = BaseCollection.prototype;

    var DocumentPages = BaseCollection.extend({

        model: BaseModel,
        model_name: 'document.page',

        initialize: function (models, options) {
            this.ready = $.Deferred();
            _super.initialize.apply(this, arguments);
        },

        update: function () {
            var self = this;
            return this.fetch(this.search())
                .done(function () {
                    self.ready.resolve();
                });
        },

        search: function(){
            var search = {
                fields: [ 'name', 'model_id', 'model_name'],
                filter: [ ['model_id', '!=', false]]
            };
            return search;
        },


        bind: function () {
        },

        unbind: function () {
        }

    });

    includes.collections('DocumentPages', DocumentPages);

});