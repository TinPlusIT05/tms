openerp.unleashed.module('booking_chart', function (booking, _, Backbone, base) {

    var View = Backbone.Marionette.ItemView,
        _super = View.prototype;

    var Buttons = View.extend({

        template: 'Booking.Buttons',

        events: {
            'click .btn_freeze': 'toggleFreeze',
            'click .btn_today': 'today',
            'click .btn_create': 'openCreateForm'
        },
        
        modelEvents: {
            'change:frozen': 'updateFrozenState',
            'change:start change:end': 'updateTodayState'
        },
        
        ui: {
            freeze: '.btn_freeze',
            today:  '.btn_today',
        },
        
        initialize: function(options){
            this.model = options.model;
            this.resources = options.resources;
            this.chart = options.chart;
        },
        
        attributes: function(){
            var self = this;
            return {
            
            };
        },

        onRender: function () {
            this.updateFrozenState();
            this.updateTodayState();
            
        },
                
        updateTodayState: function(){
            if(this.model.hasToday()){
                this.ui.today.removeAttr('disabled');
            }
            else {
                this.ui.today.attr('disabled', 'disabled');
            }
        },

        updateFrozenState: function() {
            if(this.model.isFrozen()) {
                this.ui.freeze.addClass('active').text('Unfreeze');
            } 
            else {
                this.ui.freeze.removeClass('active').text('Freeze');
            }
        },
        
        today: function(){
            this.model.scrollToday();
        },

        toggleFreeze: function(){
            if(this.model.isFrozen()) {
                this.model.unfreeze();
            }
            else {
                this.model.freeze();
            }
        },
        
        openCreateForm: function(e){
            e.preventDefault();
            var create_model_name = this.chart.get('create_model_name');
            if(!_.isEmpty(create_model_name)){
                booking.trigger('open:record', create_model_name, null);
            }else{
                throw new Error('Not defined "create_model" !, Please configure the model will be created on the Booking Chart Form');
            }
        }
    });

    booking.views('Buttons', Buttons);
});
