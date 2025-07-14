/* BigFour Cashbox Portal JavaScript */

odoo.define('bigfour_cashbox.portal', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;

    // Cashbox Portal Widget
    publicWidget.registry.CashboxPortal = publicWidget.Widget.extend({
        selector: '.cashbox-portal',
        events: {
            'click .cashbox-action-btn': '_onActionClick',
            'change .cashbox-file-input': '_onFileChange',
            'click .cashbox-print-btn': '_onPrintClick',
        },

        /**
         * Handle action button clicks
         */
        _onActionClick: function (ev) {
            ev.preventDefault();
            var $btn = $(ev.currentTarget);
            var action = $btn.data('action');
            var model = $btn.data('model');
            var recordId = $btn.data('record-id');
            
            if (!action || !model || !recordId) {
                return;
            }

            // Show confirmation for certain actions
            if (action === 'submit') {
                if (!confirm(_t('Are you sure you want to submit this record for approval?'))) {
                    return;
                }
            }

            // Disable button and show loading
            $btn.prop('disabled', true);
            var originalText = $btn.text();
            $btn.text(_t('Processing...'));

            // Submit form
            var $form = $('<form>', {
                method: 'POST',
                action: '/cashbox/action/' + model + '/' + recordId + '/' + action
            });
            
            // Add CSRF token
            $form.append($('<input>', {
                type: 'hidden',
                name: 'csrf_token',
                value: odoo.csrf_token
            }));

            $form.appendTo('body').submit();
        },

        /**
         * Handle file input changes
         */
        _onFileChange: function (ev) {
            var $input = $(ev.currentTarget);
            var file = ev.target.files[0];
            
            if (file) {
                // Validate file size (max 5MB)
                if (file.size > 5 * 1024 * 1024) {
                    alert(_t('File size must be less than 5MB'));
                    $input.val('');
                    return;
                }
                
                // Validate file type
                var allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
                if (allowedTypes.indexOf(file.type) === -1) {
                    alert(_t('Only image files (JPEG, PNG, GIF) are allowed'));
                    $input.val('');
                    return;
                }
                
                // Show preview if it's an image
                if (file.type.startsWith('image/')) {
                    var reader = new FileReader();
                    reader.onload = function (e) {
                        var $preview = $input.siblings('.cashbox-file-preview');
                        if ($preview.length === 0) {
                            $preview = $('<div class="cashbox-file-preview mt-2"></div>');
                            $input.after($preview);
                        }
                        $preview.html('<img src="' + e.target.result + '" class="cashbox-receipt-image" alt="Receipt Preview">');
                    };
                    reader.readAsDataURL(file);
                }
            }
        },

        /**
         * Handle print button clicks
         */
        _onPrintClick: function (ev) {
            ev.preventDefault();
            var $btn = $(ev.currentTarget);
            var url = $btn.attr('href');
            
            if (url) {
                window.open(url, '_blank');
            }
        },
    });

    // Form validation
    publicWidget.registry.CashboxForm = publicWidget.Widget.extend({
        selector: '.cashbox-form',
        events: {
            'submit': '_onFormSubmit',
            'change input[name="amount"]': '_onAmountChange',
        },

        /**
         * Validate form before submission
         */
        _onFormSubmit: function (ev) {
            var $form = $(ev.currentTarget);
            var isValid = true;
            var errors = [];

            // Validate required fields
            $form.find('input[required], select[required], textarea[required]').each(function () {
                var $field = $(this);
                if (!$field.val() || $field.val().trim() === '') {
                    isValid = false;
                    $field.addClass('is-invalid');
                    errors.push(_t('Please fill in all required fields'));
                } else {
                    $field.removeClass('is-invalid');
                }
            });

            // Validate amount
            var amount = parseFloat($form.find('input[name="amount"]').val());
            if (isNaN(amount) || amount <= 0) {
                isValid = false;
                $form.find('input[name="amount"]').addClass('is-invalid');
                errors.push(_t('Amount must be greater than zero'));
            }

            // Show errors
            if (!isValid) {
                ev.preventDefault();
                var errorMsg = errors.join('\n');
                alert(errorMsg);
                return false;
            }

            return true;
        },

        /**
         * Format amount input
         */
        _onAmountChange: function (ev) {
            var $input = $(ev.currentTarget);
            var value = parseFloat($input.val());
            
            if (!isNaN(value) && value > 0) {
                $input.removeClass('is-invalid');
                // Format to 2 decimal places
                $input.val(value.toFixed(2));
            } else {
                $input.addClass('is-invalid');
            }
        },
    });

    // Auto-refresh for pending items
    publicWidget.registry.CashboxAutoRefresh = publicWidget.Widget.extend({
        selector: '.cashbox-dashboard',
        
        start: function () {
            this._super.apply(this, arguments);
            // Refresh every 5 minutes
            setInterval(this._refreshPendingCounts.bind(this), 5 * 60 * 1000);
        },

        _refreshPendingCounts: function () {
            // This would typically make an AJAX call to get updated counts
            // For now, we'll just reload the page if there are pending items
            var hasPending = $('.cashbox-stats small').text().indexOf('pending') !== -1;
            if (hasPending) {
                location.reload();
            }
        },
    });

});

