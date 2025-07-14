
odoo.define('driver_portal.dashboard', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');

    var DriverPortalDashboard = AbstractAction.extend({
        template: 'DriverPortalDashboard',
        
        init: function(parent, action) {
            this._super(parent, action);
        },
        
        start: function() {
            var self = this;
            return this._super().then(function() {
                self._updateDashboard();
                self._bindEvents();
            });
        },
        
        _updateDashboard: function() {
            // Update dashboard with real-time data
            this._rpc({
                model: 'driver.trip',
                method: 'search_count',
                args: [[['driver_id', '=', this.getSession().uid], ['status', '=', 'pending']]]
            }).then(function(count) {
                $('.pending_trips_count').text(count);
            });
            
            this._rpc({
                model: 'driver.document',
                method: 'search_count',
                args: [[['driver_id', '=', this.getSession().uid], ['is_expired', '=', true]]]
            }).then(function(count) {
                $('.expired_documents_count').text(count);
            });
        },
        
        _bindEvents: function() {
            var self = this;
            
            // Refresh dashboard every 30 seconds
            setInterval(function() {
                self._updateDashboard();
            }, 30000);
            
            // Add click handlers for quick actions
            this.$('.quick_action_button').on('click', function(e) {
                e.preventDefault();
                var action = $(this).data('action');
                self._performQuickAction(action);
            });
        },
        
        _performQuickAction: function(action) {
            switch(action) {
                case 'new_trip':
                    this.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'driver.trip',
                        view_mode: 'form',
                        view_type: 'form',
                        views: [[false, 'form']],
                        target: 'new',
                        context: {'default_driver_id': this.getSession().uid}
                    });
                    break;
                case 'new_document':
                    this.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'driver.document',
                        view_mode: 'form',
                        view_type: 'form',
                        views: [[false, 'form']],
                        target: 'new',
                        context: {'default_driver_id': this.getSession().uid}
                    });
                    break;
            }
        }
    });

    core.action_registry.add('driver_portal_dashboard', DriverPortalDashboard);

    return DriverPortalDashboard;
});

